import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { PublicClientApplication, EventType } from '@azure/msal-browser'
import { MsalProvider } from '@azure/msal-react'
import { msalConfig } from './authConfig'
import App from './App'
import './index.css'

// Create MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// Set active account on login success
msalInstance.addEventCallback((event) => {
  if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
    const payload = event.payload as { account: { username: string } };
    if (payload.account) {
      msalInstance.setActiveAccount(payload.account as Parameters<typeof msalInstance.setActiveAccount>[0]);
    }
  }
});

// Initialize MSAL and render
msalInstance.initialize().then(() => {
  // Handle redirect promise for redirect flow (if used)
  msalInstance.handleRedirectPromise().then(() => {
    // Set active account if available
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
    }

    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <MsalProvider instance={msalInstance}>
          <App />
        </MsalProvider>
      </StrictMode>,
    );
  });
});

