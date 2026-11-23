const API_PREFIX = '/api/v1';

const apiBaseUrl: string =
  import.meta.env.VITE_API_BASE_URL ?? `http://localhost:8000${API_PREFIX}`;

export const env = {
  apiBaseUrl,
  // The generated paths already include /api/v1, so openapi-fetch needs only the origin.
  apiOrigin: apiBaseUrl.endsWith(API_PREFIX) ? apiBaseUrl.slice(0, -API_PREFIX.length) : apiBaseUrl,
  slowRequestMs: 5000,
} as const;
