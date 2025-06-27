#!/usr/bin/env python3
"""
Example usage of the refactored WatsonX AI client.

This script demonstrates how to use the new modular WatsonX client
for legal document analysis tasks.
"""

import os
import json
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.ai_client import WatsonXClient, WatsonXConfig, ModelType
from backend.utils.ai_client.exceptions import ConfigurationError, AuthenticationError, APIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate the new WatsonX AI client usage"""
    
    print("🤖 WatsonX AI Client Demo - Refactored Version")
    print("=" * 50)
    
    # Example 1: Create configuration
    print("\n1. Configuration Setup")
    print("-" * 25)
    
    try:
        # Try to load from environment first
        try:
            config = WatsonXConfig.from_environment()
            print("✅ Configuration loaded from environment variables")
        except ConfigurationError:
            print("⚠️  Environment variables not set, using mock configuration")
            config = WatsonXConfig(
                api_key="mock_api_key_for_demo",
                project_id="mock_project_id_for_demo",
                model_id=ModelType.GRANITE_13B.value,
                temperature=0.1,
                max_tokens=1024
            )
        
        print(f"   Model: {config.model_id}")
        print(f"   Temperature: {config.temperature}")
        print(f"   Max Tokens: {config.max_tokens}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Example 2: Initialize client
    print("\n2. Client Initialization")
    print("-" * 25)
    
    try:
        client = WatsonXClient(config)
        print("✅ WatsonX client initialized successfully")
        
        # Note: Health check would require real credentials
        print("   (Health check skipped in demo mode)")
        
    except Exception as e:
        print(f"❌ Client initialization error: {e}")
        return
    
    # Example 3: Show available methods
    print("\n3. Available Client Methods")
    print("-" * 25)
    
    methods = [
        ("analyze_contract", "Analyze contract against compliance checklist"),
        ("extract_contract_metadata", "Extract contract type and key metadata"),
        ("generate_compliance_summary", "Generate executive summary"),
        ("health_check", "Verify client connectivity"),
        ("refresh_authentication", "Force token refresh")
    ]
    
    for method_name, description in methods:
        print(f"   📋 {method_name}(): {description}")
    
    # Example 4: Sample usage patterns
    print("\n4. Usage Examples")
    print("-" * 25)
    
    # Sample contract text
    sample_contract = """
    EMPLOYMENT AGREEMENT
    
    This Employment Agreement is entered into between TechCorp Ltd. and John Doe.
    
    1. POSITION: Employee shall serve as Software Engineer.
    2. COMPENSATION: Base salary of $75,000 per annum.
    3. CONFIDENTIALITY: Employee agrees to maintain confidentiality of company information.
    4. TERM: This agreement shall commence on January 1, 2024 and continue indefinitely.
    """
    
    # Sample compliance checklist
    sample_checklist = {
        "employment_laws": {
            "jurisdiction": "US",
            "requirements": [
                "Clear termination procedures",
                "Non-discrimination clauses",
                "Overtime compensation"
            ]
        }
    }
    
    print("   📄 Sample Contract Analysis:")
    print("      - Contract Type: Employment Agreement")
    print("      - Length: ~400 characters")
    print("      - Checklist: Employment law compliance")
    
    print("\n   💻 Code Example:")
    code_example = '''
# Using the new modular client
from backend.utils.ai_client import WatsonXClient, WatsonXConfig

# Load configuration
config = WatsonXConfig.from_environment()

# Initialize client  
client = WatsonXClient(config)

# Analyze contract
result = client.analyze_contract(contract_text, compliance_checklist)
analysis = json.loads(result)

# Extract metadata
metadata = client.extract_contract_metadata(contract_text)
contract_info = json.loads(metadata)

# Generate summary
summary = client.generate_compliance_summary(analysis)
executive_summary = json.loads(summary)
'''
    
    print(code_example)
    
    # Example 5: Error handling patterns
    print("\n5. Error Handling")
    print("-" * 25)
    
    error_examples = [
        ("ConfigurationError", "Invalid or missing configuration"),
        ("AuthenticationError", "IBM Cloud authentication failed"),
        ("APIError", "WatsonX API request failed"),
        ("ResponseParsingError", "Unable to parse AI response")
    ]
    
    for error_type, description in error_examples:
        print(f"   🚨 {error_type}: {description}")
    
    print("\n   💻 Error Handling Example:")
    error_code = '''
try:
    client = WatsonXClient()
    result = client.analyze_contract(text, checklist)
except ConfigurationError as e:
    logger.error(f"Configuration issue: {e}")
except AuthenticationError as e:
    logger.error(f"Authentication failed: {e}")
except APIError as e:
    logger.error(f"API error: {e}")
'''
    print(error_code)
    
    # Example 6: Migration guide
    print("\n6. Migration from Old Client")
    print("-" * 25)
    
    migration_guide = '''
# OLD (deprecated):
from backend.utils.watsonx_client import WatsonXClient, WatsonXConfig

# NEW (recommended):
from backend.utils.ai_client import WatsonXClient, WatsonXConfig
from backend.utils.ai_client.exceptions import ConfigurationError

# The API is mostly the same, but with better error handling
# and more modular internal structure.
'''
    print(migration_guide)
    
    print("\n✨ Demo completed! The refactored client is ready to use.")
    print("   📚 Check tests/test_ai_client.py for comprehensive test examples.")


if __name__ == "__main__":
    main()
