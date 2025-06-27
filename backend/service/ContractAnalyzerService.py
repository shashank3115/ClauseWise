import json
import logging
import os
from typing import List, Dict, Any

try:
    from ibm_watsonx_ai.client import WatsonxAI
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
    IBM_AI_AVAILABLE = True
except ImportError:
    # If the import fails, we print a warning and create dummy classes/variables.
    logging.warning("ibm_watsonx_ai library not found or installation is corrupt. ContractAnalyzerService will run in mock mode.")
    IBM_AI_AVAILABLE = False
    class WatsonxAI: pass
    class GenTextParamsMetaNames: MAX_NEW_TOKENS = "max_new_tokens"; TEMPERATURE = "temperature"

from backend.models.ContractAnalysisModel import ContractAnalysisRequest
from backend.models.ContractAnalysisResponseModel import ContractAnalysisResponse, ClauseFlag, ComplianceFeedback
from backend.models.ComplianceRiskScore import ComplianceRiskScore
from backend.utils.law_loader import LawLoader
from backend.service.RegulatoryEngineService import RegulatoryEngineService 

logger = logging.getLogger(__name__)

class ContractAnalyzerService:
    def __init__(self):
        # --- REASON FOR CHANGE: Proper Dependency Management ---
        # The LawLoader is the single source of truth for data.
        # The RegulatoryEngineService USES the LawLoader to apply logic.
        # The AnalyzerService then uses the engine. This is a clean architecture.
        self.law_loader = LawLoader()
        self.regulatory_engine = RegulatoryEngineService(self.law_loader)
        self.watsonx_client = None
        if IBM_AI_AVAILABLE:
            try:
                self.watsonx_client = WatsonxAI(
                    credentials={
                        "url": os.getenv("IBM_CLOUD_URL"),
                        "apikey": os.getenv("IBM_API_KEY")
                    },
                    project_id=os.getenv("WATSONX_PROJECT_ID")
                )
                logger.info("WatsonxAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize WatsonxAI client. Ensure credentials are set. Error: {e}")
                self.watsonx_client = None
                
    async def analyze_contract(self, request: ContractAnalysisRequest) -> ContractAnalysisResponse:
        """
        Main contract analysis orchestrator. It now uses a single, powerful AI call.
        """
        try:
            # 1. Get the applicable compliance rules from our engine
            jurisdiction = request.jurisdiction or "MY"
            # Assuming you add a contract_type detector or parameter later
            compliance_checklist = self.regulatory_engine.get_compliance_checklist(
                jurisdiction=jurisdiction,
                contract_type="Generic" # This can be improved with type detection
            )

            # 2. Build a comprehensive, data-driven prompt for the AI
            prompt = self._build_analysis_prompt(request.text, compliance_checklist)
            
            # 3. Call the IBM Granite model
            # For the hackathon, you can toggle between a real call and a mock response.
            use_mock_response = (self.watsonx_client is None)

            if use_mock_response:
                ai_response_text = self._get_mock_ai_response()
            else:
                # This is the actual API call to IBM watsonx.ai
                params = {
                    GenTextParamsMetaNames.MAX_NEW_TOKENS: 2048,
                    GenTextParamsMetaNames.TEMPERATURE: 0.1,
                }
                # Example model ID, replace with your chosen Granite model
                model_id = "ibm/granite-13b-instruct-v2" 
                
                response = self.watsonx_client.generate(
                    model_id=model_id,
                    prompt=prompt,
                    params=params
                )
                ai_response_text = response['results'][0]['generated_text']


            # 4. Parse the AI's JSON response and create the final object
            # The AI is prompted to return data in the exact format of our Pydantic models.
            try:
                ai_json = json.loads(ai_response_text)
                return ContractAnalysisResponse(
                    summary=ai_json.get("summary", "Analysis complete."),
                    flagged_clauses=[ClauseFlag(**flag) for flag in ai_json.get("flagged_clauses", [])],
                    compliance_issues=[ComplianceFeedback(**issue) for issue in ai_json.get("compliance_issues", [])],
                    jurisdiction=jurisdiction
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI JSON response: {ai_response_text}")
                # Fallback in case the AI response is not valid JSON
                return ContractAnalysisResponse(summary="Error: AI response could not be parsed.", jurisdiction=jurisdiction)

        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}")
            raise

    async def calculate_risk_score(self, analysis_response: ContractAnalysisResponse) -> ComplianceRiskScore:
        """
        Calculate comprehensive risk scoring, now driven by data from our JSON files.
        """
        violation_categories = set()
        jurisdiction_risks = {}
        financial_risk = 0.0

        for issue in analysis_response.compliance_issues or []:
            violation_categories.add(issue.law_id)
            
            # --- REASON FOR CHANGE: Dynamic, Data-Driven Risk Calculation ---
            law_risk = self._get_risk_from_law(issue.law_id, len(issue.missing_requirements))
            financial_risk += law_risk
            
            jurisdiction = analysis_response.jurisdiction or "MY"
            if jurisdiction not in jurisdiction_risks:
                jurisdiction_risks[jurisdiction] = 0
            jurisdiction_risks[jurisdiction] += int(law_risk / 1000) # Convert to a simple score

        # The severity multiplier logic remains a good heuristic
        severity_multiplier = self._calculate_severity_multiplier(analysis_response.flagged_clauses)
        financial_risk *= severity_multiplier
        
        # This scoring logic is fine, maybe adjust the denominator based on testing
        overall_score = max(0, 100 - int(financial_risk / 50000))

        return ComplianceRiskScore(
            overall_score=overall_score,
            financial_risk_estimate=financial_risk,
            violation_categories=list(violation_categories),
            jurisdiction_risks=jurisdiction_risks
        )

    def _build_analysis_prompt(self, contract_text: str, checklist: Dict[str, Any]) -> str:
        """
        --- REASON FOR CHANGE: This is now the core of the service. ---
        This single prompt combines the user's contract with our structured legal knowledge,
        instructing the AI to perform the full analysis and return a structured JSON response.
        """
        checklist_str = json.dumps(checklist, indent=2)

        prompt = f"""
        You are LegalGuard AI, an expert legal technology assistant. Your task is to analyze the user's contract text based on the provided JSON compliance checklist.

        **Instructions:**
        1.  Carefully read the full "Contract Text".
        2.  Review the "Compliance Checklist" which contains the specific legal requirements for the given jurisdiction.
        3.  Identify any clauses in the contract that violate these requirements, or identify where the contract is missing required clauses.
        4.  Provide your entire output as a single, minified JSON object with NO markdown formatting or other text.
        5.  The JSON object must strictly adhere to the following structure: {{"summary": "...", "flagged_clauses": [{{...}}], "compliance_issues": [{{...}}]}}

        **JSON Structure Details:**
        -   `summary`: A concise, one-sentence summary of the contract's main compliance risks.
        -   `flagged_clauses`: A list of objects. For each problematic clause you find, include:
            -   `clause_text`: The exact text of the problematic clause.
            -   `issue`: A clear explanation of *why* it's an issue based on the checklist.
            -   `severity`: Your assessment of the risk ('high', 'medium', or 'low').
        -   `compliance_issues`: A list of objects. For each law in the checklist, if there are missing requirements, include:
            -   `law_id`: The unique ID of the law (e.g., "GDPR_EU", "EMPLOYMENT_ACT_MY").
            -   `missing_requirements`: A list of strings, where each string is a specific requirement from the checklist that is absent from the contract.
            -   `recommendations`: A list of strings, where each string is a concrete suggestion to fix the missing requirement.

        **Compliance Checklist:**
        ```json
        {checklist_str}
        ```

        **Contract Text to Analyze:**
        ```text
        {contract_text}
        ```

        Begin your JSON response now.
        """
        return prompt

    def _get_risk_from_law(self, law_id: str, violation_count: int) -> float:
        """
        Dynamically calculates financial risk based on penalty data in our JSON files.
        """
        law_data = self.law_loader.get_law_by_id(law_id)
        if not law_data or "penalties" not in law_data:
            return 2000 * violation_count # Default fallback risk

        penalties = law_data["penalties"]
        risk_level = penalties.get("risk_level", "medium").lower()

        # Simple heuristic to convert risk level to a monetary value
        if risk_level == "very high" or risk_level == "high":
            base_risk = 50000
        elif risk_level == "medium":
            base_risk = 10000
        else:
            base_risk = 2000
            
        return base_risk * violation_count

    def _calculate_severity_multiplier(self, flagged_clauses: List[ClauseFlag]) -> float:
        high_count = len([c for c in flagged_clauses if c.severity == "high"])
        medium_count = len([c for c in flagged_clauses if c.severity == "medium"])
        return 1.0 + (high_count * 0.5) + (medium_count * 0.2)

    def _get_mock_ai_response(self) -> str:
        mock_data = {
            "summary": "This contract has high-risk compliance gaps related to GDPR data transfers and is missing key termination clauses under the Malaysian Employment Act.",
            "flagged_clauses": [
                {
                    "clause_text": "All data may be transferred to our global processing centers.",
                    "issue": "GDPR: This clause allows international data transfers without specifying the required legal safeguards, such as an adequacy decision or Standard Contractual Clauses (SCCs).",
                    "severity": "high"
                },
                {
                    "clause_text": "This agreement can be terminated by either party with two (2) weeks' notice.",
                    "issue": "EMPLOYMENT_ACT_MY: The notice period of 2 weeks is less than the statutory minimum of 4 weeks for an employee with less than 2 years of service.",
                    "severity": "medium"
                }
            ],
            "compliance_issues": [
                {
                    "law_id": "GDPR_EU",
                    "missing_requirements": [
                        "The contract fails to include specific details on data subject rights (Art. 15-22).",
                        "There is no mandatory data breach notification clause obligating the processor to inform the controller without undue delay."
                    ],
                    "recommendations": [
                        "Incorporate a 'Data Subject Rights' clause detailing how individuals can exercise their rights of access, rectification, and erasure.",
                        "Add a 'Data Breach Notification' clause with a clear and immediate notification requirement."
                    ]
                }
            ]
        }
        return json.dumps(mock_data)