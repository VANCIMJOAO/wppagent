/**
 * Compatibility wrapper for api-client
 * Points to archived version to prevent build errors
 */

import { apiClient as archiveApiClient } from './archive/api-client';

export const apiClient = archiveApiClient;
export default apiClient;
