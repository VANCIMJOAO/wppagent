/**
 * Compatibility wrapper for api-client
 * Points to robust version to prevent build errors
 */

import apiService from './api-service-robust';

export const apiClient = apiService;
export default apiClient;
