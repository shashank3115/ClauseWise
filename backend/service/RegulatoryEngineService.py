import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LawLoader:
    def __init__(self, mappings_file: str = "data/general/mappings.json"):
        self.mappings_file = Path(mappings_file)
        self._law_cache = {}
        self._jurisdiction_mapping = {}
        self._contract_types = {}
        self._risk_levels = {}
        self._metadata = {}
        self._initialize_from_mappings()
    
    def _initialize_from_mappings(self):
        """Initialize the law database from mappings.json file"""
        try:
            if not self.mappings_file.exists():
                logger.error(f"Mappings file not found: {self.mappings_file}")
                self._initialize_fallback_data()
                return
            
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
            
            # Load data from mappings.json
            self._jurisdiction_mapping = mappings_data.get("jurisdiction_mapping", {})
            self._law_cache = mappings_data.get("laws", {})
            self._contract_types = mappings_data.get("contract_types", {})
            self._risk_levels = mappings_data.get("risk_levels", {})
            self._metadata = mappings_data.get("metadata", {})
            
            logger.info(f"Loaded {len(self._law_cache)} laws from {self.mappings_file}")
            
        except Exception as e:
            logger.error(f"Failed to load mappings from {self.mappings_file}: {str(e)}")
            self._initialize_fallback_data()
    
    def _initialize_fallback_data(self):
        """Initialize minimal fallback data if mappings.json cannot be loaded"""
        logger.warning("Using fallback data - some features may be limited")
        self._jurisdiction_mapping = {
            "MY": ["PDPA", "EMPLOYMENT_ACT_MY", "CONTRACT_ACT_MY"],
            "SG": ["PDPA_SG"],
            "EU": ["GDPR"],
            "US": ["CCPA"],
            "GLOBAL": ["ISO_27001"]
        }
        self._law_cache = {}
        self._contract_types = {}
        self._risk_levels = {
            "high": {"description": "High risk"},
            "medium": {"description": "Medium risk"},
            "low": {"description": "Low risk"}
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
        """Check if a provision is mandatory based on data from mappings.json"""
        law_data = self._law_cache.get(law_code, {})
        mandatory_provisions = law_data.get("mandatory_provisions", [])
        return provision_key in mandatory_provisions
    
    def _get_penalty_risk(self, law_data: Dict, provision_key: str) -> str:
        """Get penalty risk level from law data or use fallback logic"""
        # First check if penalty_risk is directly specified in the law data
        if "penalty_risk" in law_data:
            return law_data["penalty_risk"]
        
        # Fallback to type-based risk assessment
        law_type = law_data.get("type", "")
        if law_type == "data_protection":
            return "high"
        elif law_type == "employment":
            return "medium"
        elif law_type == "contract":
            return "low"
        elif law_type == "information_security":
            return "medium"
        
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
            "recent_changes": [],
            "high_risk_laws": [],
            "applicable_contract_types": set()
        }
        
        # Categorize laws by type and gather additional information
        for law_code, law_data in laws.items():
            law_type = law_data.get("type", "other")
            if law_type not in summary["law_types"]:
                summary["law_types"][law_type] = 0
            summary["law_types"][law_type] += 1
            
            # Collect recent updates
            recent_updates = law_data.get("recent_updates", [])
            summary["recent_changes"].extend(recent_updates)
            
            # Track high-risk laws
            penalty_risk = law_data.get("penalty_risk", "medium")
            if penalty_risk == "high":
                summary["high_risk_laws"].append({
                    "code": law_code,
                    "name": law_data.get("name", law_code),
                    "type": law_type
                })
            
            # Collect applicable contract types
            applicable_contracts = law_data.get("applicable_contracts", [])
            summary["applicable_contract_types"].update(applicable_contracts)
        
        # Convert set to list for JSON serialization
        summary["applicable_contract_types"] = list(summary["applicable_contract_types"])
        
        # Determine focus areas based on law types
        focus_area_mapping = {
            "data_protection": "Data Protection & Privacy",
            "employment": "Employment Rights",
            "contract": "Contract Law",
            "information_security": "Information Security",
            "financial": "Financial Compliance"
        }
        
        for law_type in summary["law_types"]:
            if law_type in focus_area_mapping:
                summary["key_focus_areas"].append(focus_area_mapping[law_type])
        
        # Assess complexity based on number, types, and risk levels of laws
        high_risk_count = len(summary["high_risk_laws"])
        total_laws = len(laws)
        
        if high_risk_count >= 2 or total_laws > 5:
            summary["compliance_complexity"] = "high"
        elif total_laws < 3 and high_risk_count == 0:
            summary["compliance_complexity"] = "low"
        else:
            summary["compliance_complexity"] = "medium"
        
        return summary
    
    async def get_contract_types(self) -> Dict:
        """Get all available contract types"""
        return self._contract_types
    
    async def get_risk_levels(self) -> Dict:
        """Get risk level definitions"""
        return self._risk_levels
    
    async def get_system_metadata(self) -> Dict:
        """Get system metadata"""
        return self._metadata
    
    async def get_contract_type_info(self, contract_type: str) -> Optional[Dict]:
        """Get information about a specific contract type"""
        return self._contract_types.get(contract_type)
    
    async def reload_mappings(self) -> bool:
        """Reload mappings from file - useful for updates without restart"""
        try:
            self._initialize_from_mappings()
            return True
        except Exception as e:
            logger.error(f"Failed to reload mappings: {str(e)}")
            return False