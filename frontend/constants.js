// Backend API Configuration
export const BACKEND_URL = 'https://c1ed-39-45-3-116.ngrok-free.app';

// WebSocket URL (derived from BACKEND_URL)
export const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
