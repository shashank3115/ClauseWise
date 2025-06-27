import asyncio
import logging
import io
import re
from typing import List, Dict, Optional, Union
from pathlib import Path
import PyPDF2
import docx
from backend.models.BulkAnalysisRequest import BulkAnalysisRequest
from backend.models.ContractAnalysisModel import ContractAnalysisRequest
from backend.models.ContractAnalysisResponseModel import ContractAnalysisResponse
from backend.service.ContractAnalyzerService import ContractAnalyzerService

logger = logging.getLogger(__name__)

class DocumentProcessorService:
    def __init__(self):
        self.contract_analyzer = ContractAnalyzerService()
        self.supported_formats = ['.pdf', '.docx', '.txt']
        self.max_file_size = 10 * 1024 * 1024 
        
    async def process_single_document(self, file_content: bytes, filename: str, 
                                    jurisdiction: str = "MY") -> ContractAnalysisResponse:
        try:
            # Validate file
            await self._validate_file(file_content, filename)
            
            # Extract text from document
            extracted_text = await self._extract_text_from_file(file_content, filename)
            
            # Clean and preprocess text
            cleaned_text = await self._clean_extracted_text(extracted_text)
            
            # Create analysis request
            analysis_request = ContractAnalysisRequest(
                text=cleaned_text,
                jurisdiction=jurisdiction
            )
            
            # Analyze contract
            return await self.contract_analyzer.analyze_contract(analysis_request)
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            raise
    
    async def process_bulk_documents(self, bulk_request: BulkAnalysisRequest) -> List[ContractAnalysisResponse]:
        results = []
        
        # Process based on priority
        if bulk_request.priority == "urgent":
            # Process all concurrently for urgent requests
            tasks = [
                self.contract_analyzer.analyze_contract(contract)
                for contract in bulk_request.contracts
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Process sequentially for normal priority to manage resources
            for contract in bulk_request.contracts:
                try:
                    result = await self.contract_analyzer.analyze_contract(contract)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process contract: {str(e)}")
                    # Continue processing other contracts
                    continue
        
        # Send notification email if provided
        if bulk_request.notification_email:
            await self._send_completion_notification(
                bulk_request.notification_email, 
                len(results), 
                len(bulk_request.contracts)
            )
        
        return [r for r in results if isinstance(r, ContractAnalysisResponse)]
    
    async def extract_contract_metadata(self, file_content: bytes, filename: str) -> Dict:
        try:
            text = await self._extract_text_from_file(file_content, filename)
            
            metadata = {
                'filename': filename,
                'file_size': len(file_content),
                'word_count': len(text.split()),
                'character_count': len(text),
                'detected_language': await self._detect_language(text),
                'contract_type': await self._detect_contract_type(text),
                'parties': await self._extract_parties(text),
                'dates': await self._extract_dates(text),
                'jurisdiction_hints': await self._detect_jurisdiction_hints(text)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {'filename': filename, 'error': str(e)}
    
    async def _validate_file(self, file_content: bytes, filename: str) -> None:
        # Check file size
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File size exceeds {self.max_file_size / (1024*1024)}MB limit")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format. Supported: {', '.join(self.supported_formats)}")
        
        # Basic file content validation
        if len(file_content) == 0:
            raise ValueError("File is empty")
    
    async def _extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        file_ext = Path(filename).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return await self._extract_from_pdf(file_content)
            elif file_ext == '.docx':
                return await self._extract_from_docx(file_content)
            elif file_ext == '.txt':
                return file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {str(e)}")
            raise
    
    async def _extract_from_pdf(self, file_content: bytes) -> str:
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise ValueError("Failed to extract text from PDF")
    
    async def _extract_from_docx(self, file_content: bytes) -> str:
        try:
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                text_content.append(paragraph.text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise ValueError("Failed to extract text from Word document")
    
    async def _clean_extracted_text(self, text: str) -> str:
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        cleaned = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned)
        cleaned = re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', cleaned, flags=re.IGNORECASE)
        
        # Remove excessive newlines
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        
        # Strip and normalize
        cleaned = cleaned.strip()
        
        return cleaned
    
    async def _detect_language(self, text: str) -> str:
        # Simple language detection based on common legal terms
        text_lower = text.lower()
        
        # English indicators
        english_terms = ['contract', 'agreement', 'whereas', 'party', 'clause', 'terms']
        english_count = sum(1 for term in english_terms if term in text_lower)
        
        # Malay indicators
        malay_terms = ['kontrak', 'perjanjian', 'pihak', 'terma', 'fasal']
        malay_count = sum(1 for term in malay_terms if term in text_lower)
        
        if malay_count > english_count:
            return 'ms'
        return 'en'
    
    async def _detect_contract_type(self, text: str) -> str:
        text_lower = text.lower()
        
        # NDA indicators
        if any(term in text_lower for term in ['non-disclosure', 'confidential', 'nda', 'secrecy']):
            return 'nda'
        
        # Employment contract indicators
        if any(term in text_lower for term in ['employment', 'employee', 'salary', 'working hours']):
            return 'employment'
        
        # Service agreement indicators
        if any(term in text_lower for term in ['service', 'vendor', 'supplier', 'delivery']):
            return 'service_agreement'
        
        # Data processing agreement indicators
        if any(term in text_lower for term in ['data processing', 'personal data', 'controller', 'processor']):
            return 'data_processing'
        
        return 'general'
    
    async def _extract_parties(self, text: str) -> List[str]:
        parties = []
        
        # Look for common party patterns
        party_patterns = [
            r'between\s+([A-Z][A-Za-z\s,\.]+?)(?:\s+and|\s+&)',
            r'Party\s+A[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\n|Party)',
            r'Party\s+B[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\n|Party)',
            r'"([A-Z][A-Za-z\s]+?)"(?:\s+\(|,\s+a)'
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            parties.extend([match.strip() for match in matches])
        
        # Remove duplicates and clean up
        unique_parties = []
        for party in parties:
            cleaned_party = party.strip(' .,')
            if cleaned_party and len(cleaned_party) > 3 and cleaned_party not in unique_parties:
                unique_parties.append(cleaned_party)
        
        return unique_parties[:5]  # Limit to 5 parties
    
    async def _extract_dates(self, text: str) -> List[str]:
        date_patterns = [
            r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',  # DD/MM/YYYY or MM/DD/YYYY
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))[:10]  
    
    async def _detect_jurisdiction_hints(self, text: str) -> List[str]:
        """Detect jurisdiction hints in the text"""
        jurisdiction_hints = []
        text_lower = text.lower()
        
        # Country/jurisdiction indicators
        jurisdiction_keywords = {
            'MY': ['malaysia', 'kuala lumpur', 'malaysian', 'ringgit', 'rm'],
            'SG': ['singapore', 'singaporean', 'sgd'],
            'US': ['united states', 'usa', 'american', 'usd', 'dollar'],
            'UK': ['united kingdom', 'british', 'gbp', 'pound sterling'],
            'EU': ['european union', 'gdpr', 'euro', 'eur']
        }
        
        for jurisdiction, keywords in jurisdiction_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                jurisdiction_hints.append(jurisdiction)
        
        return jurisdiction_hints
    
    async def _send_completion_notification(self, email: str, processed_count: int, total_count: int):
        # Placeholder for email notification logic
        logger.info(f"Bulk processing completed: {processed_count}/{total_count} contracts processed")
        logger.info(f"Notification should be sent to: {email}")
        
        # TODO: Implement actual email sending
        # This would integrate with your email service (SendGrid, AWS SES, etc.)
        pass