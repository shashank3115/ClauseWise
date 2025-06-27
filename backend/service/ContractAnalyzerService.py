import asyncio
import json
import logging
from typing import List, Dict, Optional
from backend.models.ContractAnalysisModel import ContractAnalysisRequest
from backend.models.ContractAnalysisResponseModel import ContractAnalysisResponse, ClauseFlag, ComplianceFeedback
from backend.models.ComplianceRiskScore import ComplianceRiskScore
from backend.utils.law_loader import LawLoader
from backend.service.RegulatoryEngineService import RegulatoryEngineService

logger = logging.getLogger(__name__)

class ContractAnalyzerService:
    def __init__(self):
        self.law_loader = LawLoader()
        self.regulatory_engine = RegulatoryEngineService()
        self.watsonx_client = None  # Initialize IBM watsonx.ai client here
        
    async def analyze_contract(self, request: ContractAnalysisRequest) -> ContractAnalysisResponse:
        """Main contract analysis orchestrator"""
        try:
            # 1. Extract and preprocess contract text
            processed_text = await self._preprocess_contract(request.text)
            
            # 2. Identify key clauses using IBM Granite models
            key_clauses = await self._extract_key_clauses(processed_text)
            
            # 3. Analyze compliance against jurisdiction laws
            compliance_issues = await self._analyze_compliance(
                key_clauses, request.jurisdiction or "MY"
            )
            
            # 4. Flag problematic clauses
            flagged_clauses = await self._flag_problematic_clauses(
                key_clauses, compliance_issues
            )
            
            # 5. Generate summary
            summary = await self._generate_contract_summary(
                processed_text, compliance_issues, flagged_clauses
            )
            
            return ContractAnalysisResponse(
                summary=summary,
                flagged_clauses=flagged_clauses,
                compliance_issues=compliance_issues,
                jurisdiction=request.jurisdiction or "MY"
            )
            
        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}")
            raise
    
    async def calculate_risk_score(self, analysis_response: ContractAnalysisResponse) -> ComplianceRiskScore:
        """Calculate comprehensive risk scoring"""
        violation_categories = []
        jurisdiction_risks = {}
        financial_risk = 0.0
        
        # Analyze compliance issues for risk scoring
        for issue in analysis_response.compliance_issues or []:
            violation_categories.append(issue.law)
            
            # Calculate financial risk based on law type and severity
            law_risk = self._calculate_law_risk(issue.law, len(issue.missing_requirements))
            financial_risk += law_risk
            
            # Track jurisdiction-specific risks
            jurisdiction = analysis_response.jurisdiction or "MY"
            if jurisdiction not in jurisdiction_risks:
                jurisdiction_risks[jurisdiction] = 0
            jurisdiction_risks[jurisdiction] += int(law_risk / 1000)  # Convert to score
        
        # Factor in flagged clauses severity
        severity_multiplier = self._calculate_severity_multiplier(analysis_response.flagged_clauses)
        financial_risk *= severity_multiplier
        
        # Calculate overall score (inverse of risk - higher risk = lower score)
        overall_score = max(0, 100 - int(financial_risk / 10000))
        
        return ComplianceRiskScore(
            overall_score=overall_score,
            financial_risk_estimate=financial_risk,
            violation_categories=list(set(violation_categories)),
            jurisdiction_risks=jurisdiction_risks
        )
    
    async def _preprocess_contract(self, text: str) -> str:
        # Remove extra whitespace, normalize formatting
        cleaned_text = " ".join(text.split())
        
        # TODO: Add more sophisticated preprocessing
        # - Remove headers/footers
        # - Normalize legal terminology
        # - Handle multi-language content
        
        return cleaned_text
    
    async def _extract_key_clauses(self, text: str) -> Dict[str, str]:
        # This would integrate with IBM watsonx.ai Granite models
        # For now, using rule-based extraction as placeholder
        
        clauses = {}
        text_lower = text.lower()
        
        # Data protection clauses
        if "personal data" in text_lower or "confidential" in text_lower:
            start_idx = text_lower.find("personal data")
            if start_idx == -1:
                start_idx = text_lower.find("confidential")
            clauses["data_protection"] = text[start_idx:start_idx + 200] + "..."
        
        # Termination clauses
        if "terminate" in text_lower or "termination" in text_lower:
            start_idx = text_lower.find("terminat")
            clauses["termination"] = text[start_idx:start_idx + 200] + "..."
        
        # Liability clauses
        if "liability" in text_lower or "liable" in text_lower:
            start_idx = text_lower.find("liabil")
            clauses["liability"] = text[start_idx:start_idx + 200] + "..."
        
        # Employment-specific clauses
        if "working hours" in text_lower or "overtime" in text_lower:
            start_idx = text_lower.find("working hours")
            if start_idx == -1:
                start_idx = text_lower.find("overtime")
            clauses["working_hours"] = text[start_idx:start_idx + 200] + "..."
        
        return clauses
    
    async def _analyze_compliance(self, clauses: Dict[str, str], jurisdiction: str) -> List[ComplianceFeedback]:
        compliance_issues = []
        
        # Load applicable laws for jurisdiction
        applicable_laws = await self.law_loader.get_laws_for_jurisdiction(jurisdiction)
        
        for law_code, law_data in applicable_laws.items():
            missing_requirements = []
            recommendations = []
            
            # Check data protection compliance
            if law_code in ["PDPA", "GDPR"] and "data_protection" in clauses:
                missing_reqs, recs = await self._check_data_protection_compliance(
                    clauses["data_protection"], law_data
                )
                missing_requirements.extend(missing_reqs)
                recommendations.extend(recs)
            
            # Check employment law compliance
            if law_code == "EMPLOYMENT_ACT_MY" and "working_hours" in clauses:
                missing_reqs, recs = await self._check_employment_compliance(
                    clauses["working_hours"], law_data
                )
                missing_requirements.extend(missing_reqs)
                recommendations.extend(recs)
            
            # Add compliance feedback if issues found
            if missing_requirements:
                compliance_issues.append(ComplianceFeedback(
                    law=law_data.get("name", law_code),
                    missing_requirements=missing_requirements,
                    recommendations=recommendations
                ))
        
        return compliance_issues
    
    async def _check_data_protection_compliance(self, clause: str, law_data: Dict) -> tuple:
        missing_requirements = []
        recommendations = []
        
        clause_lower = clause.lower()
        
        # Check for lawful basis (GDPR/PDPA requirement)
        if "lawful basis" not in clause_lower and "legal basis" not in clause_lower:
            missing_requirements.append("No clear lawful basis for data processing")
            recommendations.append("Add explicit lawful basis under Article 6 GDPR/Section 6 PDPA")
        
        # Check for data retention periods
        if "retain" not in clause_lower and "delete" not in clause_lower:
            missing_requirements.append("No data retention period specified")
            recommendations.append("Define clear data retention and deletion timelines")
        
        # Check for international transfer provisions
        if "transfer" in clause_lower and "adequacy" not in clause_lower:
            missing_requirements.append("International data transfer lacks adequacy safeguards")
            recommendations.append("Add adequacy decision or appropriate safeguards for data transfers")
        
        return missing_requirements, recommendations
    
    async def _check_employment_compliance(self, clause: str, law_data: Dict) -> tuple:
        missing_requirements = []
        recommendations = []
        
        clause_lower = clause.lower()
        
        # Check working hours (Malaysia Employment Act - max 48 hours/week)
        if "48 hours" not in clause_lower and "working hours" in clause_lower:
            missing_requirements.append("Working hours may exceed Malaysia Employment Act limits")
            recommendations.append("Ensure compliance with 48-hour weekly limit under Employment Act 1955")
        
        # Check overtime provisions
        if "overtime" in clause_lower and "1.5" not in clause_lower:
            missing_requirements.append("Overtime rate may not comply with statutory requirements")
            recommendations.append("Set overtime rate at minimum 1.5x normal rate as per Employment Act")
        
        return missing_requirements, recommendations
    
    async def _flag_problematic_clauses(self, clauses: Dict[str, str], 
                                      compliance_issues: List[ComplianceFeedback]) -> List[ClauseFlag]:
        flagged_clauses = []
        
        # Create severity mapping
        severity_map = {
            "GDPR": "high",
            "PDPA": "high", 
            "Employment Act": "medium",
            "Contract Act": "low"
        }
        
        for issue in compliance_issues:
            for clause_type, clause_text in clauses.items():
                # Determine severity based on law type
                severity = severity_map.get(issue.law, "medium")
                
                # Create flag for each missing requirement
                for missing_req in issue.missing_requirements:
                    flagged_clauses.append(ClauseFlag(
                        clause_text=clause_text[:100] + "..." if len(clause_text) > 100 else clause_text,
                        issue=f"{issue.law}: {missing_req}",
                        severity=severity
                    ))
        
        return flagged_clauses
    
    async def _generate_contract_summary(self, text: str, compliance_issues: List[ComplianceFeedback], 
                                       flagged_clauses: List[ClauseFlag]) -> str:
        issue_count = len(compliance_issues)
        high_severity_count = len([c for c in flagged_clauses if c.severity == "high"])
        
        if issue_count == 0:
            return "Contract appears compliant with analyzed jurisdictional requirements. No major compliance issues identified."
        
        risk_level = "HIGH" if high_severity_count > 0 else "MEDIUM" if issue_count > 2 else "LOW"
        
        summary = f"RISK LEVEL: {risk_level}\n\n"
        summary += f"Found {issue_count} compliance issue(s) across {len(set([i.law for i in compliance_issues]))} regulatory framework(s). "
        
        if high_severity_count > 0:
            summary += f"{high_severity_count} high-severity violation(s) require immediate attention. "
        
        summary += "Review flagged clauses and implement recommended changes before contract execution."
        
        return summary
    
    def _calculate_law_risk(self, law_name: str, violation_count: int) -> float:
        # Risk multipliers based on typical penalty structures
        risk_multipliers = {
            "GDPR": 50000,  # Up to €20M or 4% revenue
            "PDPA": 25000,  # Up to RM500K
            "Employment Act": 5000,  # Compensation claims
            "Contract Act": 1000   # Breach damages
        }
        
        base_risk = risk_multipliers.get(law_name, 2000)
        return base_risk * violation_count
    
    def _calculate_severity_multiplier(self, flagged_clauses: List[ClauseFlag]) -> float:
        high_count = len([c for c in flagged_clauses if c.severity == "high"])
        medium_count = len([c for c in flagged_clauses if c.severity == "medium"])
        
        return 1.0 + (high_count * 0.5) + (medium_count * 0.2)