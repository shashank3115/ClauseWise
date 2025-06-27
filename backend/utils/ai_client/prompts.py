import json
from typing import Dict, Any, Optional


class PromptFormatter:
    """Handles prompt formatting and templating for different use cases"""
    SYSTEM_MESSAGES = {
        "default": "You are LegalGuard AI, an expert legal technology assistant. You analyze contracts and provide structured JSON responses.",
        
        "contract_analysis": """You are LegalGuard AI, a legal compliance expert.

Analyze contracts for compliance violations and missing requirements. 

You must return a complete JSON response with these three required keys:
1. summary - your overall assessment
2. flagged_clauses - array of problematic contract sections 
3. compliance_issues - array of missing requirements or violations

Return only the JSON object, nothing else.""",
        
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
        Build comprehensive contract analysis prompt.
        
        Args:
            contract_text: The contract text to analyze
            compliance_checklist: Compliance requirements to check against
            
        Returns:
            Formatted analysis prompt
        """
        checklist_str = json.dumps(compliance_checklist, indent=2)
        
        return f"""CONTRACT TEXT:
{contract_text}

COMPLIANCE REQUIREMENTS:
{checklist_str}

Analyze this contract for compliance issues. Look for missing clauses and problematic sections.

Return your analysis as JSON with three keys:
- summary: your brief assessment
- flagged_clauses: array of problematic sections (each with clause_text, issue, severity)
- compliance_issues: array of violations (each with law, missing_requirements, recommendations)"""
    
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
