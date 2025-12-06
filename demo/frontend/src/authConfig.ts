import { Configuration, LogLevel } from "@azure/msal-browser";

// MSAL configuration
export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID || "",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID || "common"}`,
    redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI || window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage", // Use "localStorage" for SSO across browser tabs
    storeAuthStateInCookie: false, // Set to true for IE11 support or Safari private mode
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            break;
          case LogLevel.Warning:
            console.warn(message);
            break;
          case LogLevel.Info:
            console.info(message);
            break;
          case LogLevel.Verbose:
            console.debug(message);
            break;
        }
      },
      logLevel: LogLevel.Warning,
    },
  },
};

// Scopes for the access token
export const loginRequest = {
  scopes: [import.meta.env.VITE_ENTRA_API_SCOPE || "User.Read"],
};

// Scopes for API calls
export const apiRequest = {
  scopes: [import.meta.env.VITE_ENTRA_API_SCOPE || "User.Read"],
};
