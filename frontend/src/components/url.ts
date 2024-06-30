export const BACKEND_URL = import.meta.env.PROD
    ? "https://heimdall-api.metakgp.org" // Will be changed later
    : "http://localhost:5000";