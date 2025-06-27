from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.models import (
    ContractAnalysisRequest, 
    ContractAnalysisResponse,
    ComplianceRiskScore,
    RegulatoryAlert,
    ContractSummary,
    ComplianceReport,
    AnalysisHistory,
    JurisdictionInfo,
    ContractTemplate,
    BulkAnalysisRequest,
    BulkAnalysisResponse
)

router = APIRouter(prefix="/api/contract", tags=["Contract"])

