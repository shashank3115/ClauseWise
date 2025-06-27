import json
from typing import Dict, Any, Optional


class PromptFormatter:
    """Handles prompt formatting and templating for different use cases"""
    SYSTEM_MESSAGES = {
        "default": "You are LegalGuard AI, an expert legal technology assistant. You analyze contracts and provide structured JSON responses.",
        
        "contract_analysis": """You are LegalGuard AI, an expert legal compliance assistant. 

CRITICAL INSTRUCTIONS:
1. Analyze the contract text against the provided compliance checklist
2. Return ONLY a valid JSON object with no markdown formatting or additional text
3. The JSON must follow this exact structure:
{
  "summary": "Brief summary of compliance status",
  "flagged_clauses": [
    {
      "clause_text": "exact problematic text",
      "issue": "detailed explanation of the issue",
      "severity": "high|medium|low"
    }
  ],
  "compliance_issues": [
    {
      "law_id": "law identifier from checklist",
      "missing_requirements": ["list of missing requirements"],
      "recommendations": ["list of specific recommendations"]
    }
  ]
}""",
        
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
        
        return f"""<|system|>
{system_message}

<|user|>
{prompt}

<|assistant|>
"""
    
    @staticmethod
    def build_contract_analysis_prompt(contract_text: str, compliance_checklist: Dict[str, Any]) -> str:
        """
        Build comprehensive contract analysis prompt.
        
        Args:
            contract_text: The contract text to analyze
            compliance_checklist: Compliance requirements to check against
            
        Returns:
            Formatted analysis prompt
        """
        checklist_str = json.dumps(compliance_checklist, indent=2)
        
        return f"""Analyze this contract for legal compliance issues.

COMPLIANCE CHECKLIST (JSON format):
{checklist_str}

CONTRACT TEXT TO ANALYZE:
{contract_text}

Instructions:
1. Identify clauses that violate the requirements in the checklist
2. Find missing required clauses or provisions
3. Assess severity of each issue (high/medium/low)
4. Provide specific recommendations for compliance

Return your analysis as a JSON object only:"""
    
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
