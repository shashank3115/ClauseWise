import json
from typing import Dict, Any, Optional


class PromptFormatter:
    """Handles prompt formatting and templating for different use cases"""
    SYSTEM_MESSAGES = {
        "default": "You are LegalGuard AI, an expert legal technology assistant. You analyze contracts and provide structured JSON responses.",
        
        "contract_analysis": """You are LegalGuard AI, an expert legal compliance analyzer with deep expertise in GDPR, PDPA, employment law, and contract compliance.

ANALYSIS REQUIREMENTS:
You must perform a thorough legal compliance analysis and identify ALL significant issues, violations, and risks in the provided contract.

CRITICAL FOCUS AREAS:
1. GDPR/PDPA Data Protection Violations:
   - Missing data subject consent mechanisms
   - Inadequate cross-border data transfer safeguards
   - Excessive or indefinite data retention periods
   - Missing data subject rights (access, erasure, portability)
   - Insufficient data breach notification procedures
   - Missing Data Protection Officer requirements
   - Inadequate security measures and certifications

2. Employment Law Violations:
   - Insufficient termination notice periods
   - Missing overtime compensation provisions
   - Inadequate working time protections
   - Non-compliant salary and benefits structures

3. Contract Law Issues:
   - Inadequate liability caps that don't cover potential GDPR fines
   - Unfair indemnification clauses
   - Unilateral contract modification rights
   - Missing or weak security audit requirements
   - Problematic governing law and jurisdiction clauses

ANALYSIS APPROACH:
- Examine every clause for potential legal violations
- Identify specific text that violates regulations
- Assess severity based on potential financial and legal impact
- Provide actionable legal recommendations
- Focus on real business risks and compliance gaps

OUTPUT REQUIREMENTS:
You MUST return a complete JSON response with exactly these fields:
- "summary": Detailed assessment of all compliance risks found
- "flagged_clauses": Array of problematic clauses with exact text, specific legal issues, and severity ratings
- "compliance_issues": Array of regulatory violations with specific laws, missing requirements, and recommendations

Be comprehensive and identify ALL significant legal issues. Do not provide generic responses.""",
        
        "metadata_extraction": "You are a legal document analyzer. Extract metadata from contracts and return structured JSON.",
        
        "compliance_summary": "You are a legal compliance consultant creating executive summaries."
    }
    
    @staticmethod
    def format_for_granite(prompt: str, system_message: Optional[str] = None) -> str:
        """
        Format prompt specifically for IBM Granite models.
        
        Args:
            prompt: The main prompt text
            system_message: Optional system message, uses default if not provided
            
        Returns:
            Formatted prompt string for Granite models
        """
        if system_message is None:
            system_message = PromptFormatter.SYSTEM_MESSAGES["default"]
        
        # Granite models work better with a simpler format and explicit completion instruction
        return f"""{system_message}

{prompt}

Complete JSON response:"""
    
    @staticmethod
    def build_contract_analysis_prompt(contract_text: str, compliance_checklist: Dict[str, Any]) -> str:
        """
        Build comprehensive contract analysis prompt optimized for IBM Granite models.
        
        Args:
            contract_text: The contract text to analyze
            compliance_checklist: Compliance requirements to check against
            
        Returns:
            Formatted analysis prompt
        """
        checklist_str = json.dumps(compliance_checklist, indent=2)
        
        return f"""URGENT LEGAL COMPLIANCE ANALYSIS

CONTRACT TEXT TO ANALYZE:
{contract_text}

APPLICABLE LEGAL REQUIREMENTS:
{checklist_str}

DETAILED ANALYSIS INSTRUCTIONS:

1. MANDATORY GDPR/PDPA COMPLIANCE CHECK:
   - Scan for data processing activities without proper consent
   - Identify cross-border data transfers lacking adequate safeguards
   - Flag excessive data retention periods (look for "indefinite", "unlimited", or periods over 2 years)
   - Check for missing data subject rights (access, erasure, portability, rectification)
   - Verify data breach notification requirements (must be within 72 hours)
   - Ensure Data Protection Officer (DPO) requirements are addressed
   - Validate security measures and audit requirements

2. EMPLOYMENT LAW COMPLIANCE CHECK:
   - Verify termination notice periods meet minimum statutory requirements
   - Check overtime compensation and working time provisions
   - Validate salary, benefits, and compensation structures
   - Review workplace rights and protections

3. CONTRACT RISK ASSESSMENT:
   - Analyze liability limitations (flag caps under €1M for GDPR compliance)
   - Review indemnification clauses for unfair risk allocation
   - Check for unilateral modification rights without proper consent
   - Assess governing law and jurisdiction clauses

CRITICAL OUTPUT REQUIREMENTS:
Return ONLY valid JSON in this exact format (no additional text):

{{
  "summary": "Comprehensive assessment detailing all compliance risks, violations found, and overall legal exposure",
  "flagged_clauses": [
    {{
      "clause_text": "Exact problematic text from contract",
      "issue": "Specific legal violation or compliance issue with law reference",
      "severity": "high"
    }}
  ],
  "compliance_issues": [
    {{
      "law": "SPECIFIC_LAW_ID",
      "missing_requirements": ["Detailed list of missing legal requirements"],
      "recommendations": ["Specific actionable legal recommendations"]
    }}
  ]
}}

IMPORTANT: Analyze the actual contract text thoroughly. Identify real issues, not generic problems. Be specific about violations and provide actionable recommendations.

Analyze thoroughly and identify ALL significant compliance gaps."""
    
    @staticmethod
    def build_metadata_extraction_prompt(contract_text: str) -> str:
        """
        Build metadata extraction prompt.
        
        Args:
            contract_text: The contract text to analyze
            
        Returns:
            Formatted metadata extraction prompt
        """
        return f"""Analyze this contract and extract key metadata.

CONTRACT TEXT:
{contract_text}

Return a JSON object with this structure:
{{
  "contract_type": "employment|service|nda|partnership|other",
  "parties": ["list of contracting parties"],
  "jurisdiction": "detected jurisdiction code (MY/SG/EU/US)",
  "key_dates": ["important dates mentioned"],
  "contract_value": "monetary value if mentioned",
  "duration": "contract duration if specified"
}}

JSON response only:"""
    
    @staticmethod
    def build_compliance_summary_prompt(analysis_results: Dict[str, Any]) -> str:
        """
        Build compliance summary generation prompt.
        
        Args:
            analysis_results: Results from previous analysis
            
        Returns:
            Formatted summary prompt
        """
        return f"""Create an executive summary of this compliance analysis.

ANALYSIS RESULTS:
{json.dumps(analysis_results, indent=2)}

Return a JSON object with:
{{
  "executive_summary": "2-3 sentence overview for executives",
  "key_risks": ["top 3 compliance risks"],
  "immediate_actions": ["urgent actions needed"],
  "compliance_score": "percentage score out of 100"
}}

JSON response only:"""


class PromptTemplates:
    """Pre-defined prompt templates for common operations"""
    
    CONTRACT_ANALYSIS = {
        "system": "contract_analysis",
        "builder": PromptFormatter.build_contract_analysis_prompt
    }
    
    METADATA_EXTRACTION = {
        "system": "metadata_extraction", 
        "builder": PromptFormatter.build_metadata_extraction_prompt
    }
    
    COMPLIANCE_SUMMARY = {
        "system": "compliance_summary",
        "builder": PromptFormatter.build_compliance_summary_prompt
    }
