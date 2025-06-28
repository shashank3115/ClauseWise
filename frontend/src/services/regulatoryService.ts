import api from './root'

export const getAllRegulations = () =>
    api.post('api/v1/regulations');

export const getRegulationDetail = () =>
    api.post('api/regulations/{law_id}')

export const searchRegulations = () =>
    api.post('api/regulations/search')

export const getJurisdictions = () =>
    api.post('api/regulations/jurisdictions/list')
