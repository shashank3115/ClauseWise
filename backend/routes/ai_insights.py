"""
AI-powered insights and summaries for Legal Guard RegTech platform.

This module provides clean AI endpoints using IBM Granite for:
- Legal document summarization in plain language
- Quick risk assessment summaries  
- Contract clause explanations
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from utils.ai_client import WatsonXClient, WatsonXConfig
from utils.ai_client.exceptions import APIError, AuthenticationError

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/ai", tags=["ai-insights"])

# Pydantic models
class DocumentSummaryRequest(BaseModel):
    text: str = Field(..., min_length=100, description="Legal document text to summarize")
    summary_type: str = Field(default="plain_language", description="Type of summary: 'plain_language', 'executive', 'risks'")

class DocumentSummaryResponse(BaseModel):
    summary: str
    key_points: list[str]
    risk_level: str
    word_count_reduction: str

class ClauseExplanationRequest(BaseModel):
    clause_text: str = Field(..., min_length=10, description="Legal clause to explain")
    
class ClauseExplanationResponse(BaseModel):
    plain_english: str
    potential_risks: list[str]
    recommendations: list[str]


# Dependency injection
def get_ai_client() -> WatsonXClient:
    """Get configured AI client."""
    return WatsonXClient()


@router.post("/summarize", response_model=DocumentSummaryResponse)
async def summarize_document(
    request: DocumentSummaryRequest,
    ai_client: WatsonXClient = Depends(get_ai_client)
):
    """
    Generate AI-powered plain language summary of legal documents.
    
    Perfect for making complex legal text accessible to non-lawyers.
    """
    try:
        logger.info(f"Generating {request.summary_type} summary for document")
        
        # Create summary prompt based on type
        if request.summary_type == "plain_language":
            prompt = f"""
            Summarize this legal document in simple, clear language that anyone can understand:
            
            {request.text}
            
            Focus on:
            1. What this document is about
            2. Key obligations and rights
            3. Important deadlines or conditions
            4. Potential risks or concerns
            
            Use simple words and short sentences. Avoid legal jargon.
            """
        elif request.summary_type == "executive":
            prompt = f"""
            Create an executive summary of this legal document:
            
            {request.text}
            
            Include:
            - Business impact
            - Key financial implications  
            - Critical deadlines
            - Risk assessment
            """
        else:  # risks
            prompt = f"""
            Identify and explain the main risks in this legal document:
            
            {request.text}
            
            Focus on potential problems, liabilities, and areas of concern.
            """
        
        # Get AI response
        summary = ai_client._make_request(prompt)
        
        # Extract key points (simple parsing)
        key_points = []
        lines = summary.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*')) or any(char.isdigit() and '.' in line for char in line[:3]):
                key_points.append(line.lstrip('-•* ').split('.', 1)[-1].strip())
        
        # Simple risk assessment based on keywords
        risk_keywords = ['penalty', 'liability', 'breach', 'termination', 'damages', 'default']
        risk_count = sum(1 for keyword in risk_keywords if keyword.lower() in request.text.lower())
        
        if risk_count >= 3:
            risk_level = "High"
        elif risk_count >= 1:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Calculate word reduction
        original_words = len(request.text.split())
        summary_words = len(summary.split())
        reduction = f"{((original_words - summary_words) / original_words * 100):.0f}%"
        
        return DocumentSummaryResponse(
            summary=summary.strip(),
            key_points=key_points[:5],  # Top 5 points
            risk_level=risk_level,
            word_count_reduction=reduction
        )
        
    except (APIError, AuthenticationError) as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in document summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/explain-clause", response_model=ClauseExplanationResponse)
async def explain_clause(
    request: ClauseExplanationRequest,
    ai_client: WatsonXClient = Depends(get_ai_client)
):
    """
    Explain a specific legal clause in plain English with risk assessment.
    
    Great for understanding complex contract terms quickly.
    """
    try:
        logger.info("Explaining legal clause")
        
        prompt = f"""
        Explain this legal clause in simple, everyday language:
        
        "{request.clause_text}"
        
        Provide:
        1. What it means in plain English
        2. Potential risks or problems
        3. Practical recommendations
        
        Be clear and concise. Avoid legal jargon.
        """
        
        explanation = ai_client._make_request(prompt)
        
        # Simple parsing for structured response
        lines = [line.strip() for line in explanation.split('\n') if line.strip()]
        
        plain_english = lines[0] if lines else explanation
        risks = [line for line in lines if any(word in line.lower() for word in ['risk', 'problem', 'concern', 'warning'])]
        recommendations = [line for line in lines if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'consider'])]
        
        return ClauseExplanationResponse(
            plain_english=plain_english,
            potential_risks=risks[:3],  # Top 3 risks
            recommendations=recommendations[:3]  # Top 3 recommendations
        )
        
    except (APIError, AuthenticationError) as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in clause explanation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Simple health check for AI services."""
    try:
        ai_client = get_ai_client()
        # Simple test prompt
        test_response = ai_client._make_request("Hello, this is a test. Respond with 'OK'.")
        return {"status": "healthy", "ai_service": "connected"}
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
