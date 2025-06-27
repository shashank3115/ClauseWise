"""
WatsonX AI Client Package

A modular and clean implementation of IBM WatsonX AI client for legal document analysis.
Provides contract analysis, metadata extraction, and compliance checking capabilities.
"""

from .config import ModelType, WatsonXConfig
from .client import WatsonXClient
from .exceptions import WatsonXError, AuthenticationError, APIError, ConfigurationError, ResponseParsingError

__all__ = [
    'ModelType',
    'WatsonXConfig', 
    'WatsonXClient',
    'WatsonXError',
    'AuthenticationError',
    'APIError',
    'ConfigurationError',
    'ResponseParsingError'
]

__version__ = "1.0.0"
