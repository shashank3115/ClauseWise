import api from './api'

// Analyze Single Contract
export const analyzeContract = (formData: FormData) =>
    api.post('/api/v1//contracts/analyze', formData);

// Analyze Contract File
export const analyzeContractFile = (formData: FormData) =>
    api.post('/api/v1/contracts/analyze/file', formData);

// Analyze Bulk Contracts
export const analyzeBulkContract = (formData: FormData) =>
    api.post('/api/v1//contracts/analyze/bulk', formData);

// Calculate Risk Score
export const riskScore = (formData: FormData) =>
    api.post('/api/v1//contracts/risk-score', formData);

// Extract Text from Contract File
export const extractText = (formData: FormData) =>
    api.post('/api/v1//contracts/extract-text', formData);

// Get Supported Jurisdictions
export const getSupportedJurisdictions = () =>
    api.get('/api/v1//contracts/supported-jurisdictions');

// Health Check
export const healthCheck = () =>
    api.get('/api/v1//contracts/health');