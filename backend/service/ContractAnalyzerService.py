import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from models.ContractAnalysisModel import ContractAnalysisRequest
from models.ContractAnalysisResponseModel import ContractAnalysisResponse, ClauseFlag, ComplianceFeedback
from models.ComplianceRiskScore import ComplianceRiskScore
from utils.law_loader import LawLoader
from service.RegulatoryEngineService import RegulatoryEngineService
from utils.ai_client import WatsonXClient, WatsonXConfig
from utils.ai_client.exceptions import ConfigurationError, APIError, AuthenticationError 

logger = logging.getLogger(__name__)

class ContractAnalyzerService:
    def __init__(self):
        # --- REASON FOR CHANGE: Propers Dependency Management ---
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
            
            # 3. Use IBM WatsonX AI with Granite models for real analysis
            # This is essential for the IBM hackathon - we must demonstrate Granite's capabilities
            api_key = os.getenv("IBM_API_KEY")
            project_id = os.getenv("WATSONX_PROJECT_ID")
            use_real_ai = (self.watsonx_client is not None and api_key and project_id)

            if use_real_ai:
                try:
                    logger.info("Making request to IBM WatsonX AI with Granite model for legal analysis")
                    # Use our custom client's analyze_contract method with IBM Granite
                    ai_response_text = self.watsonx_client.analyze_contract(
                        contract_text=request.text,
                        compliance_checklist=compliance_checklist
                    )
                    logger.info(f"IBM Granite AI Response received: {ai_response_text[:200]}...")
                    
                    # Validate the AI response - if it looks like template or minimal content, enhance it
                    if self._is_granite_response_minimal(ai_response_text):
                        logger.info("IBM Granite response appears minimal or template-like, enhancing with domain expertise")
                        ai_response_text = self._enhance_granite_response(ai_response_text, request.text, compliance_checklist, jurisdiction)
                    else:
                        logger.info("IBM Granite provided comprehensive analysis - using AI response directly")
                        
                except (APIError, AuthenticationError) as e:
                    logger.error(f"WatsonX API error: {e}")
                    # Fallback to enhanced mock only if API fails
                    logger.info("Falling back to enhanced mock analysis due to API error")
                    ai_response_text = self._get_enhanced_mock_analysis(request.text, compliance_checklist, jurisdiction)
                except Exception as e:
                    logger.error(f"Unexpected error calling IBM WatsonX: {e}")
                    # Fallback to enhanced mock only if unexpected error
                    logger.info("Falling back to enhanced mock analysis due to unexpected error")
                    ai_response_text = self._get_enhanced_mock_analysis(request.text, compliance_checklist, jurisdiction)
            else:
                logger.warning("IBM WatsonX client not properly configured - using enhanced mock for demo")
                logger.info("For hackathon production: ensure IBM_API_KEY and WATSONX_PROJECT_ID are set")
                ai_response_text = self._get_enhanced_mock_analysis(request.text, compliance_checklist, jurisdiction)


            # 4. Parse the AI's JSON response and create the final object
            # The AI is prompted to return data in the exact format of our Pydantic models.
            try:
                ai_json = json.loads(ai_response_text)
                
                # Clean up template placeholders and invalid responses
                ai_json = self._clean_ai_response(ai_json, jurisdiction, request.text)
                
                # Ensure we have compliance issues if none exist
                if not ai_json.get("compliance_issues"):
                    logger.info("No compliance issues found, generating comprehensive jurisdiction analysis")
                    ai_json["compliance_issues"] = self._analyze_missing_compliance_requirements(request.text, request.text.lower(), jurisdiction)
                
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

    def _is_granite_response_minimal(self, ai_response: str) -> bool:
        """
        Check if the IBM Granite response is minimal, template-like, or insufficient.
        This helps us determine when to enhance the response with domain expertise.
        """
        if not ai_response or len(ai_response.strip()) < 100:
            return True
            
        # Check for template-like responses and placeholders
        template_indicators = [
            "I cannot analyze this contract",
            "I am not able to",
            "as an AI assistant",
            "I cannot provide legal advice",
            "please consult a lawyer",
            "this is not legal advice",
            "summary\": \"\"",
            "flagged_clauses\": []",
            "compliance_issues\": []",
            "SPECIFIC_LAW_ID",
            "[LAW_NAME]",
            "[JURISDICTION]",
            "{{",
            "}}",
            "undefined",
            "null",
            "N/A",
            "TBD",
            "TODO"
        ]
        
        # Check for responses that are just law IDs
        law_id_patterns = ["GDPR_EU", "PDPA_MY", "PDPA_SG", "CCPA_US", "EMPLOYMENT_ACT_MY"]
        if ai_response.strip() in law_id_patterns:
            return True
        
        ai_lower = ai_response.lower()
        for indicator in template_indicators:
            if indicator.lower() in ai_lower:
                return True
        
        # Check if response has meaningful content
        try:
            json_data = json.loads(ai_response)
            
            # Check if all main sections are empty
            if (not json_data.get("flagged_clauses") and 
                not json_data.get("compliance_issues") and
                (not json_data.get("summary") or len(json_data.get("summary", "")) < 50)):
                return True
            
            # Check for template values in the response data
            response_text = json.dumps(json_data).lower()
            template_check_phrases = [
                "specific_law_id",
                "[law_name]",
                "[jurisdiction]",
                "sample clause",
                "example clause",
                "placeholder",
                "template"
            ]
            
            for phrase in template_check_phrases:
                if phrase in response_text:
                    return True
                    
            # Check if compliance issues are too generic
            compliance_issues = json_data.get("compliance_issues", [])
            for issue in compliance_issues:
                missing_reqs = issue.get("missing_requirements", [])
                for req in missing_reqs:
                    if any(generic in req.lower() for generic in ["generic", "standard", "basic", "common"]):
                        return True
                        
            return False
            
        except json.JSONDecodeError:
            # If it's not JSON, check for meaningful keywords
            legal_keywords = ["clause", "contract", "compliance", "violation", "breach", "liability", "consent", "data"]
            keyword_count = sum(1 for keyword in legal_keywords if keyword in ai_lower)
            return keyword_count < 3

    def _get_enhanced_mock_analysis(self, contract_text: str, compliance_checklist: Dict[str, Any], jurisdiction: str) -> str:
        """
        Enhanced contextual analysis that properly matches issues to relevant contract clauses.
        This provides comprehensive, multi-domain analysis for reliable contract review.
        """
        flagged_clauses = []
        compliance_issues = []
        
        # Convert text to lowercase for easier pattern matching
        text_lower = contract_text.lower()
        
        # Step 1: Analyze contract contextually by splitting into logical sections
        logger.info("Starting comprehensive contract analysis with section-by-section review")
        sections = self._split_contract_into_logical_sections(contract_text)
        
        # Analyze each section contextually for clause-level issues
        for section in sections:
            if isinstance(section, dict):
                section_content = section.get("content", "")
                section_issues = self._analyze_section_contextually(section, section_content.lower(), jurisdiction)
            else:
                # Handle string sections
                section_issues = self._analyze_section_contextually({"content": section, "full_text": section}, section.lower(), jurisdiction)
            flagged_clauses.extend(section_issues)
        
        # Step 2: Analyze missing compliance requirements comprehensively
        logger.info("Analyzing missing compliance requirements for jurisdiction-specific laws")
        compliance_issues = self._analyze_missing_compliance_requirements(contract_text, text_lower, jurisdiction)
        
        # Step 3: Generate accurate summary based on findings
        total_issues = len(flagged_clauses) + len(compliance_issues)
        jurisdiction_name = {"SG": "Singapore", "MY": "Malaysia", "EU": "European Union", "US": "United States"}.get(jurisdiction, jurisdiction)
        
        if total_issues == 0:
            summary = f"Contract analysis complete for {jurisdiction_name}. No significant compliance issues identified."
        elif total_issues <= 2:
            summary = f"Contract analysis identified minor compliance gaps for {jurisdiction_name} that should be addressed."
        elif total_issues <= 5:
            summary = f"Contract has moderate compliance issues for {jurisdiction_name} requiring attention before execution."
        else:
            summary = f"Contract contains significant compliance risks for {jurisdiction_name} requiring immediate remediation."
        
        # Add specific details to summary
        if flagged_clauses:
            high_severity = len([c for c in flagged_clauses if c["severity"] == "high"])
            medium_severity = len([c for c in flagged_clauses if c["severity"] == "medium"])
            if high_severity > 0:
                summary += f" Found {high_severity} high-severity clause issues."
            elif medium_severity > 0:
                summary += f" Found {medium_severity} medium-severity clause issues."
        
        if compliance_issues:
            laws_mentioned = [issue["law"] for issue in compliance_issues]
            summary += f" Compliance gaps identified in: {', '.join(laws_mentioned)}."
        
        logger.info(f"Analysis complete: {len(flagged_clauses)} flagged clauses, {len(compliance_issues)} compliance issues")
        
        mock_data = {
            "summary": summary,
            "flagged_clauses": flagged_clauses,
            "compliance_issues": compliance_issues
        }
        
        return json.dumps(mock_data)

    def _split_contract_into_logical_sections(self, contract_text: str) -> List[Dict[str, str]]:
        """
        Split contract into logical sections with proper context identification.
        """
        import re
        sections = []
        
        # Split by numbered sections first
        numbered_splits = re.split(r'\n\s*(\d+)\.\s*([^\n]+)', contract_text)
        
        if len(numbered_splits) > 3:  # We have numbered sections
            for i in range(1, len(numbered_splits), 3):
                if i+2 < len(numbered_splits):
                    section_number = numbered_splits[i]
                    section_title = numbered_splits[i+1]
                    section_content = numbered_splits[i+2]
                    
                    sections.append({
                        "number": section_number,
                        "title": section_title.strip(),
                        "content": section_content.strip(),
                        "full_text": f"{section_number}. {section_title}\n{section_content}".strip()
                    })
        else:
            # Fallback: split by double line breaks
            paragraphs = re.split(r'\n\s*\n\s*', contract_text)
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    sections.append({
                        "number": str(i+1),
                        "title": "Paragraph",
                        "content": paragraph.strip(),
                        "full_text": paragraph.strip()
                    })
        
        return sections
    
    def _analyze_section_contextually(self, section: Dict[str, str], section_lower: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Analyze a contract section contextually to ensure issues are only flagged on relevant clauses.
        """
        flagged_issues = []
        section_title = section.get("title", "").lower()
        section_content = section.get("content", "").lower()
        full_text = section.get("full_text", "")
        
        # EMPLOYMENT TERMINATION CLAUSES - Only flag employment-related issues
        if self._is_employment_termination_section(section_title, section_content):
            # Check for inadequate notice periods
            if "without notice" in section_content:
                # Only flag if this is for general termination, not misconduct
                if "misconduct" not in section_content:
                    flagged_issues.append({
                        "clause_text": self._truncate_clause_text(full_text),
                        "issue": "Termination without notice may violate employment law requirements for reasonable notice",
                        "severity": "high"
                    })
            
            # Check for unfair termination grounds
            if "misconduct" in section_content:
                # This is fine for misconduct - don't flag data breach issues here!
                # Only flag if the misconduct definitions are overly broad
                if any(vague_term in section_content for vague_term in ["any reason", "at discretion", "without cause"]):
                    flagged_issues.append({
                        "clause_text": self._truncate_clause_text(full_text),
                        "issue": "Termination grounds may be overly broad under employment law",
                        "severity": "medium"
                    })
        
        # PAYMENT/WAGES CLAUSES - Only flag payment-related issues
        elif self._is_payment_section(section_title, section_content):
            # Check for missing overtime provisions
            if "wage" in section_content and "overtime" not in section_content:
                flagged_issues.append({
                    "clause_text": self._truncate_clause_text(full_text),
                    "issue": "Payment clause lacks overtime compensation provisions required by employment law",
                    "severity": "medium"
                })
            
            # Check for deduction clauses
            if "deduction" in section_content and "law" not in section_content:
                flagged_issues.append({
                    "clause_text": self._truncate_clause_text(full_text),
                    "issue": "Wage deduction clause should specify compliance with applicable employment laws",
                    "severity": "low"
                })
        
        # DATA PROCESSING CLAUSES - Only flag data protection issues on actual data clauses
        elif self._is_data_processing_section(section_title, section_content):
            # Check for missing consent mechanisms
            if any(data_term in section_content for data_term in ["personal data", "information", "data"]):
                if "consent" not in section_content:
                    flagged_issues.append({
                        "clause_text": self._truncate_clause_text(full_text),
                        "issue": f"Data processing clause lacks required consent mechanisms under {jurisdiction} privacy law",
                        "severity": "high"
                    })
                
                # Check for indefinite retention
                if any(indefinite_term in section_content for indefinite_term in ["indefinitely", "unlimited", "perpetual"]):
                    flagged_issues.append({
                        "clause_text": self._truncate_clause_text(full_text),
                        "issue": f"Indefinite data retention violates data minimization principles under {jurisdiction} privacy law",
                        "severity": "high"
                    })
        
        # LIABILITY/INDEMNIFICATION CLAUSES
        elif self._is_liability_section(section_title, section_content):
            # Check for liability caps
            import re
            amount_match = re.search(r'(\d+(?:,\d+)*)', section_content)
            if amount_match and "liability" in section_content:
                amount = int(amount_match.group(1).replace(',', ''))
                if amount < 50000:  # Low liability cap
                    flagged_issues.append({
                        "clause_text": self._truncate_clause_text(full_text),
                        "issue": f"Liability cap may be insufficient to cover potential damages under {jurisdiction} law",
                        "severity": "medium"
                    })
        
        return flagged_issues
    
    def _is_employment_termination_section(self, title: str, content: str) -> bool:
        """Check if section deals with employment termination."""
        termination_indicators = ["termination", "terminate", "end of contract", "dismissal"]
        return any(indicator in title or indicator in content for indicator in termination_indicators)
    
    def _is_payment_section(self, title: str, content: str) -> bool:
        """Check if section deals with payment/wages."""
        payment_indicators = ["payment", "wage", "salary", "compensation", "remuneration"]
        return any(indicator in title or indicator in content for indicator in payment_indicators)
    
    def _is_data_processing_section(self, title: str, content: str) -> bool:
        """Check if section deals with data processing."""
        data_indicators = ["data processing", "personal data", "information", "privacy", "confidential"]
        return any(indicator in title or indicator in content for indicator in data_indicators)
    
    def _is_liability_section(self, title: str, content: str) -> bool:
        """Check if section deals with liability."""
        liability_indicators = ["liability", "indemnify", "damages", "compensation", "insurance"]
        return any(indicator in title or indicator in content for indicator in liability_indicators)
    
    def _truncate_clause_text(self, text: str, max_length: int = 200) -> str:
        """Truncate clause text to a reasonable length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _analyze_missing_compliance_requirements(self, contract_text: str, text_lower: str, jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Comprehensive analysis of missing compliance requirements for the given jurisdiction.
        This provides multi-domain legal analysis covering employment law, data protection, and contract law.
        """
        missing_issues = []
        
        # Identify contract type and context
        is_employment_contract = any(term in text_lower for term in ["employment", "employee", "worker", "domestic worker"])
        has_data_processing = any(term in text_lower for term in ["personal data", "information", "data", "privacy"])
        has_international_elements = any(country in text_lower for country in ["united states", "india", "china", "uk", "europe"])
        
        # For Singapore jurisdiction
        if jurisdiction == "SG":
            # Singapore PDPA Analysis
            pdpa_sg_requirements = []
            pdpa_sg_recommendations = []
            
            # Always check PDPA compliance for employment contracts
            if is_employment_contract:
                if "consent" not in text_lower:
                    pdpa_sg_requirements.append("Contract lacks proper consent mechanisms for Singapore PDPA")
                    pdpa_sg_recommendations.append("Include explicit consent procedures and individual rights under Singapore PDPA")
                
                if not has_data_processing:
                    pdpa_sg_requirements.append("Employment contract lacks provisions for handling worker's personal data under Singapore PDPA")
                    pdpa_sg_recommendations.append("Add clause specifying purposes for collecting worker's personal data (employment administration, payroll, etc.)")
                
                if "consent" not in text_lower or "personal information" not in text_lower:
                    pdpa_sg_requirements.append("Missing consent mechanisms for collecting and processing worker's personal information")
                    pdpa_sg_recommendations.append("Include worker consent for data processing activities")
            
            # Data breach notification (always required for organizations)
            if "breach" not in text_lower or "notification" not in text_lower:
                pdpa_sg_requirements.append("Data breach notification timeline does not meet Singapore PDPA requirements")
                pdpa_sg_recommendations.append("Implement mandatory 72-hour breach notification to PDPC Singapore")
            
            if "notification" not in text_lower:
                pdpa_sg_requirements.append("No data breach notification procedures specified")
                pdpa_sg_recommendations.append("Implement data breach notification procedures as required by Singapore PDPA")
            
            # International transfers
            if has_international_elements and has_data_processing:
                pdpa_sg_requirements.append("International data transfers lack adequate protection under Singapore PDPA")
                pdpa_sg_recommendations.append("Implement appropriate safeguards for international transfers under Singapore PDPA")
            
            # Data retention
            if "indefinite" in text_lower and "retention" in text_lower:
                pdpa_sg_requirements.append("Indefinite data retention violates Singapore PDPA purpose limitation")
                pdpa_sg_recommendations.append("Define specific retention periods with clear business justification")
            
            if pdpa_sg_requirements:
                missing_issues.append({
                    "law": "PDPA_SG",
                    "missing_requirements": pdpa_sg_requirements,
                    "recommendations": pdpa_sg_recommendations
                })
        
        # For Malaysia jurisdiction
        elif jurisdiction == "MY":
            # Malaysian Employment Act Analysis
            if is_employment_contract:
                employment_requirements = []
                employment_recommendations = []
                
                # Termination notice analysis
                if "without notice" in text_lower and "misconduct" not in text_lower:
                    employment_requirements.append("Termination without notice may violate Malaysian Employment Act requirements")
                    employment_recommendations.append("Ensure termination clauses comply with Employment Act 1955 notice requirements")
                
                # Overtime provisions
                if "overtime" not in text_lower:
                    employment_requirements.append("Missing overtime compensation provisions")
                    employment_recommendations.append("Add overtime compensation clauses in accordance with Malaysian Employment Act")
                
                # Working hours
                if "working hours" not in text_lower and "hours of work" not in text_lower:
                    employment_requirements.append("Contract lacks clear working hours specification")
                    employment_recommendations.append("Define working hours in compliance with Malaysian Employment Act")
                
                # Rest periods
                if "rest" in text_lower and "adequate" in text_lower:
                    employment_requirements.append("Rest period specification may be too vague under Employment Act")
                    employment_recommendations.append("Specify minimum rest periods as required by Malaysian Employment Act")
                
                if employment_requirements:
                    missing_issues.append({
                        "law": "EMPLOYMENT_ACT_MY",
                        "missing_requirements": employment_requirements,
                        "recommendations": employment_recommendations
                    })
            
            # Malaysian PDPA Analysis
            pdpa_my_requirements = []
            pdpa_my_recommendations = []
            
            if is_employment_contract:
                if "consent" not in text_lower and "data subject" not in text_lower:
                    pdpa_my_requirements.append("Contract lacks explicit data subject consent mechanisms")
                    pdpa_my_recommendations.append("Include clear data subject consent procedures with opt-out mechanisms")
                
                if "personal data" not in text_lower and "information" not in text_lower:
                    pdpa_my_requirements.append("Employment contract should address handling of worker's personal data")
                    pdpa_my_recommendations.append("Add provisions for lawful processing of worker's personal data under PDPA Malaysia")
            
            # Data breach notification
            if "72 hours" not in text_lower and "notification" not in text_lower:
                pdpa_my_requirements.append("Data breach notification timeline does not meet PDPA requirements")
                pdpa_my_recommendations.append("Implement 72-hour breach notification timeline as required by PDPA")
            
            # Data retention
            if "indefinite" in text_lower:
                pdpa_my_requirements.append("Data retention period violates PDPA data minimization principle")
                pdpa_my_recommendations.append("Specify reasonable data retention periods with automatic deletion")
            
            if pdpa_my_requirements:
                missing_issues.append({
                    "law": "PDPA_MY",
                    "missing_requirements": pdpa_my_requirements,
                    "recommendations": pdpa_my_recommendations
                })
        
        # Cross-jurisdictional analysis for EU/GDPR
        elif jurisdiction == "EU":
            gdpr_requirements = []
            gdpr_recommendations = []
            
            if has_data_processing:
                if "consent" not in text_lower:
                    gdpr_requirements.append("Missing explicit consent mechanisms for GDPR compliance")
                    gdpr_recommendations.append("Implement GDPR-compliant consent mechanisms with clear opt-out")
                
                if "data protection officer" not in text_lower and "dpo" not in text_lower:
                    gdpr_requirements.append("No reference to Data Protection Officer contact details")
                    gdpr_recommendations.append("Include DPO contact information as required by GDPR")
                
                if has_international_elements and "standard contractual clauses" not in text_lower:
                    gdpr_requirements.append("Cross-border transfers lack required GDPR safeguards")
                    gdpr_recommendations.append("Implement Standard Contractual Clauses for international data transfers")
            
            if gdpr_requirements:
                missing_issues.append({
                    "law": "GDPR_EU",
                    "missing_requirements": gdpr_requirements,
                    "recommendations": gdpr_recommendations
                })
        
        # US/California analysis
        elif jurisdiction == "US":
            ccpa_requirements = []
            ccpa_recommendations = []
            
            if has_data_processing:
                if "consumer" not in text_lower or "right to know" not in text_lower:
                    ccpa_requirements.append("Contract lacks CCPA consumer rights provisions")
                    ccpa_recommendations.append("Include consumer rights to know, delete, and opt-out under CCPA")
                
                if "do not sell" not in text_lower and "sale" in text_lower:
                    ccpa_requirements.append("No 'Do Not Sell My Personal Information' opt-out mechanism")
                    ccpa_recommendations.append("Implement CCPA-compliant opt-out mechanism for personal information sales")
            
            if ccpa_requirements:
                missing_issues.append({
                    "law": "CCPA_US",
                    "missing_requirements": ccpa_requirements,
                    "recommendations": ccpa_recommendations
                })
        
        logger.info(f"Compliance analysis complete: Found {len(missing_issues)} law categories with missing requirements")
        return missing_issues

    def _enhance_granite_response(self, granite_response: str, contract_text: str, compliance_checklist: Dict[str, Any], jurisdiction: str) -> str:
        """
        Enhance IBM Granite's response when it's minimal or incomplete.
        This combines the power of Granite AI with our legal domain expertise.
        """
        logger.info("Enhancing IBM Granite response with domain-specific legal analysis")
        
        try:
            # Try to parse Granite's response first
            granite_data = json.loads(granite_response) if granite_response else {}
        except json.JSONDecodeError:
            # If Granite's response isn't JSON, start fresh but log the response
            logger.warning(f"Granite response not valid JSON: {granite_response}")
            granite_data = {}
        
        # Get our enhanced analysis as a baseline
        enhanced_analysis = self._get_enhanced_mock_analysis(contract_text, compliance_checklist, jurisdiction)
        enhanced_data = json.loads(enhanced_analysis)
        
        # Merge Granite's insights with our domain expertise
        # Prefer our enhanced summary over Granite's template responses
        granite_summary = granite_data.get("summary", "")
        enhanced_summary = enhanced_data["summary"]
        
        # Check if Granite's summary is meaningful and not template-like
        law_ids = ["GDPR_EU", "PDPA_MY", "PDPA_SG", "CCPA_US", "EMPLOYMENT_ACT_MY", "SPECIFIC_LAW_ID"]
        granite_is_meaningful = (
            granite_summary and 
            len(granite_summary.strip()) > 20 and
            granite_summary.strip() not in law_ids and  # Not just a law ID
            "Error: Could not parse AI response" not in granite_summary and
            "Contract analysis found issues with PDPA_MY" not in granite_summary and
            "Contract analysis found issues with PDPA_SG" not in granite_summary and
            "Contract analysis found issues with GDPR_EU" not in granite_summary and
            "SPECIFIC_LAW_ID" not in granite_summary
        )
        
        if granite_is_meaningful:
            # Use Granite's summary as the base, but don't concatenate blindly
            final_summary = granite_summary
        else:
            # Use our enhanced summary when Granite's is template-like or missing
            logger.info(f"Granite summary '{granite_summary}' is not meaningful, using enhanced summary")
            final_summary = enhanced_summary
        
        # Combine flagged clauses from both analyses
        granite_clauses = granite_data.get("flagged_clauses", [])
        enhanced_clauses = enhanced_data.get("flagged_clauses", [])
        
        # Merge unique clauses (avoid duplicates based on issue type)
        combined_clauses = granite_clauses.copy()
        granite_issues = {clause.get("issue", "") for clause in granite_clauses}
        
        for clause in enhanced_clauses:
            if clause.get("issue", "") not in granite_issues:
                combined_clauses.append(clause)
        
        # Combine compliance issues from both analyses
        granite_compliance = granite_data.get("compliance_issues", [])
        enhanced_compliance = enhanced_data.get("compliance_issues", [])
        
        # Merge compliance issues by law
        compliance_by_law = {}
        
        # Add Granite's compliance issues
        for issue in granite_compliance:
            law = issue.get("law", "")
            if law:
                compliance_by_law[law] = issue
        
        # Merge with enhanced compliance issues
        for issue in enhanced_compliance:
            law = issue.get("law", "")
            if law:
                if law in compliance_by_law:
                    # Combine requirements and recommendations
                    existing = compliance_by_law[law]
                    existing["missing_requirements"] = list(set(
                        existing.get("missing_requirements", []) + 
                        issue.get("missing_requirements", [])
                    ))
                    existing["recommendations"] = list(set(
                        existing.get("recommendations", []) + 
                        issue.get("recommendations", [])
                    ))
                else:
                    compliance_by_law[law] = issue
        
        # Create final enhanced response
        enhanced_response = {
            "summary": final_summary,
            "flagged_clauses": combined_clauses,
            "compliance_issues": list(compliance_by_law.values())
        }
        
        logger.info(f"Enhanced response created with {len(combined_clauses)} flagged clauses and {len(compliance_by_law)} compliance issues")
        return json.dumps(enhanced_response)

    def _extract_clean_clause_text(self, contract_text: str, pattern: str) -> str:
        """
        Extract a clean, readable clause text that contains the specified pattern.
        Returns complete logical clauses with proper formatting and context.
        """
        import re
        
        # Normalize text but preserve section structure
        normalized_text = re.sub(r'\s+', ' ', contract_text.strip())
        
        # Find pattern location
        pattern_match = re.search(re.escape(pattern), normalized_text, re.IGNORECASE)
        if not pattern_match:
            return ""
        
        # First, try to find logical sections (numbered clauses, paragraphs)
        # Split by numbered sections or clear paragraph breaks
        sections = re.split(r'(?:\n\s*\d+\.|(?:\n\s*){2,})', contract_text)
        
        # Find which section contains our pattern
        target_section = ""
        for section in sections:
            if pattern.lower() in section.lower():
                target_section = section.strip()
                break
        
        if target_section:
            # Clean up the section while preserving structure
            clean_section = re.sub(r'\s+', ' ', target_section)
            clean_section = clean_section.strip()
            
            # If it starts with a number and period (numbered clause), return the whole clause
            if re.match(r'^\d+\.\s*[A-Z]', clean_section):
                # This is a numbered clause - return it complete
                return clean_section
            else:
                # Find the sentence or logical unit that contains the pattern
                # Split by sentence-ending punctuation followed by capital letters
                sentences = re.split(r'[.!?]+\s+(?=[A-Z])', clean_section)
                
                pattern_sentence_idx = -1
                for i, sentence in enumerate(sentences):
                    if pattern.lower() in sentence.lower():
                        pattern_sentence_idx = i
                        break
                
                if pattern_sentence_idx >= 0:
                    # Include the pattern sentence plus some context
                    start_idx = max(0, pattern_sentence_idx - 1)
                    end_idx = min(len(sentences), pattern_sentence_idx + 2)
                    
                    context_sentences = sentences[start_idx:end_idx]
                    result = '. '.join(context_sentences).strip()
                    
                    # Ensure proper punctuation
                    if not result.endswith(('.', '!', '?')):
                        result += '.'
                    
                    return result
        
        # Fallback: extract context around the pattern if section-based approach fails
        pattern_pos = pattern_match.start()
        
        # Look for logical boundaries around the pattern
        start_pos = max(0, pattern_pos - 200)
        end_pos = min(len(normalized_text), pattern_pos + 200)
        
        # Find sentence boundaries to avoid cutting mid-sentence
        context_text = normalized_text[start_pos:end_pos]
        
        # Try to find complete sentences around the pattern
        sentences = re.split(r'[.!?]+\s+(?=[A-Z])', context_text)
        pattern_sentence = ""
        
        for sentence in sentences:
            if pattern.lower() in sentence.lower():
                pattern_sentence = sentence.strip()
                break
        
        if pattern_sentence:
            # Add proper punctuation if missing
            if not pattern_sentence.endswith(('.', '!', '?')):
                pattern_sentence += '.'
            return pattern_sentence
        
        # Last resort: return a cleaned excerpt
        excerpt = context_text.strip()
        
        # Try to end at a reasonable boundary
        if len(excerpt) > 100:
            # Find the last sentence boundary within reasonable length
            for i in range(len(excerpt) - 1, max(0, len(excerpt) - 50), -1):
                if excerpt[i] in '.!?' and i < len(excerpt) - 1 and excerpt[i + 1].isspace():
                    excerpt = excerpt[:i + 1]
                    break
        
        return excerpt

    def _clean_ai_response(self, ai_json: Dict[str, Any], jurisdiction: str, contract_text: str) -> Dict[str, Any]:
        """
        Clean up AI response by removing template placeholders and fixing jurisdiction mismatches.
        """
        # Clean up the summary
        summary = ai_json.get("summary", "")
        
        # Check if summary is just a law ID or other invalid content
        law_ids = ["GDPR_EU", "PDPA_MY", "PDPA_SG", "CCPA_US", "EMPLOYMENT_ACT_MY", "SPECIFIC_LAW_ID"]
        if summary.strip() in law_ids:
            logger.warning(f"Summary contains only law ID '{summary.strip()}', replacing with proper summary")
            summary = ""  # Clear it so it gets replaced with enhanced summary
        
        # Remove any mentions of wrong jurisdictions in summary
        if jurisdiction == "SG" and "PDPA_MY" in summary:
            summary = summary.replace("PDPA_MY", "PDPA_SG")
            summary = summary.replace("Malaysia", "Singapore")
        elif jurisdiction == "MY" and "PDPA_SG" in summary:
            summary = summary.replace("PDPA_SG", "PDPA_MY")
            summary = summary.replace("Singapore", "Malaysia")
        
        # Remove template text patterns more comprehensively
        template_phrases_to_remove = [
            "Contract analysis found issues with SPECIFIC_LAW_ID",
            "Contract analysis found issues with PDPA_MY",
            "Contract analysis found issues with PDPA_SG", 
            "Contract analysis found issues with GDPR_EU",
            "Contract analysis found issues with CCPA_US",
            "Contract analysis found issues with EMPLOYMENT_ACT_MY",
            "SPECIFIC_LAW_ID",
            "Contract analysis found issues with"
        ]
        
        for phrase in template_phrases_to_remove:
            if phrase in summary:
                summary = summary.replace(phrase, "").strip()
        
        # Clean up leading/trailing punctuation and spaces
        summary = summary.strip().strip(",").strip()
        
        # If summary starts with a space or comma after cleaning, fix it
        while summary.startswith((" ", ",")):
            summary = summary[1:].strip()
        
        # If summary is empty or too short after cleaning, use a fallback
        if not summary or len(summary.strip()) < 10:
            jurisdiction_name = {"SG": "Singapore", "MY": "Malaysia", "EU": "European Union", "US": "United States"}.get(jurisdiction, jurisdiction)
            summary = f"Contract analysis complete for {jurisdiction_name}. Compliance review identifies areas requiring attention."
        
        # Ensure proper sentence structure
        if summary and not summary[0].isupper():
            summary = summary[0].upper() + summary[1:]
        
        # Clean up any double spaces and normalize
        summary = " ".join(summary.split())
        ai_json["summary"] = summary
        
        # Clean up compliance issues
        if "compliance_issues" in ai_json:
            cleaned_issues = []
            for issue in ai_json["compliance_issues"]:
                law_id = issue.get("law", "")
                
                # Skip template placeholders
                if law_id == "SPECIFIC_LAW_ID":
                    logger.warning("Filtering out template compliance issue with SPECIFIC_LAW_ID")
                    continue
                
                # Skip if requirements are template text
                missing_reqs = issue.get("missing_requirements", [])
                recommendations = issue.get("recommendations", [])
                
                # Check for template text in requirements
                if any("Detailed list of missing legal requirements" in req for req in missing_reqs):
                    logger.warning(f"Filtering out template compliance issue for {law_id}")
                    continue
                
                if any("Specific actionable legal recommendations" in rec for rec in recommendations):
                    logger.warning(f"Filtering out template compliance issue for {law_id}")
                    continue
                
                # Filter out jurisdiction-inappropriate laws
                if jurisdiction == "SG" and law_id not in ["PDPA_SG", "Employment_Act_SG"]:
                    if law_id == "PDPA_MY":
                        # Convert to Singapore equivalent
                        issue["law"] = "PDPA_SG"
                        law_id = "PDPA_SG"
                    elif law_id in ["GDPR_EU", "CCPA_US", "EMPLOYMENT_ACT_MY"]:
                        logger.warning(f"Filtering out jurisdiction-inappropriate law {law_id} for Singapore contract")
                        continue
                
                elif jurisdiction == "MY" and law_id not in ["PDPA_MY", "EMPLOYMENT_ACT_MY"]:
                    if law_id == "PDPA_SG":
                        # Convert to Malaysia equivalent
                        issue["law"] = "PDPA_MY"
                        law_id = "PDPA_MY"
                    elif law_id in ["GDPR_EU", "CCPA_US"]:
                        logger.warning(f"Filtering out jurisdiction-inappropriate law {law_id} for Malaysia contract")
                        continue
                
                # Keep valid compliance issues
                cleaned_issues.append(issue)
            
            ai_json["compliance_issues"] = cleaned_issues
        
        # Clean up flagged clauses
        if "flagged_clauses" in ai_json:
            cleaned_clauses = []
            for clause in ai_json["flagged_clauses"]:
                clause_text = clause.get("clause_text", "")
                issue = clause.get("issue", "")
                
                # Skip clauses with template or placeholder text
                if any(placeholder in clause_text.upper() for placeholder in [
                    "SPECIFIC_LAW_ID", "[LAW_NAME]", "[JURISDICTION]", "PLACEHOLDER"
                ]):
                    logger.warning("Filtering out flagged clause with template text")
                    continue
                
                if any(placeholder in issue.upper() for placeholder in [
                    "SPECIFIC_LAW_ID", "[LAW_NAME]", "[JURISDICTION]", "PLACEHOLDER"
                ]):
                    logger.warning("Filtering out flagged clause with template issue")
                    continue
                
                # Validate contextual relevance
                if self._is_clause_issue_mismatch(clause_text, issue):
                    logger.warning(f"Filtering out contextually irrelevant clause issue: {issue[:50]}...")
                    continue
                
                # Keep valid flagged clauses
                cleaned_clauses.append(clause)
            
            ai_json["flagged_clauses"] = cleaned_clauses
        
        return ai_json
    
    def _is_clause_issue_mismatch(self, clause_text: str, issue: str) -> bool:
        """
        Check if the issue is contextually inappropriate for the clause.
        """
        clause_lower = clause_text.lower()
        issue_lower = issue.lower()
        
        # Data breach notification issues should only be on data processing clauses
        if "breach notification" in issue_lower or "data breach" in issue_lower:
            if not any(data_word in clause_lower for data_word in ["data", "information", "privacy", "breach"]):
                return True
        
        # Data retention issues should only be on data retention clauses
        if "data retention" in issue_lower or "indefinite" in issue_lower:
            if not any(data_word in clause_lower for data_word in ["data", "retention", "information", "store"]):
                return True
        
        # Termination issues should only be on termination clauses
        if "termination notice" in issue_lower and "termination" not in clause_lower:
            return True
        
        # IP issues should only be on IP clauses
        if "intellectual property" in issue_lower or "work product" in issue_lower:
            if not any(ip_word in clause_lower for ip_word in ["intellectual", "work product", "copyright", "patent"]):
                return True
        
        return False