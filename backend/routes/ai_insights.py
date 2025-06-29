"""
AI-powered insights and summaries for Legal Guard RegTech platform.

This module provides clean AI endpoints using IBM Granite for:
- Legal document summarization in plain language
- Quick risk assessment summaries  
- Contract clause explanations
"""

import json
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
            Please analyze this legal document and provide a simple, easy-to-understand summary.
            
            Document:
            {request.text}
            
            First, identify what type of document this is (employment contract, service agreement, privacy policy, etc.).
            
            Then write a clear paragraph summary in plain English that explains:
            - What type of document this is and its main purpose
            - Who the parties are (if applicable)
            - The key terms and obligations
            - Important rights, payments, or deadlines
            - Any notable conditions or restrictions
            
            Write your response as normal text, like you would explain it to a friend. Be concise and focus on the most important points.
            """
        elif request.summary_type == "executive":
            prompt = f"""
            Write a business-focused executive summary of this legal document.
            
            Document:
            {request.text}
            
            Provide a concise executive summary that covers:
            - Business impact and implications of this agreement
            - Key financial terms, obligations, and commitments  
            - Critical deadlines, milestones, and deliverables
            - Main risks and areas of concern for the business
            - Key performance requirements or standards
            
            Write in a professional tone suitable for business executives and decision-makers.
            """
        else:  # risks
            prompt = f"""
            Analyze the main risks and potential problems in this legal document.
            
            Document:
            {request.text}
            
            Identify and explain the primary risks, including:
            - Legal and compliance risks
            - Financial exposure and liabilities
            - Operational risks and dependencies
            - Potential disputes or enforcement issues
            - Areas where terms may be unclear or problematic
            
            Focus on practical business risks and what could realistically go wrong. Be specific about the potential consequences.
            """
        
        # Get AI response
        summary = ai_client._make_text_request(prompt)
        
        # Handle case where AI returns JSON despite asking for plain text
        clean_summary = summary
        try:
            import json
            # Check if the response is JSON
            if summary.strip().startswith('{') and summary.strip().endswith('}'):
                parsed = json.loads(summary)
                
                # Try to extract meaningful summary text from various possible fields
                if 'summary' in parsed:
                    if isinstance(parsed['summary'], str):
                        clean_summary = parsed['summary']
                    elif isinstance(parsed['summary'], dict):
                        # If summary is a dict, extract first meaningful text
                        clean_summary = str(list(parsed['summary'].values())[0]) if parsed['summary'] else ""
                elif 'text' in parsed:
                    clean_summary = parsed['text']
                elif 'content' in parsed:
                    clean_summary = parsed['content']
                elif 'description' in parsed:
                    clean_summary = parsed['description']
                else:
                    # Extract the most descriptive field from the JSON
                    descriptive_fields = ['summary', 'text', 'content', 'description', 'explanation']
                    extracted_text = []
                    
                    for key, value in parsed.items():
                        if isinstance(value, str) and len(value) > 50:  # Meaningful text content
                            extracted_text.append(f"{key.replace('_', ' ').title()}: {value}")
                        elif isinstance(value, dict):
                            # If it's a nested dict, extract some meaningful content
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, str) and len(sub_value) > 30:
                                    extracted_text.append(f"{sub_key.replace('_', ' ').title()}: {sub_value}")
                                    break  # Just take the first meaningful one
                    
                    if extracted_text:
                        clean_summary = ". ".join(extracted_text[:3])  # Limit to first 3 meaningful items
                    else:
                        clean_summary = "This is a legal document with various terms and conditions that should be reviewed carefully."
                        
        except (json.JSONDecodeError, TypeError, KeyError):
            # If it's not valid JSON or processing fails, use as-is
            pass
        
        # Clean up the summary text
        if clean_summary:
            # Remove JSON-like formatting artifacts
            clean_summary = clean_summary.replace('\\n', ' ').replace('\\"', '"')
            # Ensure it's a proper sentence
            if not clean_summary.endswith('.'):
                clean_summary += '.'
        
        # Extract key points (improved parsing for better readability)
        key_points = []
        
        # Try to extract from original JSON structure if it exists
        try:
            if summary.strip().startswith('{'):
                parsed = json.loads(summary)
                
                # Look for structured key points in various fields
                points_sources = []
                
                # Check common fields that might contain key points
                for field in ['key_obligations', 'key_rights', 'key_points', 'main_points', 'important_items']:
                    if field in parsed and isinstance(parsed[field], (dict, list)):
                        if isinstance(parsed[field], dict):
                            points_sources.extend(list(parsed[field].keys())[:5])
                        else:
                            points_sources.extend(parsed[field][:5])
                
                # Clean up the points for frontend display
                for point in points_sources[:5]:
                    if isinstance(point, str):
                        # Clean up the text
                        clean_point = point.replace('\\n', ' ').replace('\\"', '"')
                        # Remove common prefixes and clean formatting
                        clean_point = clean_point.replace('": "', ': ').strip()
                        # Remove trailing quotes and colons
                        clean_point = clean_point.rstrip('",').strip()
                        
                        if len(clean_point) > 10:  # Only meaningful points
                            key_points.append(clean_point)
                            
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        
        # If no key points extracted from JSON, try extracting from the clean summary
        if not key_points:
            # First, try to find structured content
            lines = clean_summary.split('\n')
            for line in lines:
                line = line.strip()
                # Look for numbered items, bullet points, or lines with colons
                if (line.startswith(('-', '•', '*')) or 
                    any(char.isdigit() and '.' in line for char in line[:3]) or
                    ':' in line and len(line.split(':')) == 2):
                    
                    clean_line = line.lstrip('-•* 0123456789.').strip()
                    if len(clean_line) > 20:  # Meaningful content
                        key_points.append(clean_line)
            
            # If still no key points, extract from sentences in the summary
            if not key_points:
                sentences = clean_summary.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 30 and len(sentence) < 150:  # Good length for key points
                        # Look for sentences that mention key contract elements
                        key_indicators = [
                            'contract', 'agreement', 'parties', 'employer', 'employee', 
                            'duties', 'responsibilities', 'wages', 'termination', 'duration',
                            'rights', 'obligations', 'payment', 'benefits', 'terms'
                        ]
                        
                        if any(indicator in sentence.lower() for indicator in key_indicators):
                            # Clean up the sentence for display
                            clean_sentence = sentence.replace('The ', '').replace('This ', '')
                            if not clean_sentence.endswith('.'):
                                clean_sentence += '.'
                            key_points.append(clean_sentence)
                            
                            if len(key_points) >= 5:  # Limit to 5 key points
                                break  # Limit to 5 key points
                                break
            
            # Final fallback: create key points from main topics if still empty
            if not key_points:
                # Extract key topics from the original contract text
                contract_sections = []
                if 'duration' in request.text.lower():
                    contract_sections.append('Contract duration and employment period are specified')
                if 'duties' in request.text.lower() or 'responsibilities' in request.text.lower():
                    contract_sections.append('Employee and employer duties are clearly defined')
                if 'wage' in request.text.lower() or 'salary' in request.text.lower():
                    contract_sections.append('Compensation and payment terms are outlined')
                if 'termination' in request.text.lower():
                    contract_sections.append('Termination conditions and procedures are established')
                if 'benefits' in request.text.lower():
                    contract_sections.append('Employee benefits and entitlements are detailed')
                
                key_points = contract_sections[:5]
                        
            # Limit to 5 key points maximum
            key_points = key_points[:5]
        
        # Simple risk assessment based on keywords
        risk_keywords = ['penalty', 'liability', 'breach', 'termination', 'damages', 'default']
        risk_count = sum(1 for keyword in risk_keywords if keyword.lower() in request.text.lower())
        
        if risk_count >= 3:
            risk_level = "High"
        elif risk_count >= 1:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Calculate word reduction - fix negative percentages
        original_words = len(request.text.split())
        summary_words = len(clean_summary.split())
        
        if original_words > 0:
            if summary_words >= original_words:
                # If summary is longer than original, show as 0% reduction
                reduction = "0%"
            else:
                reduction_pct = ((original_words - summary_words) / original_words * 100)
                reduction = f"{reduction_pct:.0f}%"
        else:
            reduction = "0%"
        
        return DocumentSummaryResponse(
            summary=clean_summary.strip(),
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
        
        explanation = ai_client._make_text_request(prompt)
        
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
        test_response = ai_client._make_text_request("Hello, this is a test. Respond with 'OK'.")
        return {"status": "healthy", "ai_service": "connected"}
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
