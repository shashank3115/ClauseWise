import api from './api';

export const getAllRegulations = () => {
    return api.get('/regulations');
};

export const getRegulationDetail = (lawId: string) => {
    return api.get(`/regulations/${lawId}`);
};

export const searchRegulations = (formData: FormData) => {
    return api.post('/regulations/search', formData);
};

export const getJurisdictions = () => {
    return api.post('/api/regulations/jurisdictions/list');
};
