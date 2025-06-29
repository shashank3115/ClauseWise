import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
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
        Main contract analysis orchestrator with enhanced content-aware analysis.
        """
        try:
            # 1. Pre-process and clean the contract text
            cleaned_contract = self._preprocess_contract_text(request.text)
            logger.info(f"Contract preprocessing complete. Original length: {len(request.text)}, Cleaned length: {len(cleaned_contract)}")
            
            # 2. Analyze contract structure and content type
            contract_metadata = self._analyze_contract_metadata(cleaned_contract)
            logger.info(f"Contract analysis: Type={contract_metadata['type']}, Sections={len(contract_metadata['sections'])}, Has_Data_Processing={contract_metadata['has_data_processing']}")
            
            # 3. Get the applicable compliance rules from our engine
            jurisdiction = request.jurisdiction or "MY"
            compliance_checklist = self.regulatory_engine.get_compliance_checklist(
                jurisdiction=jurisdiction,
                contract_type=contract_metadata['type']
            )

            # 4. Use IBM WatsonX AI with enhanced prompting
            api_key = os.getenv("IBM_API_KEY")
            project_id = os.getenv("WATSONX_PROJECT_ID")
            use_real_ai = (self.watsonx_client is not None and api_key and project_id)

            if use_real_ai:
                try:
                    logger.info("Making request to IBM WatsonX AI with Granite model for legal analysis")
                    # Use enhanced prompting with contract metadata
                    ai_response_text = self._get_granite_analysis_with_context(
                        cleaned_contract, contract_metadata, compliance_checklist, jurisdiction
                    )
                    logger.info(f"IBM Granite AI Response received: {ai_response_text[:200]}...")
                    
                    # Validate the AI response
                    if self._is_granite_response_minimal(ai_response_text):
                        logger.info("IBM Granite response appears minimal, enhancing with domain expertise")
                        ai_response_text = self._get_intelligent_mock_analysis(
                            cleaned_contract, contract_metadata, compliance_checklist, jurisdiction
                        )
                    else:
                        logger.info("IBM Granite provided comprehensive analysis - using AI response directly")
                        
                except (APIError, AuthenticationError) as e:
                    logger.error(f"WatsonX API error: {e}")
                    ai_response_text = self._get_intelligent_mock_analysis(
                        cleaned_contract, contract_metadata, compliance_checklist, jurisdiction
                    )
                except Exception as e:
                    logger.error(f"Unexpected error calling IBM WatsonX: {e}")
                    ai_response_text = self._get_intelligent_mock_analysis(
                        cleaned_contract, contract_metadata, compliance_checklist, jurisdiction
                    )
            else:
                logger.warning("IBM WatsonX client not properly configured - using intelligent mock for demo")
                ai_response_text = self._get_intelligent_mock_analysis(
                    cleaned_contract, contract_metadata, compliance_checklist, jurisdiction
                )

            # 5. Parse and validate the AI's JSON response
            try:
                ai_json = json.loads(ai_response_text)
                ai_json = self._clean_ai_response(ai_json, jurisdiction, cleaned_contract)
                
                # Ensure we have meaningful analysis
                if not ai_json.get("compliance_issues") and not ai_json.get("flagged_clauses"):
                    logger.info("No issues found, generating comprehensive compliance analysis")
                    ai_json = self._generate_comprehensive_analysis(
                        cleaned_contract, contract_metadata, jurisdiction
                    )
                
                # Convert law_id to law for compatibility
                if "compliance_issues" in ai_json:
                    for issue in ai_json["compliance_issues"]:
                        if "law_id" in issue and "law" not in issue:
                            issue["law"] = issue.pop("law_id")
                
                # Ensure required fields
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
                return ContractAnalysisResponse(
                    summary="Error: AI response could not be parsed as valid JSON.", 
                    flagged_clauses=[],
                    compliance_issues=[],
                    jurisdiction=jurisdiction
                )
            except Exception as e:
                logger.error(f"Failed to create response model from AI data: {e}")
                return ContractAnalysisResponse(
                    summary="Error: Failed to process AI response into structured format.", 
                    flagged_clauses=[],
                    compliance_issues=[],
                    jurisdiction=jurisdiction
                )

        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}")
            raise

    def _preprocess_contract_text(self, contract_text: str) -> str:
        """
        Enhanced preprocessing to remove formatting artifacts and focus on actual contract content.
        """
        # Remove markdown headers and formatting
        text = re.sub(r'^#{1,6}\s+.*$', '', contract_text, flags=re.MULTILINE)
        
        # Remove markdown emphasis
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove markdown lists that aren't contract content
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace but preserve paragraph structure
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove common non-contract content patterns
        non_contract_patterns = [
            r'(?i)^(contract analysis|legal review|summary|overview):.*$',
            r'(?i)^(note|disclaimer|warning):.*$',
            r'(?i)^(created by|generated by|analyzed by):.*$',
        ]
        
        for pattern in non_contract_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Clean up and normalize
        text = text.strip()
        
        # If text is too short after cleaning, it might not be a real contract
        if len(text.strip()) < 100:
            logger.warning("Contract text appears to be very short after preprocessing")
        
        return text
    
    def _analyze_contract_metadata(self, contract_text: str) -> Dict[str, Any]:
        """
        Analyze contract structure and content to understand what type of contract this is
        and what specific legal areas it touches.
        """
        text_lower = contract_text.lower()
        
        # Detect contract type based on content analysis
        contract_type = "General"
        type_indicators = {
            "Employment": ["employee", "employer", "employment", "salary", "wage", "termination", "workplace", "job duties", "position", "work schedule"],
            "Service": ["services", "service provider", "client", "deliverables", "scope of work", "performance"],
            "NDA": ["confidential", "non-disclosure", "proprietary", "trade secret", "confidentiality"],
            "Rental": ["tenant", "landlord", "rent", "lease", "property", "premises", "rental"],
            "Sales": ["purchase", "buyer", "seller", "goods", "products", "sale", "delivery"],
            "Partnership": ["partner", "partnership", "joint venture", "profit sharing", "collaboration"]
        }
        
        max_score = 0
        for contract_type_candidate, keywords in type_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > max_score:
                max_score = score
                contract_type = contract_type_candidate
        
        # Analyze content areas
        has_data_processing = any(term in text_lower for term in [
            "personal data", "data processing", "privacy", "information", "data subject", "gdpr", "pdpa"
        ])
        
        has_termination_clauses = any(term in text_lower for term in [
            "termination", "terminate", "end of contract", "expiry", "cancellation"
        ])
        
        has_payment_terms = any(term in text_lower for term in [
            "payment", "pay", "salary", "wage", "compensation", "fee", "amount", "money"
        ])
        
        has_liability_clauses = any(term in text_lower for term in [
            "liable", "liability", "damages", "indemnify", "responsibility", "loss"
        ])
        
        has_ip_clauses = any(term in text_lower for term in [
            "intellectual property", "copyright", "patent", "trademark", "work product", "invention"
        ])
        
        # Extract meaningful sections
        sections = self._extract_meaningful_sections(contract_text)
        
        # Detect jurisdiction indicators in the text
        jurisdiction_indicators = {
            "MY": ["malaysia", "malaysian", "kuala lumpur", "ringgit", "employment act 1955"],
            "SG": ["singapore", "singaporean", "sgd", "singapore dollar"],
            "US": ["united states", "usd", "dollar", "state of", "california", "new york"],
            "EU": ["european union", "gdpr", "euro", "eur"]
        }
        
        detected_jurisdictions = []
        for jurisdiction, indicators in jurisdiction_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                detected_jurisdictions.append(jurisdiction)
        
        return {
            "type": contract_type,
            "has_data_processing": has_data_processing,
            "has_termination_clauses": has_termination_clauses,
            "has_payment_terms": has_payment_terms,
            "has_liability_clauses": has_liability_clauses,
            "has_ip_clauses": has_ip_clauses,
            "sections": sections,
            "detected_jurisdictions": detected_jurisdictions,
            "word_count": len(contract_text.split()),
            "is_substantial": len(contract_text.strip()) > 500  # Flag for substantial contracts
        }
    
    def _extract_meaningful_sections(self, contract_text: str) -> List[Dict[str, str]]:
        """
        Extract meaningful contract sections, ignoring formatting artifacts.
        """
        sections = []
        
        # Try different section detection patterns
        section_patterns = [
            r'\n\s*(\d+)\.\s*([A-Z][^.\n]*[.:]?)\s*\n((?:[^\n]+\n?)*?)(?=\n\s*\d+\.|$)',  # Numbered sections
            r'\n\s*([A-Z][A-Z\s]{2,}):?\s*\n((?:[^\n]+\n?)*?)(?=\n\s*[A-Z][A-Z\s]{2,}:|$)',  # ALL CAPS headers
            r'\n\s*([A-Z][^.\n]*):?\s*\n((?:[^\n]+\n?)*?)(?=\n\s*[A-Z][^.\n]*:|$)'  # Title Case headers
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, contract_text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.groups()) >= 2:
                    title = match.group(1).strip() if len(match.groups()) > 1 else f"Section {match.group(1)}"
                    content = match.group(2).strip() if len(match.groups()) > 2 else match.group(2).strip()
                    
                    # Skip sections that are too short or look like formatting artifacts
                    if len(content) > 50 and not self._is_formatting_artifact(title, content):
                        sections.append({
                            "title": title,
                            "content": content,
                            "word_count": len(content.split())
                        })
            
            if sections:  # If we found sections with one pattern, use those
                break
        
        # Fallback: split by paragraphs if no clear sections found
        if not sections:
            paragraphs = re.split(r'\n\s*\n\s*', contract_text)
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) > 100:  # Only substantial paragraphs
                    sections.append({
                        "title": f"Paragraph {i+1}",
                        "content": paragraph.strip(),
                        "word_count": len(paragraph.split())
                    })
        
        return sections
    
    def _is_formatting_artifact(self, title: str, content: str) -> bool:
        """
        Check if a section is likely a formatting artifact rather than actual contract content.
        """
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Skip common non-contract sections
        artifact_indicators = [
            "summary", "analysis", "review", "note", "disclaimer", "generated", 
            "created", "overview", "introduction", "conclusion", "appendix",
            "table of contents", "index", "header", "footer"
        ]
        
        if any(indicator in title_lower for indicator in artifact_indicators):
            return True
        
        # Skip sections that are mostly formatting
        if len(content.strip()) < 20:
            return True
        
        # Skip sections with too many special characters (likely formatting)
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content)
        if special_char_ratio > 0.3:
            return True
        
        return False
    
    def _get_granite_analysis_with_context(self, contract_text: str, metadata: Dict[str, Any], 
                                         compliance_checklist: Dict[str, Any], jurisdiction: str) -> str:
        """
        Enhanced prompting for IBM Granite with contract context and intelligent analysis.
        Optimized for TechXchange Hackathon submission.
        """
        if not self.watsonx_client:
            logger.warning("IBM WatsonX client not available, falling back to intelligent analysis")
            return self._get_intelligent_mock_analysis(contract_text, metadata, compliance_checklist, jurisdiction)
        
        try:
            logger.info("Engaging IBM Granite model for advanced legal analysis")
            
            # Use the enhanced prompt designed for Granite
            granite_response = self.watsonx_client.analyze_contract(
                contract_text=contract_text,
                compliance_checklist=compliance_checklist
            )
            
            logger.info(f"IBM Granite analysis completed successfully: {len(granite_response)} characters")
            
            # Validate Granite response quality
            if self._is_granite_response_minimal(granite_response):
                logger.info("IBM Granite response needs enhancement, combining with domain expertise")
                # Enhance minimal Granite response with our intelligent analysis
                enhanced_response = self._enhance_granite_response(
                    granite_response, contract_text, metadata, jurisdiction
                )
                return enhanced_response
            
            return granite_response
            
        except (APIError, AuthenticationError) as e:
            logger.error(f"IBM Granite API error: {e}")
            return self._get_intelligent_mock_analysis(contract_text, metadata, compliance_checklist, jurisdiction)
        except Exception as e:
            logger.error(f"Unexpected error with IBM Granite: {e}")
            return self._get_intelligent_mock_analysis(contract_text, metadata, compliance_checklist, jurisdiction)
    
    def _build_enhanced_granite_prompt(self, contract_text: str, metadata: Dict[str, Any], jurisdiction: str) -> str:
        """
        Build an intelligent prompt for Granite that focuses on actual contract content.
        """
        jurisdiction_name = {
            "MY": "Malaysia", "SG": "Singapore", "EU": "European Union", "US": "United States"
        }.get(jurisdiction, jurisdiction)
        
        prompt = f"""Analyze this {metadata['type']} contract for {jurisdiction_name} compliance.

CONTRACT CONTEXT:
- Type: {metadata['type']} contract
- Word Count: {metadata['word_count']} words
- Sections Identified: {len(metadata['sections'])}
- Data Processing Elements: {'Yes' if metadata['has_data_processing'] else 'No'}
- Termination Clauses: {'Yes' if metadata['has_termination_clauses'] else 'No'}
- Payment Terms: {'Yes' if metadata['has_payment_terms'] else 'No'}

ANALYSIS REQUIREMENTS:
1. Focus ONLY on actual contract clauses, ignore any headers, titles, or formatting
2. For flagged clauses, extract the EXACT clause text that has the issue
3. Only flag issues that are contextually relevant to the specific clause content
4. Provide jurisdiction-specific compliance analysis for {jurisdiction_name}

IMPORTANT: Do not flag issues on section headers, markdown formatting, or non-contractual text.
Only analyze substantive contractual provisions and obligations.

Return analysis in JSON format with summary, flagged_clauses, and compliance_issues arrays."""
        
        return prompt
    
    def _get_intelligent_mock_analysis(self, contract_text: str, metadata: Dict[str, Any], 
                                     compliance_checklist: Dict[str, Any], jurisdiction: str) -> str:
        """
        Intelligent mock analysis that adapts to the specific contract content and avoids repetitive outputs.
        Enhanced for IBM Granite compatibility with rigorous legal analysis.
        """
        flagged_clauses = []
        compliance_issues = []
        seen_issues = set()  # Track unique issues to prevent duplicates
        
        logger.info(f"Starting rigorous intelligent analysis for {metadata['type']} contract with {len(metadata['sections'])} sections")
        
        # Analyze the entire contract holistically first to identify key areas
        contract_analysis = self._perform_comprehensive_contract_analysis(
            contract_text, metadata, jurisdiction
        )
        
        # Extract unique flagged clauses with strict criteria
        for issue in contract_analysis.get('flagged_clauses', []):
            issue_key = f"{issue['issue'][:50]}_{issue['severity']}"  # Create unique key
            if issue_key not in seen_issues and self._is_substantive_legal_issue(issue, contract_text):
                seen_issues.add(issue_key)
                flagged_clauses.append(issue)
        
        # Generate compliance issues based on actual contract content and gaps
        compliance_issues = self._generate_smart_compliance_issues(
            contract_text, metadata, jurisdiction
        )
        
        # Validate and clean compliance issues to prevent malformed data
        compliance_issues = self._validate_compliance_issues(compliance_issues, jurisdiction)
        
        # Apply critical analysis - only flag serious violations
        flagged_clauses = self._apply_critical_legal_analysis(flagged_clauses, metadata, jurisdiction)
        
        # Generate contextual summary
        summary = self._generate_contextual_summary(
            flagged_clauses, compliance_issues, metadata, jurisdiction
        )
        
        logger.info(f"Rigorous analysis complete: {len(flagged_clauses)} unique flagged clauses, {len(compliance_issues)} compliance issues")
        
        return json.dumps({
            "summary": summary,
            "flagged_clauses": flagged_clauses,
            "compliance_issues": compliance_issues
        })
    
    def _analyze_section_intelligently(self, section: Dict[str, str], metadata: Dict[str, Any], 
                                     jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Intelligent section analysis that only flags relevant issues on appropriate content.
        """
        issues = []
        title = section['title'].lower()
        content = section['content'].lower()
        
        # Only analyze if this is substantial contract content
        if section['word_count'] < 10:
            return issues
        
        # Employment-specific analysis
        if metadata['type'] == 'Employment':
            if 'termination' in title or 'termination' in content:
                if 'without notice' in content and 'misconduct' not in content:
                    issues.append({
                        "clause_text": self._extract_relevant_clause(section['content'], 'without notice'),
                        "issue": f"Termination without notice may not comply with {jurisdiction} employment law minimum notice requirements",
                        "severity": "high"
                    })
                
                # Check for inadequate notice periods
                notice_match = re.search(r'(\d+)\s*(day|week|month)', content)
                if notice_match:
                    notice_period = int(notice_match.group(1))
                    period_type = notice_match.group(2)
                    
                    if period_type == 'day' and notice_period < 7:
                        issues.append({
                            "clause_text": self._extract_relevant_clause(section['content'], notice_match.group(0)),
                            "issue": f"Notice period of {notice_period} days may be insufficient under {jurisdiction} employment standards",
                            "severity": "medium"
                        })
            
            if ('wage' in content or 'salary' in content) and 'overtime' not in content:
                issues.append({
                    "clause_text": self._extract_relevant_clause(section['content'], 'wage salary'),
                    "issue": f"Compensation clause lacks overtime provisions required under {jurisdiction} employment law",
                    "severity": "medium"
                })
        
        # Data processing analysis (only for contracts that actually process data)
        if metadata['has_data_processing'] and ('data' in content or 'information' in content):
            if 'personal data' in content and 'consent' not in content:
                issues.append({
                    "clause_text": self._extract_relevant_clause(section['content'], 'personal data'),
                    "issue": f"Data processing clause lacks explicit consent mechanisms required under {jurisdiction} privacy law",
                    "severity": "high"
                })
        
        # Liability analysis
        if 'liability' in content or 'damages' in content:
            # Look for liability caps that might be too low
            amount_match = re.search(r'(\d+(?:,\d+)*)', content)
            if amount_match:
                amount = int(amount_match.group(1).replace(',', ''))
                if 'liability' in content and amount < 10000:
                    issues.append({
                        "clause_text": self._extract_relevant_clause(section['content'], amount_match.group(0)),
                        "issue": f"Liability limitation of {amount} may be insufficient for this type of contract",
                        "severity": "low"
                    })
        
        return issues
    
    def _extract_relevant_clause(self, section_content: str, search_terms: str) -> str:
        """
        Extract the most relevant sentence or clause that contains the search terms.
        """
        sentences = re.split(r'[.!?]+', section_content)
        
        # Find the sentence containing the search terms
        for sentence in sentences:
            if any(term.lower() in sentence.lower() for term in search_terms.split()):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 10:
                    return clean_sentence + "."
        
        # Fallback: return first substantial sentence
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                return sentence.strip() + "."
        
        # Last resort: return truncated content
        return section_content[:150] + "..." if len(section_content) > 150 else section_content
    
    def _generate_smart_compliance_issues(self, contract_text: str, metadata: Dict[str, Any], 
                                        jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Generate critical compliance issues that are specific to the contract type and jurisdiction.
        Enhanced for IBM Granite compatibility with specific statutory references.
        """
        issues = []
        text_lower = contract_text.lower()
        
        # Employment contract compliance (only for employment contracts in Malaysia)
        if metadata['type'] == 'Employment' and jurisdiction == 'MY':
            requirements = []
            recommendations = []
            
            # Check for critical Employment Act 1955 violations
            if not re.search(r'(?:notice|termination).*(?:\d+.*(?:week|month|day))', text_lower):
                requirements.append("Termination notice provisions do not meet Employment Act 1955 Section 12 minimum requirements")
                recommendations.append("Add termination clause specifying minimum 4 weeks notice for employees with >2 years service")
            
            if not re.search(r'overtime.*(?:compensation|payment|rate)', text_lower):
                requirements.append("Missing overtime compensation violates Employment Act 1955 Section 60A")
                recommendations.append("Include overtime payment at minimum 1.5x normal hourly rate as mandated by Section 60A")
            
            if not re.search(r'annual.*leave|vacation.*day', text_lower):
                requirements.append("Missing annual leave entitlement violates Employment Act 1955 Section 60E")
                recommendations.append("Specify annual leave: 8 days (<2 years), 12 days (2-5 years), 16 days (>5 years)")
            
            # Check working hours violations
            hours_match = re.search(r'(\d+).*hours?.*(?:per|each).*(?:day|week)', text_lower)
            if hours_match:
                hours = int(hours_match.group(1))
                if 'week' in hours_match.group(0) and hours > 48:
                    requirements.append(f"Working hours of {hours} per week exceeds Employment Act 1955 maximum of 48 hours")
                    recommendations.append("Reduce working hours to comply with 48-hour weekly maximum under Section 60A")
                elif 'day' in hours_match.group(0) and hours > 8:
                    requirements.append(f"Working hours of {hours} per day exceeds Employment Act 1955 maximum of 8 hours")
                    recommendations.append("Reduce daily working hours to 8-hour maximum as mandated by Employment Act")
            
            if requirements:
                issues.append({
                    "law": "EMPLOYMENT_ACT_MY",
                    "missing_requirements": requirements,
                    "recommendations": recommendations
                })
        
        # Data protection compliance (only for contracts that actually process personal data)
        if metadata['has_data_processing']:
            law_id = f"PDPA_{jurisdiction}" if jurisdiction in ['MY', 'SG'] else f"GDPR_{jurisdiction}" if jurisdiction == 'EU' else f"CCPA_{jurisdiction}"
            law_name = {"MY": "Personal Data Protection Act 2010", "SG": "Personal Data Protection Act 2012", "EU": "GDPR", "US": "CCPA"}.get(jurisdiction, "privacy law")
            
            requirements = []
            recommendations = []
            
            # Critical data protection violations only
            if not re.search(r'consent.*(?:explicit|written|informed)', text_lower):
                requirements.append(f"Missing explicit consent mechanisms required under {law_name}")
                recommendations.append(f"Implement clear, informed consent procedures before collecting personal data")
            
            if jurisdiction in ['MY', 'SG'] and not re.search(r'data subject.*rights', text_lower):
                requirements.append(f"Missing data subject rights provisions required under {law_name}")
                recommendations.append("Include data subject rights: access, correction, and withdrawal of consent")
            
            if jurisdiction == 'EU' and not re.search(r'(?:access|rectification|erasure|portability)', text_lower):
                requirements.append("Missing GDPR data subject rights (access, rectification, erasure, portability)")
                recommendations.append("Implement all GDPR data subject rights as mandated by Articles 15-20")
            
            if requirements:
                issues.append({
                    "law": law_id,
                    "missing_requirements": requirements,
                    "recommendations": recommendations
                })
        
        return issues
    
    def _generate_contextual_summary(self, flagged_clauses: List[Dict], compliance_issues: List[Dict], 
                                   metadata: Dict[str, Any], jurisdiction: str) -> str:
        """
        Generate a contextual summary based on the specific contract and findings.
        """
        jurisdiction_name = {
            "MY": "Malaysia", "SG": "Singapore", "EU": "European Union", "US": "United States"
        }.get(jurisdiction, jurisdiction)
        
        total_issues = len(flagged_clauses) + len(compliance_issues)
        contract_type = metadata['type']
        
        if total_issues == 0:
            return f"Review of this {contract_type.lower()} contract for {jurisdiction_name} compliance found no significant issues requiring immediate attention."
        
        # Count severity levels
        high_severity = sum(1 for clause in flagged_clauses if clause.get('severity') == 'high')
        medium_severity = sum(1 for clause in flagged_clauses if clause.get('severity') == 'medium')
        
        summary_parts = []
        
        # Main assessment
        if high_severity > 0:
            summary_parts.append(f"This {contract_type.lower()} contract contains {high_severity} high-priority compliance issue{'s' if high_severity != 1 else ''} for {jurisdiction_name}")
        elif medium_severity > 0:
            summary_parts.append(f"This {contract_type.lower()} contract has {medium_severity} moderate compliance concern{'s' if medium_severity != 1 else ''} for {jurisdiction_name}")
        else:
            summary_parts.append(f"This {contract_type.lower()} contract has minor compliance gaps for {jurisdiction_name}")
        
        # Add specific areas of concern
        concern_areas = []
        if compliance_issues:
            laws_affected = [issue['law'] for issue in compliance_issues]
            if 'EMPLOYMENT_ACT_MY' in laws_affected:
                concern_areas.append("employment law compliance")
            if any('PDPA' in law for law in laws_affected):
                concern_areas.append("data protection requirements")
            if any('GDPR' in law for law in laws_affected):
                concern_areas.append("GDPR compliance")
        
        if concern_areas:
            summary_parts.append(f"requiring attention in: {', '.join(concern_areas)}")
        
        # Add recommendation level
        if high_severity > 0 or len(compliance_issues) > 2:
            summary_parts.append("Recommend legal review before contract execution.")
        elif total_issues > 0:
            summary_parts.append("Consider addressing identified issues to ensure full compliance.")
        
        return " ".join(summary_parts)
    
    def _generate_comprehensive_analysis(self, contract_text: str, metadata: Dict[str, Any], 
                                       jurisdiction: str) -> Dict[str, Any]:
        """
        Generate comprehensive analysis when no issues are initially found.
        """
        # This should rarely be called with the new intelligent analysis
        return {
            "summary": f"Comprehensive review of this {metadata['type'].lower()} contract completed for {jurisdiction} jurisdiction.",
            "flagged_clauses": [],
            "compliance_issues": []
        }

    async def calculate_risk_score(self, analysis_response: ContractAnalysisResponse) -> ComplianceRiskScore:
            """
            Calculate comprehensive risk scoring with proper weighting for severity and violations.
            Uses IBM Granite AI for enhanced risk assessment when available.
            """
            violation_categories = set()
            jurisdiction_risks = {}
            financial_risk = 0.0
            
            # Enhanced risk calculation with proper severity weighting
            base_risk_score = 100
            risk_deductions = 0
            
            # Analyze compliance issues with proper weighting
            for issue in analysis_response.compliance_issues or []:
                violation_categories.add(issue.law)
                
                # Calculate law-specific risk
                law_risk = self._get_risk_from_law(issue.law, len(issue.missing_requirements))
                financial_risk += law_risk
                
                # Deduct points based on number of missing requirements
                missing_count = len(issue.missing_requirements)
                if missing_count >= 4:
                    risk_deductions += 25  # Severe compliance gaps
                elif missing_count >= 2:
                    risk_deductions += 15  # Moderate compliance gaps
                else:
                    risk_deductions += 8   # Minor compliance gaps
                
                jurisdiction = analysis_response.jurisdiction or "MY"
                jurisdiction_risks[jurisdiction] = jurisdiction_risks.get(jurisdiction, 0) + law_risk
            
            # Analyze flagged clauses with severity weighting
            for clause in analysis_response.flagged_clauses or []:
                severity = getattr(clause, 'severity', 'medium')
                
                if severity == 'high':
                    risk_deductions += 20
                    financial_risk += 15000
                elif severity == 'medium':
                    risk_deductions += 12
                    financial_risk += 8000
                else:  # low severity
                    risk_deductions += 5
                    financial_risk += 3000
            
            # Calculate final risk score (capped at 0-100)
            final_score = max(0, min(100, base_risk_score - risk_deductions))
            
            # Determine risk level
            if final_score >= 80:
                risk_level = "Low"
            elif final_score >= 60:
                risk_level = "Medium"
            elif final_score >= 40:
                risk_level = "High"
            else:
                risk_level = "Critical"
            
            return ComplianceRiskScore(
                overall_score=final_score,
                financial_risk_estimate=financial_risk,
                violation_categories=list(violation_categories),
                jurisdiction_risks=jurisdiction_risks
            )
    
    def _get_risk_from_law(self, law_id: str, violation_count: int) -> float:
        """Calculate financial risk based on law type and violation severity."""
        base_risks = {
            "EMPLOYMENT_ACT_MY": 12000,
            "PDPA_MY": 20000,
            "PDPA_SG": 25000,
            "GDPR_EU": 50000,
            "CCPA_US": 30000
        }
        
        base_risk = base_risks.get(law_id, 10000)
        return base_risk * (1 + (violation_count * 0.3))  # Scale by violation count
    
    def _preprocess_contract_text(self, contract_text: str) -> str:
        """
        Enhanced preprocessing to remove formatting artifacts and focus ONLY on actual contract content.
        This is the key fix to prevent markdown headers from being analyzed as contract clauses.
        """
        # Step 1: Remove markdown headers completely (these are NOT contract content)
        text = re.sub(r'^#{1,6}\s+.*$', '', contract_text, flags=re.MULTILINE)
        
        # Step 2: Remove markdown formatting but keep the content
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code spans
        
        # Step 3: Remove markdown list markers that aren't part of contract content
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+(?=[A-Z])', '', text, flags=re.MULTILINE)
        
        # Step 4: Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Step 5: Remove common document metadata and non-contract content
        non_contract_patterns = [
            r'(?i)^(contract analysis|legal review|summary|overview|analysis|review):.*$',
            r'(?i)^(note|disclaimer|warning|important):.*$',
            r'(?i)^(created by|generated by|analyzed by|document|title):.*$',
            r'(?i)^(version|date|status|author):.*$',
            r'(?i)^(page \d+|header|footer):.*$',
            r'(?i)^\s*(summary|conclusion|recommendations?):\s*$',  # Section headers only
            r'(?i)^\s*-{3,}\s*$',  # Markdown dividers
            r'(?i)^\s*={3,}\s*$',  # Underlines
        ]
        
        for pattern in non_contract_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Step 6: Clean up whitespace but preserve paragraph structure
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)              # Multiple spaces to single
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Leading whitespace
        
        # Step 7: Remove lines that are clearly formatting artifacts or too short to be meaningful
        lines = text.split('\n')
        meaningful_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                meaningful_lines.append('')  # Preserve paragraph breaks
                continue
                
            # Skip lines that are clearly not contract content
            if (len(line) < 10 or  # Too short
                line.isupper() and len(line.split()) < 5 or  # Short ALL CAPS (likely headers)
                re.match(r'^[^\w]*$', line) or  # Only special characters
                re.match(r'^(page|section|article|chapter)\s*\d+\s*$', line, re.IGNORECASE) or  # Page/section numbers
                line.count('_') > len(line) // 3 or  # Too many underscores (formatting)
                line.count('-') > len(line) // 3):   # Too many dashes (formatting)
                continue
            
            meaningful_lines.append(line)
        
        text = '\n'.join(meaningful_lines)
        
        # Step 8: Final cleanup
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)  # No more than double newlines
        
        # Step 9: Validation - if text is too short after cleaning, it might not be a real contract
        if len(text.strip()) < 100:
            logger.warning(f"Contract text appears to be very short after preprocessing: {len(text.strip())} characters")
        
        logger.info(f"Text preprocessing complete. Removed formatting artifacts. Clean text length: {len(text)}")
        return text
    
    def _analyze_contract_metadata(self, contract_text: str) -> Dict[str, Any]:
        """
        Enhanced contract analysis that focuses ONLY on substantive contract content.
        Ignores formatting artifacts and document metadata.
        """
        text_lower = contract_text.lower()
        
        # Enhanced contract type detection with more sophisticated analysis
        contract_type = "General"
        type_scores = {}
        
        type_indicators = {
            "Employment": {
                "strong": ["employee", "employer", "employment", "position", "job duties", "workplace", "termination of employment"],
                "moderate": ["salary", "wage", "work schedule", "benefits", "leave", "resignation"],
                "weak": ["work", "duties", "responsibilities"]
            },
            "Service": {
                "strong": ["service provider", "client", "deliverables", "scope of work", "statement of work"],
                "moderate": ["services", "performance", "completion", "milestone"],
                "weak": ["provide", "deliver", "complete"]
            },
            "NDA": {
                "strong": ["non-disclosure", "confidentiality agreement", "trade secret", "proprietary information"],
                "moderate": ["confidential", "proprietary", "confidentiality"],
                "weak": ["information", "disclosure"]
            },
            "Rental": {
                "strong": ["landlord", "tenant", "lease agreement", "rental agreement", "premises"],
                "moderate": ["rent", "lease", "property", "occupancy"],
                "weak": ["monthly", "deposit"]
            },
            "Sales": {
                "strong": ["purchase agreement", "sale agreement", "buyer", "seller", "transfer of ownership"],
                "moderate": ["purchase", "sale", "goods", "products", "delivery"],
                "weak": ["buy", "sell", "payment"]
            },
            "Partnership": {
                "strong": ["partnership agreement", "joint venture", "business partnership", "profit sharing"],
                "moderate": ["partner", "partnership", "collaboration", "venture"],
                "weak": ["together", "joint", "share"]
            }
        }
        
        # Calculate weighted scores for each contract type
        for contract_type_candidate, indicators in type_indicators.items():
            score = 0
            
            # Strong indicators (weight: 3)
            for indicator in indicators["strong"]:
                if indicator in text_lower:
                    score += 3
            
            # Moderate indicators (weight: 2)
            for indicator in indicators["moderate"]:
                if indicator in text_lower:
                    score += 2
            
            # Weak indicators (weight: 1)
            for indicator in indicators["weak"]:
                if indicator in text_lower:
                    score += 1
            
            type_scores[contract_type_candidate] = score
        
        # Select the type with the highest score (minimum threshold of 3)
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] >= 3:
                contract_type = best_type
        
        logger.info(f"Contract type analysis: {type_scores} -> Selected: {contract_type}")
        
        # Enhanced content analysis with better detection
        has_data_processing = any(phrase in text_lower for phrase in [
            "personal data", "data processing", "data protection", "privacy policy",
            "data subject", "gdpr", "pdpa", "collect information", "process data"
        ])
        
        has_termination_clauses = any(phrase in text_lower for phrase in [
            "termination", "terminate this", "end of contract", "contract expiry",
            "cancellation", "breach of contract", "dissolution"
        ])
        
        has_payment_terms = any(phrase in text_lower for phrase in [
            "payment terms", "payment schedule", "compensation", "remuneration",
            "salary", "wage", "fee", "amount due", "invoice"
        ])
        
        has_liability_clauses = any(phrase in text_lower for phrase in [
            "liability", "liable for", "damages", "indemnify", "indemnification",
            "limitation of liability", "hold harmless", "responsibility for"
        ])
        
        has_ip_clauses = any(phrase in text_lower for phrase in [
            "intellectual property", "copyright", "patent", "trademark",
            "work product", "invention", "proprietary rights", "trade secret"
        ])
        
        # Extract meaningful sections with improved filtering
        sections = self._extract_contract_sections_only(contract_text)
        
        # Enhanced jurisdiction detection
        jurisdiction_indicators = {
            "MY": ["malaysia", "malaysian", "kuala lumpur", "ringgit", "rm ", "employment act 1955", "companies act 2016"],
            "SG": ["singapore", "singaporean", "sgd", "singapore dollar", "companies act singapore"],
            "US": ["united states", "usd", "us dollar", "state of california", "state of new york", "delaware"],
            "EU": ["european union", "gdpr", "euro", "eur", "brussels", "directive 95/46/ec"]
        }
        
        detected_jurisdictions = []
        for jurisdiction, indicators in jurisdiction_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                detected_jurisdictions.append(jurisdiction)
        
        # Calculate actual contract substance metrics
        word_count = len([word for word in contract_text.split() if len(word) > 2])  # Exclude short words
        sentence_count = len(re.findall(r'[.!?]+', contract_text))
        
        # Determine if this is a substantial contract worth analyzing
        is_substantial = (
            len(contract_text.strip()) > 500 and
            word_count > 100 and
            sentence_count > 5 and
            len(sections) > 0
        )
        
        metadata = {
            "type": contract_type,
            "type_confidence": type_scores.get(contract_type, 0),
            "has_data_processing": has_data_processing,
            "has_termination_clauses": has_termination_clauses,
            "has_payment_terms": has_payment_terms,
            "has_liability_clauses": has_liability_clauses,
            "has_ip_clauses": has_ip_clauses,
            "sections": sections,
            "detected_jurisdictions": detected_jurisdictions,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "is_substantial": is_substantial
        }
        
        logger.info(f"Contract metadata analysis complete: {contract_type} contract with {len(sections)} substantive sections")
        return metadata
    
    def _extract_contract_sections_only(self, contract_text: str) -> List[Dict[str, str]]:
        """
        Extract ONLY meaningful contract sections, completely ignoring formatting artifacts.
        This is crucial for preventing analysis of document headers and formatting.
        """
        sections = []
        
        # Multiple patterns to detect genuine contract sections vs formatting
        section_patterns = [
            # Pattern 1: Numbered contract sections (e.g., "1. Definitions", "2.1 Scope")
            r'\n\s*(\d+(?:\.\d+)*)\.\s+([A-Z][^.\n]{5,50}?)\s*\n((?:(?!\n\s*\d+(?:\.\d+)*\.)(?:[^\n]+\n?))*)',
            
            # Pattern 2: Lettered sections (e.g., "A. Terms", "B. Conditions")
            r'\n\s*([A-Z])\.\s+([A-Z][^.\n]{5,50}?)\s*\n((?:(?!\n\s*[A-Z]\.)(?:[^\n]+\n?))*)',
            
            # Pattern 3: Named sections in contracts (e.g., "WHEREAS", "NOW THEREFORE")
            r'\n\s*(WHEREAS|NOW THEREFORE|WITNESSETH|RECITALS?)\s*[,:]\s*\n((?:[^\n]+\n?)*?)(?=\n\s*(?:WHEREAS|NOW THEREFORE|WITNESSETH|\d+\.|[A-Z]{3,})|$)',
            
            # Pattern 4: Title case sections with substantial content
            r'\n\s*([A-Z][a-z][^.\n]{10,80}?)\s*[:.]?\s*\n((?:[^\n]+\n?){3,}?)(?=\n\s*[A-Z][a-z][^.\n]{10,80}?[:.]?\s*\n|$)'
        ]
        
        for pattern_idx, pattern in enumerate(section_patterns):
            matches = list(re.finditer(pattern, contract_text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2:
                    if len(groups) == 3:
                        section_id, title, content = groups
                    else:
                        title, content = groups
                        section_id = f"Section {len(sections) + 1}"
                    
                    title = title.strip()
                    content = content.strip()
                    
                    # Strict filtering for genuine contract content
                    if self._is_genuine_contract_section(title, content):
                        sections.append({
                            "id": section_id,
                            "title": title,
                            "content": content,
                            "word_count": len(content.split()),
                            "pattern_used": pattern_idx + 1
                        })
            
            # If we found good sections with one pattern, prioritize those
            if len(sections) >= 3:
                break
        
        # Fallback for contracts without clear section headers
        if len(sections) < 2:
            paragraphs = self._extract_meaningful_paragraphs(contract_text)
            sections.extend(paragraphs)
        
        # Sort by appearance order and limit to most substantial sections
        sections = sorted(sections, key=lambda x: x.get('word_count', 0), reverse=True)[:10]
        
        logger.info(f"Extracted {len(sections)} genuine contract sections for analysis")
        return sections
    
    def _is_genuine_contract_section(self, title: str, content: str) -> bool:
        """
        Determine if a section is genuine contract content vs formatting artifact.
        This is the key method to prevent analysis of non-contractual content.
        """
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Immediately reject if title indicates non-contract content
        non_contract_titles = [
            "summary", "analysis", "review", "note", "disclaimer", "generated",
            "created", "overview", "introduction", "conclusion", "appendix",
            "table of contents", "index", "header", "footer", "document",
            "title", "subject", "re:", "from:", "to:", "date:", "version",
            "page", "confidential", "draft", "final", "approved"
        ]
        
        if any(nc_title in title_lower for nc_title in non_contract_titles):
            logger.debug(f"Rejected section '{title}' - contains non-contract title indicator")
            return False
        
        # Reject very short content (likely formatting)
        if len(content.strip()) < 50:
            logger.debug(f"Rejected section '{title}' - content too short ({len(content.strip())} chars)")
            return False
        
        # Reject content with too many special characters (formatting artifacts)
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / max(len(content), 1)
        if special_char_ratio > 0.4:
            logger.debug(f"Rejected section '{title}' - too many special characters ({special_char_ratio:.2f})")
            return False
        
        # Reject if content is mostly uppercase (likely headers/formatting)
        upper_ratio = sum(1 for c in content if c.isupper()) / max(len([c for c in content if c.isalpha()]), 1)
        if upper_ratio > 0.7:
            logger.debug(f"Rejected section '{title}' - mostly uppercase ({upper_ratio:.2f})")
            return False
        
        # Require minimum word count and sentence structure
        word_count = len(content.split())
        sentence_count = len(re.findall(r'[.!?]+', content))
        
        if word_count < 15 or sentence_count < 1:
            logger.debug(f"Rejected section '{title}' - insufficient content (words: {word_count}, sentences: {sentence_count})")
            return False
        
        # Positive indicators of contract content
        contract_indicators = [
            "party", "parties", "agreement", "contract", "shall", "will",
            "hereby", "whereas", "therefore", "obligations", "rights",
            "terms", "conditions", "provision", "clause", "section"
        ]
        
        indicator_count = sum(1 for indicator in contract_indicators if indicator in content_lower)
        if indicator_count < 2:
            logger.debug(f"Rejected section '{title}' - insufficient contract indicators ({indicator_count})")
            return False
        
        logger.debug(f"Accepted section '{title}' - genuine contract content (words: {word_count}, indicators: {indicator_count})")
        return True
    
    def _extract_meaningful_paragraphs(self, contract_text: str) -> List[Dict[str, str]]:
        """
        Extract meaningful paragraphs when no clear sections are found.
        """
        paragraphs = re.split(r'\n\s*\n\s*', contract_text)
        meaningful_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            
            if self._is_genuine_contract_section(f"Paragraph {i+1}", paragraph):
                meaningful_paragraphs.append({
                    "id": f"P{i+1}",
                    "title": f"Paragraph {i+1}",
                    "content": paragraph,
                    "word_count": len(paragraph.split()),
                    "pattern_used": 0  # Fallback pattern
                })
        
        return meaningful_paragraphs
    
    def _build_enhanced_granite_prompt(self, contract_text: str, metadata: Dict[str, Any], jurisdiction: str) -> str:
        """
        Build an enhanced prompt that prevents analysis of formatting artifacts.
        """
        jurisdiction_name = {
            "MY": "Malaysia", "SG": "Singapore", "EU": "European Union", "US": "United States"
        }.get(jurisdiction, jurisdiction)
        
        # Create content focus guidance
        content_focus = f"""CRITICAL INSTRUCTION: ONLY analyze substantive contractual provisions. 

IGNORE completely:
- Document headers, titles, or section names
- Markdown formatting (###, **, *, etc.)
- Document metadata or analysis summaries
- Any content that appears to be document formatting rather than contract terms

ANALYZE only:
- Actual contractual obligations and rights
- Specific terms and conditions
- Substantive legal provisions
- Binding commitments between parties

CONTRACT CONTEXT:
- Type: {metadata['type']} contract (confidence: {metadata.get('type_confidence', 0)})
- Substantive sections: {len([s for s in metadata['sections'] if s['word_count'] > 20])}
- Contains data processing: {'Yes' if metadata['has_data_processing'] else 'No'}
- Contains termination clauses: {'Yes' if metadata['has_termination_clauses'] else 'No'}
- Contains payment terms: {'Yes' if metadata['has_payment_terms'] else 'No'}
- Word count: {metadata['word_count']} meaningful words

ANALYSIS REQUIREMENTS FOR {jurisdiction_name}:
1. Extract ONLY the exact contractual clause text that has legal issues
2. Focus on binding obligations, not descriptive text
3. Identify specific legal non-compliance, not formatting issues
4. Provide actionable legal recommendations
5. Consider jurisdiction-specific requirements for {jurisdiction_name}

OUTPUT FORMAT: Valid JSON with summary, flagged_clauses, and compliance_issues arrays."""
        
        return content_focus

    def _is_granite_response_minimal(self, response_text: str) -> bool:
        """
        Enhanced detection of minimal AI responses that need augmentation.
        """
        try:
            response_json = json.loads(response_text)
            
            # Check for truly minimal responses
            flagged_count = len(response_json.get("flagged_clauses", []))
            compliance_count = len(response_json.get("compliance_issues", []))
            summary_length = len(response_json.get("summary", ""))
            
            # Consider minimal if very few issues found AND short summary
            is_minimal = (
                (flagged_count + compliance_count) < 2 and
                summary_length < 100
            )
            
            logger.info(f"Response assessment: {flagged_count} flagged, {compliance_count} compliance issues, {summary_length} char summary -> {'Minimal' if is_minimal else 'Comprehensive'}")
            return is_minimal
            
        except json.JSONDecodeError:
            logger.warning("Could not parse AI response as JSON - treating as minimal")
            return True
    
    def _clean_ai_response(self, ai_json: Dict[str, Any], jurisdiction: str, contract_text: str) -> Dict[str, Any]:
        """
        Enhanced cleaning that removes any analysis of formatting artifacts and fixes malformed law fields.
        """
        cleaned_flagged = []
        cleaned_compliance = []
        
        # Clean flagged clauses - remove any that are clearly formatting artifacts
        for flag in ai_json.get("flagged_clauses", []):
            clause_text = flag.get("clause_text", "")
            
            # Skip if clause is clearly a formatting artifact
            if not self._is_substantive_clause(clause_text):
                logger.debug(f"Removing flagged clause - not substantive: {clause_text[:50]}...")
                continue
            
            cleaned_flagged.append(flag)
        
        # Clean compliance issues and fix malformed law fields
        valid_laws = ["EMPLOYMENT_ACT_MY", "PDPA_MY", "PDPA_SG", "GDPR_EU", "CCPA_US"]
        
        for issue in ai_json.get("compliance_issues", []):
            # Fix malformed law field (contains multiple laws separated by |)
            law_field = issue.get("law", "")
            
            if "|" in law_field:
                # Split and take the first valid law based on jurisdiction and contract type
                law_options = law_field.split("|")
                fixed_law = self._select_appropriate_law(law_options, jurisdiction, ai_json)
                issue["law"] = fixed_law
                logger.warning(f"Fixed malformed law field: '{law_field}' -> '{fixed_law}'")
            elif law_field not in valid_laws:
                # Set appropriate law based on jurisdiction
                issue["law"] = self._get_default_law_for_jurisdiction(jurisdiction)
                logger.warning(f"Invalid law field '{law_field}' replaced with '{issue['law']}'")
            
            # Clean up generic placeholder requirements
            requirements = issue.get("missing_requirements", [])
            cleaned_requirements = []
            
            for req in requirements:
                if req and not self._is_generic_placeholder(req):
                    cleaned_requirements.append(req)
            
            # If all requirements were generic, generate specific ones
            if not cleaned_requirements:
                cleaned_requirements = self._generate_specific_requirements(issue["law"], jurisdiction)
            
            issue["missing_requirements"] = cleaned_requirements
            
            # Clean up generic placeholder recommendations
            recommendations = issue.get("recommendations", [])
            cleaned_recommendations = []
            
            for rec in recommendations:
                if rec and not self._is_generic_placeholder(rec):
                    cleaned_recommendations.append(rec)
            
            # If all recommendations were generic, generate specific ones
            if not cleaned_recommendations:
                cleaned_recommendations = self._generate_specific_recommendations(issue["law"], jurisdiction)
            
            issue["recommendations"] = cleaned_recommendations
            
            cleaned_compliance.append(issue)
        
        ai_json["flagged_clauses"] = cleaned_flagged
        ai_json["compliance_issues"] = cleaned_compliance
        
        logger.info(f"Response cleaning complete: {len(cleaned_flagged)} flagged clauses, {len(cleaned_compliance)} compliance issues retained")
        return ai_json
    
    def _select_appropriate_law(self, law_options: List[str], jurisdiction: str, ai_json: Dict[str, Any]) -> str:
        """
        Select the most appropriate law from a list of options based on jurisdiction and contract context.
        """
        # Priority mapping based on jurisdiction
        jurisdiction_priority = {
            "MY": ["EMPLOYMENT_ACT_MY", "PDPA_MY"],
            "SG": ["PDPA_SG"],
            "EU": ["GDPR_EU"],
            "US": ["CCPA_US"]
        }
        
        # Get priority laws for jurisdiction
        priority_laws = jurisdiction_priority.get(jurisdiction, [])
        
        # Find the first matching priority law
        for priority_law in priority_laws:
            if priority_law in law_options:
                return priority_law
        
        # Fallback: return first valid law option
        valid_laws = ["EMPLOYMENT_ACT_MY", "PDPA_MY", "PDPA_SG", "GDPR_EU", "CCPA_US"]
        for law in law_options:
            if law.strip() in valid_laws:
                return law.strip()
        
        # Last resort: default for jurisdiction
        return self._get_default_law_for_jurisdiction(jurisdiction)
    
    def _get_default_law_for_jurisdiction(self, jurisdiction: str) -> str:
        """
        Get the default law for a given jurisdiction.
        """
        defaults = {
            "MY": "EMPLOYMENT_ACT_MY",
            "SG": "PDPA_SG", 
            "EU": "GDPR_EU",
            "US": "CCPA_US"
        }
        return defaults.get(jurisdiction, "EMPLOYMENT_ACT_MY")
    
    def _is_generic_placeholder(self, text: str) -> bool:
        """
        Check if text is a generic placeholder that should be replaced.
        """
        generic_phrases = [
            "specific statutory requirements missing",
            "specific actionable legal compliance steps",
            "general compliance concern identified",
            "review with legal counsel",
            "statutory requirements missing",
            "actionable legal compliance steps"
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in generic_phrases)
    
    def _generate_specific_requirements(self, law: str, jurisdiction: str) -> List[str]:
        """
        Generate specific missing requirements based on the law.
        """
        requirements_map = {
            "EMPLOYMENT_ACT_MY": [
                "Contract lacks minimum termination notice periods as required by Employment Act 1955 Section 12",
                "Missing overtime compensation provisions mandated by Employment Act 1955 Section 60A"
            ],
            "PDPA_MY": [
                "Missing explicit consent mechanisms required under Personal Data Protection Act 2010",
                "Lacks data subject rights provisions as mandated by PDPA 2010"
            ],
            "PDPA_SG": [
                "Missing consent notification requirements under Singapore PDPA 2012",
                "Lacks data protection officer designation as required by PDPA"
            ],
            "GDPR_EU": [
                "Missing lawful basis for processing personal data under GDPR Article 6",
                "Lacks data subject rights implementation as required by GDPR Articles 15-22"
            ],
            "CCPA_US": [
                "Missing consumer privacy rights disclosure under CCPA",
                "Lacks opt-out mechanisms as required by California Consumer Privacy Act"
            ]
        }
        
        return requirements_map.get(law, ["Contract requires legal review for compliance"])
    
    def _generate_specific_recommendations(self, law: str, jurisdiction: str) -> List[str]:
        """
        Generate specific recommendations based on the law.
        """
        recommendations_map = {
            "EMPLOYMENT_ACT_MY": [
                "Add termination clause with minimum 4 weeks notice for employees with >2 years service",
                "Include overtime payment at 1.5x normal rate as mandated by Section 60A"
            ],
            "PDPA_MY": [
                "Implement clear consent procedures with opt-in mechanisms",
                "Add data subject rights clauses covering access, correction, and withdrawal"
            ],
            "PDPA_SG": [
                "Include notification requirements before collecting personal data",
                "Designate data protection officer and include contact details"
            ],
            "GDPR_EU": [
                "Establish clear lawful basis for each type of data processing",
                "Implement comprehensive data subject rights response procedures"
            ],
            "CCPA_US": [
                "Add consumer privacy notice with clear disclosure of data practices",
                "Implement opt-out mechanisms for data selling and sharing"
            ]
        }
        
        return recommendations_map.get(law, ["Consult legal counsel for jurisdiction-specific compliance"])
    
    def _is_substantive_clause(self, clause_text: str) -> bool:
        """
        Determine if a clause is substantive contract content vs formatting artifact.
        """
        if not clause_text or len(clause_text.strip()) < 20:
            return False
        
        clause_lower = clause_text.lower()
        
        # Reject formatting artifacts
        formatting_indicators = [
            "###", "##", "#", "**", "*", "```", "---", "===",
            "summary", "analysis", "review", "note", "generated",
            "created by", "document", "title", "header", "footer"
        ]
        
        if any(indicator in clause_lower for indicator in formatting_indicators):
            return False
        
        # Require substantive legal language
        legal_indicators = [
            "shall", "will", "agree", "party", "parties", "contract",
            "obligation", "right", "term", "condition", "provision",
            "whereas", "therefore", "hereby", "subject to"
        ]
        
        return any(indicator in clause_lower for indicator in legal_indicators)
    
    def _perform_comprehensive_contract_analysis(self, contract_text: str, metadata: Dict[str, Any], 
                                               jurisdiction: str) -> Dict[str, Any]:
        """
        Perform comprehensive contract analysis using IBM Granite-inspired legal reasoning.
        Only flags genuine legal violations with specific statutory references.
        """
        flagged_clauses = []
        text_lower = contract_text.lower()
        
        # Employment contract analysis (MY jurisdiction specific)
        if metadata['type'] == 'Employment' and jurisdiction == 'MY':
            
            # 1. Termination notice requirements (Employment Act 1955, Section 12)
            termination_patterns = [
                r'terminate.*without.*notice',
                r'dismiss.*immediately',
                r'termination.*effective.*immediately'
            ]
            
            for pattern in termination_patterns:
                matches = re.finditer(pattern, contract_text, re.IGNORECASE)
                for match in matches:
                    context = self._extract_clause_context(contract_text, match.start(), match.end())
                    if 'misconduct' not in context.lower() and 'gross negligence' not in context.lower():
                        flagged_clauses.append({
                            "clause_text": context,
                            "issue": "Immediate termination without notice violates Employment Act 1955 Section 12 minimum notice requirements (4 weeks for employees with >2 years service)",
                            "severity": "high"
                        })
                        break  # Only flag once per contract
            
            # 2. Overtime compensation (Employment Act 1955, Section 60A)
            if not re.search(r'overtime.*(?:compensation|payment|rate)', text_lower):
                wage_section = re.search(r'(?:salary|wage|compensation).*?(?:\.|$)', contract_text, re.IGNORECASE | re.DOTALL)
                if wage_section:
                    context = wage_section.group(0)[:200] + ("..." if len(wage_section.group(0)) > 200 else "")
                    flagged_clauses.append({
                        "clause_text": context,
                        "issue": "Missing overtime compensation provisions required under Employment Act 1955 Section 60A (minimum 1.5x normal rate)",
                        "severity": "high"
                    })
            
            # 3. Annual leave entitlement (Employment Act 1955, Section 60E)
            if not re.search(r'annual.*leave|vacation.*days?|paid.*leave', text_lower):
                flagged_clauses.append({
                    "clause_text": "Employment terms and conditions",
                    "issue": "Missing annual leave entitlement violates Employment Act 1955 Section 60E (minimum 8 days for <2 years, 12 days for 2-5 years, 16 days for >5 years)",
                    "severity": "medium"
                })
            
            # 4. Working hours limitations (Employment Act 1955, Section 60A)
            hours_match = re.search(r'(\d+).*hours?.*(?:per|each).*(?:day|week)', text_lower)
            if hours_match:
                hours = int(hours_match.group(1))
                if 'week' in hours_match.group(0) and hours > 48:
                    context = self._extract_clause_context(contract_text, hours_match.start(), hours_match.end())
                    flagged_clauses.append({
                        "clause_text": context,
                        "issue": f"Working hours of {hours} per week exceeds Employment Act 1955 maximum of 48 hours per week",
                        "severity": "high"
                    })
                elif 'day' in hours_match.group(0) and hours > 8:
                    context = self._extract_clause_context(contract_text, hours_match.start(), hours_match.end())
                    flagged_clauses.append({
                        "clause_text": context,
                        "issue": f"Working hours of {hours} per day exceeds Employment Act 1955 maximum of 8 hours per day",
                        "severity": "high"
                    })
        
        # Data protection analysis (only if contract actually processes personal data)
        if metadata['has_data_processing']:
            law_name = f"PDPA_{jurisdiction}" if jurisdiction in ['MY', 'SG'] else f"GDPR_{jurisdiction}" if jurisdiction == 'EU' else f"CCPA_{jurisdiction}"
            
            # 1. Consent mechanisms
            if not re.search(r'consent.*(?:explicit|written|informed)', text_lower):
                data_clause = re.search(r'(?:personal.*data|information.*collect).*?(?:\.|$)', contract_text, re.IGNORECASE | re.DOTALL)
                if data_clause:
                    context = data_clause.group(0)[:200] + ("..." if len(data_clause.group(0)) > 200 else "")
                    flagged_clauses.append({
                        "clause_text": context,
                        "issue": f"Missing explicit consent mechanisms required under {law_name} for personal data processing",
                        "severity": "high"
                    })
            
            # 2. Data subject rights
            required_rights = ['access', 'rectification', 'erasure', 'portability'] if jurisdiction == 'EU' else ['access', 'correction', 'withdrawal']
            missing_rights = [right for right in required_rights if right not in text_lower]
            
            if len(missing_rights) > 2:
                flagged_clauses.append({
                    "clause_text": "Data processing provisions",
                    "issue": f"Missing data subject rights ({', '.join(missing_rights)}) required under {law_name}",
                    "severity": "medium"
                })
        
        # General contract law issues
        
        # 1. Unconscionable liability limitations
        liability_match = re.search(r'liability.*limited.*to.*(\d+)', text_lower)
        if liability_match:
            amount = int(liability_match.group(1))
            if amount < 1000:  # Unusually low liability cap
                context = self._extract_clause_context(contract_text, liability_match.start(), liability_match.end())
                flagged_clauses.append({
                    "clause_text": context,
                    "issue": f"Liability limitation of {amount} may be unconscionably low and unenforceable under contract law",
                    "severity": "medium"
                })
        
        # 2. Unilateral modification rights
        if re.search(r'(?:company|employer|party).*may.*(?:modify|change|alter).*(?:unilaterally|without.*consent)', text_lower):
            modification_clause = re.search(r'(?:company|employer|party).*may.*(?:modify|change|alter).*?(?:\.|$)', contract_text, re.IGNORECASE | re.DOTALL)
            if modification_clause:
                context = modification_clause.group(0)[:200] + ("..." if len(modification_clause.group(0)) > 200 else "")
                flagged_clauses.append({
                    "clause_text": context,
                    "issue": "Unilateral modification rights without consideration may be unenforceable under contract law",
                    "severity": "medium"
                })
        
        return {"flagged_clauses": flagged_clauses}
    
    def _extract_clause_context(self, contract_text: str, start_pos: int, end_pos: int, context_chars: int = 150) -> str:
        """
        Extract contextual clause text around a specific match position.
        """
        # Find sentence boundaries around the match
        start_context = max(0, start_pos - context_chars)
        end_context = min(len(contract_text), end_pos + context_chars)
        
        # Try to find sentence boundaries
        context = contract_text[start_context:end_context]
        
        # Clean up the context
        context = re.sub(r'\s+', ' ', context).strip()
        
        if len(context) > 200:
            context = context[:200] + "..."
        
        return context
    
    def _is_substantive_legal_issue(self, issue: Dict[str, Any], contract_text: str) -> bool:
        """
        Determine if an issue represents a substantive legal violation worth flagging.
        Enhanced criteria for IBM Granite analysis.
        """
        clause_text = issue.get('clause_text', '').lower()
        issue_description = issue.get('issue', '').lower()
        severity = issue.get('severity', 'low')
        
        # Skip if clause text is too generic or short
        if len(clause_text.strip()) < 20:
            return False
        
        # Skip if it's likely metadata or formatting
        metadata_indicators = [
            'summary', 'analysis', 'review', 'overview', 'title', 'header',
            'created by', 'generated by', 'document', 'version'
        ]
        
        if any(indicator in clause_text for indicator in metadata_indicators):
            return False
        
        # Only flag high and medium severity issues for critical analysis
        if severity not in ['high', 'medium']:
            return False
        
        # Ensure the issue is specific and actionable
        vague_issues = [
            'may not comply', 'might be insufficient', 'could be problematic',
            'appears to lack', 'seems to be missing'
        ]
        
        if any(vague in issue_description for vague in vague_issues):
            return False
        
        # Issue must reference specific law or regulation
        law_references = [
            'employment act', 'pdpa', 'gdpr', 'ccpa', 'section', 'regulation',
            'statutory', 'mandatory', 'required under'
        ]
        
        if not any(ref in issue_description for ref in law_references):
            return False
        
        return True
    
    def _apply_critical_legal_analysis(self, flagged_clauses: List[Dict[str, Any]], 
                                     metadata: Dict[str, Any], jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Apply critical legal analysis to filter only genuine violations.
        Designed for IBM Granite model compatibility.
        """
        filtered_clauses = []
        
        for clause in flagged_clauses:
            # Only include clauses that meet strict legal criteria
            if self._meets_granite_legal_standards(clause, metadata, jurisdiction):
                filtered_clauses.append(clause)
        
        # Limit to maximum 5 most critical issues to avoid information overload
        # Sort by severity and specificity
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        filtered_clauses.sort(
            key=lambda x: (
                severity_order.get(x.get('severity', 'low'), 1),
                len(x.get('issue', ''))  # More detailed issues first
            ),
            reverse=True
        )
        
        return filtered_clauses[:5]  # Maximum 5 issues
    
    def _meets_granite_legal_standards(self, clause: Dict[str, Any], 
                                     metadata: Dict[str, Any], jurisdiction: str) -> bool:
        """
        Check if a flagged clause meets IBM Granite model's legal analysis standards.
        """
        issue_text = clause.get('issue', '').lower()
        severity = clause.get('severity', 'low')
        
        # Must be high or medium severity
        if severity not in ['high', 'medium']:
            return False
        
        # Must reference specific legal requirements
        specific_legal_refs = [
            'employment act 1955',
            'section 12', 'section 60a', 'section 60e',
            'pdpa', 'gdpr', 'ccpa',
            'minimum notice', 'overtime rate', 'annual leave',
            'explicit consent', 'data subject rights'
        ]
        
        if not any(ref in issue_text for ref in specific_legal_refs):
            return False
        
        # Issue must be contextually relevant to contract type
        if metadata['type'] == 'Employment':
            employment_issues = ['employment act', 'notice', 'overtime', 'leave', 'hours']
            if not any(emp_issue in issue_text for emp_issue in employment_issues):
                return False
        
        if metadata['has_data_processing']:
            data_issues = ['consent', 'data subject', 'privacy', 'personal data']
            if 'data' in issue_text and not any(data_issue in issue_text for data_issue in data_issues):
                return False
        
        return True
    
    def _enhance_granite_response(self, granite_response: str, contract_text: str, 
                                metadata: Dict[str, Any], jurisdiction: str) -> str:
        """
        Enhance minimal IBM Granite responses with domain expertise for better legal analysis.
        """
        try:
            # Try to parse existing Granite response
            granite_data = json.loads(granite_response)
        except:
            # If parsing fails, start fresh with intelligent analysis
            return self._get_intelligent_mock_analysis(contract_text, metadata, {}, jurisdiction)
        
        # Get comprehensive analysis from our domain expertise
        comprehensive_analysis = self._perform_comprehensive_contract_analysis(
            contract_text, metadata, jurisdiction
        )
        
        # Merge Granite insights with our analysis
        enhanced_flagged_clauses = granite_data.get('flagged_clauses', [])
        
        # Add our domain-specific findings if they're not already covered
        for clause in comprehensive_analysis.get('flagged_clauses', []):
            if not any(clause['issue'] in existing['issue'] for existing in enhanced_flagged_clauses):
                enhanced_flagged_clauses.append(clause)
        
        # Generate enhanced compliance issues
        enhanced_compliance_issues = granite_data.get('compliance_issues', [])
        smart_issues = self._generate_smart_compliance_issues(contract_text, metadata, jurisdiction)
        
        for issue in smart_issues:
            if not any(issue['law'] == existing['law'] for existing in enhanced_compliance_issues):
                enhanced_compliance_issues.append(issue)
        
        # Generate comprehensive summary
        enhanced_summary = self._generate_contextual_summary(
            enhanced_flagged_clauses, enhanced_compliance_issues, metadata, jurisdiction
        )
        
        return json.dumps({
            "summary": enhanced_summary,
            "flagged_clauses": enhanced_flagged_clauses[:5],  # Limit for focus
            "compliance_issues": enhanced_compliance_issues
        })
    
    def _validate_compliance_issues(self, compliance_issues: List[Dict[str, Any]], jurisdiction: str) -> List[Dict[str, Any]]:
        """
        Validate and clean compliance issues to ensure proper structure and prevent malformed data.
        """
        validated_issues = []
        valid_laws = ["EMPLOYMENT_ACT_MY", "PDPA_MY", "PDPA_SG", "GDPR_EU", "CCPA_US"]
        
        for issue in compliance_issues:
            # Validate law field
            law = issue.get("law", "")
            if not law or law not in valid_laws:
                logger.warning(f"Invalid law field '{law}', setting default for jurisdiction {jurisdiction}")
                issue["law"] = self._get_default_law_for_jurisdiction(jurisdiction)
            
            # Validate missing_requirements
            requirements = issue.get("missing_requirements", [])
            if not requirements or not isinstance(requirements, list):
                issue["missing_requirements"] = self._generate_specific_requirements(issue["law"], jurisdiction)
            else:
                # Clean generic placeholders
                cleaned_reqs = [req for req in requirements if not self._is_generic_placeholder(req)]
                if not cleaned_reqs:
                    issue["missing_requirements"] = self._generate_specific_requirements(issue["law"], jurisdiction)
                else:
                    issue["missing_requirements"] = cleaned_reqs
            
            # Validate recommendations
            recommendations = issue.get("recommendations", [])
            if not recommendations or not isinstance(recommendations, list):
                issue["recommendations"] = self._generate_specific_recommendations(issue["law"], jurisdiction)
            else:
                # Clean generic placeholders
                cleaned_recs = [rec for rec in recommendations if not self._is_generic_placeholder(rec)]
                if not cleaned_recs:
                    issue["recommendations"] = self._generate_specific_recommendations(issue["law"], jurisdiction)
                else:
                    issue["recommendations"] = cleaned_recs
            
            validated_issues.append(issue)
        
        logger.info(f"Validated {len(validated_issues)} compliance issues")
        return validated_issues