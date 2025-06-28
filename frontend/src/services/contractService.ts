import api from './root'

// Analyze Single Contract
export const analyzeContract = (formData: FormData) =>
    api.post('/contracts/analyze', formData);

// Analyze Contract File
export const analyzeContractFile = (formData: FormData) =>
    api.post('/contracts/analyze/file', formData);

// Analyze Bulk Contracts
export const analyzeBulkContract = (formData: FormData) =>
    api.post('/contracts/analyze/bulk', formData);

// Calculate Risk Score
export const riskScore = (formData: FormData) =>
    api.post('/contracts/risk-score', formData);

// Extract Text from Contract File
export const extractText = (formData: FormData) =>
    api.post('/contracts/extract-text', formData);

// Get Supported Jurisdictions
export const getSupportedJurisdictions = () =>
    api.get('/contracts/supported-jurisdictions');

// Health Check
export const healthCheck = () =>
    api.get('/contracts/health');