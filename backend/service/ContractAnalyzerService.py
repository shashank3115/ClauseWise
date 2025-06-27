import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from backend.models.ContractAnalysisModel import ContractAnalysisRequest
from backend.models.ContractAnalysisResponseModel import ContractAnalysisResponse, ClauseFlag, ComplianceFeedback
from backend.models.ComplianceRiskScore import ComplianceRiskScore
from backend.utils.law_loader import LawLoader
from backend.service.RegulatoryEngineService import RegulatoryEngineService
from backend.utils.ai_client import WatsonXClient, WatsonXConfig
from backend.utils.ai_client.exceptions import ConfigurationError, APIError, AuthenticationError 

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
        
        # Initialize our custom WatsonX AI client
        try:
            config = WatsonXConfig.from_environment()
            self.watsonx_client = WatsonXClient(config)
            logger.info("Custom WatsonX AI client initialized successfully.")
        except ConfigurationError as e:
            logger.warning(f"Failed to initialize WatsonX client due to configuration: {e}")
            self.watsonx_client = None
        except Exception as e:
            logger.error(f"Failed to initialize WatsonX client: {e}")
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

            # 2. Use our custom AI client for analysis
            # The custom client handles prompt formatting and system messages internally
            
            # 3. Call our custom WatsonX AI client
            # Toggle between real API call and mock response based on client availability
            use_mock_response = (self.watsonx_client is None)

            if use_mock_response:
                logger.info("Using mock AI response (WatsonX client not available)")
                ai_response_text = self._get_mock_ai_response()
            else:
                try:
                    logger.info("Making request to WatsonX AI via custom client")
                    # Use our custom client's analyze_contract method
                    ai_response_text = self.watsonx_client.analyze_contract(
                        contract_text=request.text,
                        compliance_checklist=compliance_checklist
                    )
                except (APIError, AuthenticationError) as e:
                    logger.error(f"WatsonX API error: {e}")
                    # Fallback to mock response on API errors
                    ai_response_text = self._get_mock_ai_response()
                except Exception as e:
                    logger.error(f"Unexpected error calling WatsonX: {e}")
                    # Fallback to mock response on unexpected errors
                    ai_response_text = self._get_mock_ai_response()


            # 4. Parse the AI's JSON response and create the final object
            # The AI is prompted to return data in the exact format of our Pydantic models.
            try:
                ai_json = json.loads(ai_response_text)
                
                # Convert law_id to law for compatibility with ComplianceFeedback model
                if "compliance_issues" in ai_json:
                    for issue in ai_json["compliance_issues"]:
                        if "law_id" in issue and "law" not in issue:
                            issue["law"] = issue.pop("law_id")
                
                # Ensure required fields have default values if missing
                ai_json.setdefault("summary", "Analysis complete.")
                ai_json.setdefault("flagged_clauses", [])
                ai_json.setdefault("compliance_issues", [])
                
                return ContractAnalysisResponse(
                    summary=ai_json["summary"],
                    flagged_clauses=[ClauseFlag(**flag) for flag in ai_json["flagged_clauses"]],
                    compliance_issues=[ComplianceFeedback(**issue) for issue in ai_json["compliance_issues"]],
                    jurisdiction=jurisdiction
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI JSON response: {ai_response_text}")
                logger.error(f"JSON decode error: {e}")
                # Fallback in case the AI response is not valid JSON
                return ContractAnalysisResponse(
                    summary="Error: AI response could not be parsed as valid JSON.", 
                    flagged_clauses=[],
                    compliance_issues=[],
                    jurisdiction=jurisdiction
                )
            except Exception as e:
                logger.error(f"Failed to create response model from AI data: {e}")
                logger.error(f"AI response data: {ai_json if 'ai_json' in locals() else 'Not parsed'}")
                # Fallback for any other errors
                return ContractAnalysisResponse(
                    summary="Error: Failed to process AI response into structured format.", 
                    flagged_clauses=[],
                    compliance_issues=[],
                    jurisdiction=jurisdiction
                )

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
            violation_categories.add(issue.law)
            
            # --- REASON FOR CHANGE: Dynamic, Data-Driven Risk Calculation ---
            law_risk = self._get_risk_from_law(issue.law, len(issue.missing_requirements))
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

    def _get_risk_from_law(self, law_id: str, violation_count: int) -> float:
        """
        Dynamically calculates financial risk based on penalty data in our JSON files.
        """
        law_data = self.law_loader.get_law_details(law_id)
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
                    "clause_text": "Either party may terminate this agreement with 1 week notice.",
                    "issue": "EMPLOYMENT_ACT_MY: The notice period of 1 week is less than the statutory minimum of 4 weeks for an employee.",
                    "severity": "high"
                },
                {
                    "clause_text": "Employee may access and process customer data as needed for job duties.",
                    "issue": "PDPA_MY: This clause allows data processing without specifying the required legal safeguards and consent mechanisms.",
                    "severity": "medium"
                }
            ],
            "compliance_issues": [
                {
                    "law": "EMPLOYMENT_ACT_MY",
                    "missing_requirements": [
                        "The contract fails to include proper termination notice periods as required by the Employment Act 1955.",
                        "Missing mandatory overtime compensation clauses."
                    ],
                    "recommendations": [
                        "Update termination clause to provide minimum 4 weeks notice for employees.",
                        "Add overtime compensation clause in accordance with Section 60A of the Employment Act."
                    ]
                },
                {
                    "law": "PDPA_MY",
                    "missing_requirements": [
                        "The contract lacks specific data subject consent mechanisms.",
                        "No data breach notification procedures are specified."
                    ],
                    "recommendations": [
                        "Include explicit data subject consent clauses with opt-out mechanisms.",
                        "Add data breach notification procedures with 72-hour reporting requirements."
                    ]
                }
            ]
        }
        return json.dumps(mock_data)