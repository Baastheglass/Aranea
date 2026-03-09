// Backend API Configuration
// Automatically detect if running in Electron or web browser
const isElectron = typeof window !== 'undefined' && window.electron;

// Use localhost for Electron app, external URL for web deployment
export const BACKEND_URL = isElectron 
  ? 'http://localhost:8000'
  : (process.env.NEXT_PUBLIC_BACKEND_URL || 'https://c1ed-39-45-3-116.ngrok-free.app');

// WebSocket URL (derived from BACKEND_URL)
export const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws:/');

