import api from './api'

export const getAllRegulations = () =>
    api.get('v1/regulations');

export const getRegulationDetail = () =>
    api.get('regulations/{law_id}')

export const searchRegulations = () =>
    api.post('regulations/search')

export const getJurisdictions = () =>
    api.get('/regulations/jurisdictions/list')
