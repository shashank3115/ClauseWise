import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LawLoader:
    def __init__(self, laws_directory: str = "backend/data/laws"):
        self.laws_directory = Path(laws_directory)
        self._law_cache = {}
        self._jurisdiction_mapping = {
            "MY": ["PDPA", "EMPLOYMENT_ACT_MY", "CONTRACT_ACT_MY", "COMPANIES_ACT_MY"],
            "SG": ["PDPA_SG", "EMPLOYMENT_ACT_SG", "CONTRACT_ACT_SG"],
            "EU": ["GDPR", "DIGITAL_SERVICES_ACT", "AI_ACT"],
            "US": ["CCPA", "CPRA", "FEDERAL_TRADE_COMMISSION_ACT"],
            "UK": ["UK_GDPR", "DATA_PROTECTION_ACT", "EMPLOYMENT_RIGHTS_ACT"],
            "GLOBAL": ["UN_GLOBAL_COMPACT", "ISO_27001", "SOC2"]
        }
        self._initialize_law_database()
    
    def _initialize_law_database(self):
        """Initialize the law database with regulatory frameworks"""
        self._law_cache = {
            # Malaysia Laws
            "PDPA": {
                "name": "Personal Data Protection Act 2010 (Malaysia)",
                "jurisdiction": "MY",
                "type": "data_protection",
                "applicable_contracts": ["data_processing", "employment", "nda", "service_agreement"],
                "key_provisions": {
                    "consent": "Section 6 - Processing must be based on valid consent",
                    "purpose_limitation": "Section 6 - Data must be processed for specified purposes only",
                    "data_retention": "Section 9 - Data must not be kept longer than necessary",
                    "cross_border": "Section 129 - Restrictions on transfer outside Malaysia",
                    "security": "Section 7 - Adequate security measures required",
                    "breach_notification": "Section 15A - Mandatory breach notification"
                },
                "penalties": {
                    "individual": "Up to RM500,000 fine or 3 years imprisonment",
                    "corporate": "Up to RM500,000 fine"
                },
                "recent_updates": [
                    "2022 Amendment - Enhanced cross-border transfer restrictions",
                    "2023 Guidelines - AI and automated decision-making"
                ]
            },
            
            "EMPLOYMENT_ACT_MY": {
                "name": "Employment Act 1955 (Malaysia)",
                "jurisdiction": "MY", 
                "type": "employment",
                "applicable_contracts": ["employment"],
                "key_provisions": {
                    "working_hours": "Section 60A - Maximum 48 hours per week",
                    "overtime": "Section 60A - Minimum 1.5x rate for overtime",
                    "annual_leave": "Section 60E - Minimum 8 days annual leave",
                    "termination": "First Schedule - Notice periods based on service length",
                    "maternity": "Section 37 - 98 days maternity leave",
                    "minimum_wage": "Minimum wage as per government orders"
                },
                "penalties": {
                    "individual": "Fine up to RM10,000",
                    "corporate": "Compensation and statutory penalties"
                }
            },
            
            # European Union Laws
            "GDPR": {
                "name": "General Data Protection Regulation (EU)",
                "jurisdiction": "EU",
                "type": "data_protection",
                "applicable_contracts": ["data_processing", "employment", "nda", "service_agreement"],
                "key_provisions": {
                    "lawful_basis": "Article 6 - Six lawful bases for processing",
                    "consent": "Article 7 - Conditions for consent",
                    "data_subject_rights": "Articles 15-22 - Individual rights",
                    "international_transfers": "Chapter V - Transfers to third countries",
                    "data_protection_officer": "Articles 37-39 - DPO requirements",
                    "privacy_by_design": "Article 25 - Data protection by design and default",
                    "breach_notification": "Articles 33-34 - Breach notification requirements"
                },
                "penalties": {
                    "administrative_fines": "Up to €20 million or 4% of annual global turnover",
                    "corrective_measures": "Processing bans, data erasure orders"
                },
                "recent_updates": [
                    "2024 Guidelines on AI and automated decision-making",
                    "2023 Adequacy decisions updates",
                    "2024 Guidelines on consent in digital services"
                ]
            },
            
            # United States Laws
            "CCPA": {
                "name": "California Consumer Privacy Act",
                "jurisdiction": "US",
                "type": "data_protection",
                "applicable_contracts": ["data_processing", "service_agreement", "nda"],
                "key_provisions": {
                    "consumer_rights": "Right to know, delete, opt-out, non-discrimination",
                    "business_obligations": "Privacy policy requirements and consumer request handling",
                    "third_party_sharing": "Disclosure requirements for data sharing",
                    "sensitive_information": "Additional protections for sensitive personal information"
                },
                "penalties": {
                    "civil_penalties": "Up to $7,500 per violation",
                    "private_right": "$100-$750 per consumer per incident"
                }
            },
            
            # Singapore Laws
            "PDPA_SG": {
                "name": "Personal Data Protection Act 2012 (Singapore)",
                "jurisdiction": "SG",
                "type": "data_protection", 
                "applicable_contracts": ["data_processing", "employment", "nda", "service_agreement"],
                "key_provisions": {
                    "consent": "Section 13 - Consent obligations",
                    "purpose_limitation": "Section 12 - Purpose limitation obligation",
                    "notification": "Section 20 - Notification of data breaches",
                    "transfer_limitation": "Section 26 - Transfer limitation obligation"
                },
                "penalties": {
                    "financial": "Up to S$1 million fine"
                }
            },
            
            # Contract Law Frameworks
            "CONTRACT_ACT_MY": {
                "name": "Contracts Act 1950 (Malaysia)",
                "jurisdiction": "MY",
                "type": "contract",
                "applicable_contracts": ["all"],
                "key_provisions": {
                    "formation": "Sections 2-9 - Contract formation requirements",
                    "consideration": "Sections 26-30 - Consideration requirements", 
                    "capacity": "Sections 11-12 - Capacity to contract",
                    "free_consent": "Sections 13-22 - Free consent requirements",
                    "void_agreements": "Sections 23-30 - Void agreements",
                    "performance": "Sections 37-67 - Performance obligations"
                }
            },
            
            # Industry Standards
            "ISO_27001": {
                "name": "ISO/IEC 27001 Information Security Management",
                "jurisdiction": "GLOBAL",
                "type": "information_security",
                "applicable_contracts": ["data_processing", "service_agreement", "nda"],
                "key_provisions": {
                    "isms": "Information Security Management System requirements",
                    "risk_assessment": "Risk assessment and treatment processes",
                    "controls": "Annex A security controls framework",
                    "continuous_improvement": "Plan-Do-Check-Act cycle"
                }
            }
        }
    
    async def get_laws_for_jurisdiction(self, jurisdiction: str) -> Dict:
        """Get all applicable laws for a specific jurisdiction"""
        try:
            applicable_law_codes = self._jurisdiction_mapping.get(jurisdiction.upper(), [])
            applicable_laws = {}
            
            for law_code in applicable_law_codes:
                if law_code in self._law_cache:
                    applicable_laws[law_code] = self._law_cache[law_code]
            
            # Always include global standards
            global_standards = self._jurisdiction_mapping.get("GLOBAL", [])
            for standard in global_standards:
                if standard in self._law_cache:
                    applicable_laws[standard] = self._law_cache[standard]
            
            return applicable_laws
            
        except Exception as e:
            logger.error(f"Failed to get laws for jurisdiction {jurisdiction}: {str(e)}")
            return {}
    
    async def get_law_details(self, law_code: str) -> Optional[Dict]:
        return self._law_cache.get(law_code)
    
    async def get_contract_applicable_laws(self, jurisdiction: str, contract_type: str) -> Dict:
        all_laws = await self.get_laws_for_jurisdiction(jurisdiction)
        applicable_laws = {}
        
        for law_code, law_data in all_laws.items():
            applicable_contracts = law_data.get("applicable_contracts", [])
            if contract_type in applicable_contracts or "all" in applicable_contracts:
                applicable_laws[law_code] = law_data
        
        return applicable_laws
    
    async def get_compliance_checklist(self, jurisdiction: str, contract_type: str) -> List[Dict]:
        applicable_laws = await self.get_contract_applicable_laws(jurisdiction, contract_type)
        checklist = []
        
        for law_code, law_data in applicable_laws.items():
            law_name = law_data.get("name", law_code)
            key_provisions = law_data.get("key_provisions", {})
            
            for provision_key, provision_desc in key_provisions.items():
                checklist.append({
                    "law": law_name,
                    "law_code": law_code,
                    "provision": provision_key,
                    "description": provision_desc,
                    "category": law_data.get("type", "general"),
                    "mandatory": self._is_provision_mandatory(law_code, provision_key),
                    "penalty_risk": self._get_penalty_risk(law_data, provision_key)
                })
        
        return checklist
    
    def _is_provision_mandatory(self, law_code: str, provision_key: str) -> bool:
        mandatory_provisions = {
            "PDPA": ["consent", "purpose_limitation", "cross_border", "breach_notification"],
            "GDPR": ["lawful_basis", "data_subject_rights", "international_transfers", "breach_notification"],
            "EMPLOYMENT_ACT_MY": ["working_hours", "overtime", "minimum_wage", "termination"],
            "CCPA": ["consumer_rights", "business_obligations"],
            "CONTRACT_ACT_MY": ["formation", "consideration", "capacity", "free_consent"]
        }
        
        return provision_key in mandatory_provisions.get(law_code, [])
    
    def _get_penalty_risk(self, law_data: Dict, provision_key: str) -> str:
        penalties = law_data.get("penalties", {})
        
        # High risk laws with significant financial penalties
        high_risk_laws = ["GDPR", "PDPA", "CCPA"]
        if any(law in str(law_data.get("name", "")) for law in high_risk_laws):
            return "high"
        
        # Employment laws typically have medium risk
        if law_data.get("type") == "employment":
            return "medium"
        
        # Contract law violations typically lower financial risk
        if law_data.get("type") == "contract":
            return "low"
        
        return "medium"
    
    async def search_provisions(self, search_term: str, jurisdiction: Optional[str] = None) -> List[Dict]:
        results = []
        search_term_lower = search_term.lower()
        
        laws_to_search = self._law_cache
        if jurisdiction:
            laws_to_search = await self.get_laws_for_jurisdiction(jurisdiction)
        
        for law_code, law_data in laws_to_search.items():
            law_name = law_data.get("name", law_code)
            key_provisions = law_data.get("key_provisions", {})
            
            for provision_key, provision_desc in key_provisions.items():
                if (search_term_lower in provision_key.lower() or 
                    search_term_lower in provision_desc.lower()):
                    results.append({
                        "law": law_name,
                        "law_code": law_code,
                        "jurisdiction": law_data.get("jurisdiction"),
                        "provision_key": provision_key,
                        "provision_description": provision_desc,
                        "relevance_score": self._calculate_relevance(search_term_lower, provision_key, provision_desc)
                    })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def _calculate_relevance(self, search_term: str, provision_key: str, provision_desc: str) -> float:
        score = 0.0
        
        # Exact match in provision key gets highest score
        if search_term == provision_key.lower():
            score += 10.0
        elif search_term in provision_key.lower():
            score += 5.0
        
        # Match in description
        if search_term in provision_desc.lower():
            score += 2.0
        
        # Partial word matches
        search_words = search_term.split()
        for word in search_words:
            if word in provision_key.lower():
                score += 1.0
            if word in provision_desc.lower():
                score += 0.5
        
        return score
    
    async def get_jurisdiction_summary(self, jurisdiction: str) -> Dict:
        laws = await self.get_laws_for_jurisdiction(jurisdiction)
        
        summary = {
            "jurisdiction": jurisdiction,
            "total_laws": len(laws),
            "law_types": {},
            "key_focus_areas": [],
            "compliance_complexity": "medium",
            "recent_changes": []
        }
        
        # Categorize laws by type
        for law_code, law_data in laws.items():
            law_type = law_data.get("type", "other")
            if law_type not in summary["law_types"]:
                summary["law_types"][law_type] = 0
            summary["law_types"][law_type] += 1
            
            # Collect recent updates
            recent_updates = law_data.get("recent_updates", [])
            summary["recent_changes"].extend(recent_updates)
        
        # Determine focus areas based on law types
        if "data_protection" in summary["law_types"]:
            summary["key_focus_areas"].append("Data Protection & Privacy")
        if "employment" in summary["law_types"]:
            summary["key_focus_areas"].append("Employment Rights")
        if "contract" in summary["law_types"]:
            summary["key_focus_areas"].append("Contract Law")
        
        # Assess complexity based on number and types of laws
        if len(laws) > 5 or "data_protection" in summary["law_types"]:
            summary["compliance_complexity"] = "high"
        elif len(laws) < 3:
            summary["compliance_complexity"] = "low"
        
        return summary