"""
Main WatsonX AI client implementation.
"""

import requests
import logging
from typing import Dict, Any, Optional

from .config import WatsonXConfig
from .auth import IBMCloudAuth
from .prompts import PromptFormatter, PromptTemplates
from .exceptions import APIError, ResponseParsingError, ConfigurationError

logger = logging.getLogger(__name__)


class WatsonXClient:
    """
    Enhanced WatsonX AI client for legal document analysis.
    
    Provides a clean, modular interface for interacting with IBM WatsonX AI services
    specifically tailored for legal document processing and compliance analysis.
    """
    
    def __init__(self, config: Optional[WatsonXConfig] = None):
        """
        Initialize the WatsonX client.
        
        Args:
            config: Optional configuration object. If not provided, 
                   will attempt to load from environment variables.
                   
        Raises:
            ConfigurationError: If configuration is invalid or incomplete
        """
        if config is None:
            config = WatsonXConfig.from_environment()
        
        config.validate()
        self.config = config
        self.auth = IBMCloudAuth(config.api_key)
        
        logger.info(f"WatsonX client initialized with model: {config.model_id}")
    
    def _make_request(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Make a request to the WatsonX API.
        
        Args:
            prompt: The formatted prompt to send
            system_message: Optional system message for context
            
        Returns:
            Generated text response from the model
            
        Raises:
            APIError: If the API request fails
            ResponseParsingError: If response cannot be parsed
        """
        try:
            token = self.auth.get_access_token()
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Format prompt for Granite models
        formatted_prompt = PromptFormatter.format_for_granite(prompt, system_message)
        
        body = {
            "project_id": self.config.project_id,
            "model_id": self.config.model_id,
            "parameters": {
                "temperature": self.config.temperature,
                "max_new_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "stop_sequences": ["</json>", "\n\n---"],
                "include_stop_sequence": False
            },
            "input": formatted_prompt
        }
        
        try:
            logger.debug(f"Making request to WatsonX API: {self.config.base_url}")
            response = requests.post(
                self.config.base_url,
                headers=headers,
                json=body,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "results" in result and len(result["results"]) > 0:
                generated_text = result["results"][0]["generated_text"]
                logger.debug(f"Successfully received response from WatsonX")
                return generated_text
            else:
                logger.error(f"Unexpected response format: {result}")
                raise ResponseParsingError("Invalid response format from WatsonX", str(result))
                
        except requests.exceptions.Timeout:
            raise APIError("Request to WatsonX API timed out", 408)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            response_data = {}
            try:
                response_data = e.response.json() if e.response else {}
            except:
                pass
            raise APIError(f"WatsonX API HTTP error: {e}", status_code, response_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"WatsonX API request failed: {e}")
            raise APIError(f"WatsonX API request failed: {e}")
    
    def analyze_contract(self, contract_text: str, compliance_checklist: Dict[str, Any]) -> str:
        """
        Analyze a contract against a compliance checklist.
        
        Args:
            contract_text: The contract text to analyze
            compliance_checklist: Compliance requirements to check against
            
        Returns:
            JSON string containing analysis results
            
        Raises:
            APIError: If the API request fails
            ResponseParsingError: If response cannot be parsed
        """
        logger.info("Starting contract compliance analysis")
        
        template = PromptTemplates.CONTRACT_ANALYSIS
        prompt = template["builder"](contract_text, compliance_checklist)
        system_message = PromptFormatter.SYSTEM_MESSAGES[template["system"]]
        
        return self._make_request(prompt, system_message)
    
    def extract_contract_metadata(self, contract_text: str) -> str:
        """
        Extract key metadata from a contract.
        
        Args:
            contract_text: The contract text to analyze
            
        Returns:
            JSON string containing extracted metadata
            
        Raises:
            APIError: If the API request fails
            ResponseParsingError: If response cannot be parsed
        """
        logger.info("Starting contract metadata extraction")
        
        template = PromptTemplates.METADATA_EXTRACTION
        prompt = template["builder"](contract_text)
        system_message = PromptFormatter.SYSTEM_MESSAGES[template["system"]]
        
        return self._make_request(prompt, system_message)
    
    def generate_compliance_summary(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate an executive summary from compliance analysis results.
        
        Args:
            analysis_results: Results from previous compliance analysis
            
        Returns:
            JSON string containing executive summary
            
        Raises:
            APIError: If the API request fails
            ResponseParsingError: If response cannot be parsed
        """
        logger.info("Generating compliance executive summary")
        
        template = PromptTemplates.COMPLIANCE_SUMMARY
        prompt = template["builder"](analysis_results)
        system_message = PromptFormatter.SYSTEM_MESSAGES[template["system"]]
        
        return self._make_request(prompt, system_message)
    
    def refresh_authentication(self) -> None:
        """Force refresh of authentication token"""
        logger.info("Refreshing authentication token")
        self.auth.invalidate_token()
    
    def health_check(self) -> bool:
        """
        Perform a simple health check to verify the client is working.
        
        Returns:
            True if client can successfully authenticate and make a request
        """
        try:
            logger.info("Performing WatsonX client health check")
            # Simple test request
            test_prompt = "Return only the word 'healthy' as a JSON string."
            response = self._make_request(test_prompt)
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
