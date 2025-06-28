import api from './api';

export const getAllRegulations = () => {
    return api.get('/regulations');
};

export const getRegulationDetail = (lawId: string) => {
    return api.get(`/regulations/${lawId}`);
};

export const searchRegulations = (payload: {
    keyword?: string;
    jurisdiction?: string;
    type?: string;
    page?: number;
}) => {
    return api.post('/regulations/search', payload);
};

export const getJurisdictions = () => {
    return api.post('/api/regulations/jurisdictions/list');
};
