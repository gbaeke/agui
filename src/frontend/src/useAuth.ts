import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest, apiRequest } from "./authConfig";
import { InteractionStatus, InteractionRequiredAuthError } from "@azure/msal-browser";
import { useCallback, useEffect, useState } from "react";

// Check if auth should be disabled (for testing)
const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === "true";

// Hook to get access token for API calls
// Following Microsoft best practices: acquire token on-demand, handle InteractionRequiredAuthError specifically
export function useAccessToken() {
  const { instance, accounts, inProgress } = useMsal();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isAcquiringToken, setIsAcquiringToken] = useState(false);

  const acquireToken = useCallback(async () => {
    if (accounts.length === 0 || inProgress !== InteractionStatus.None) {
      return null;
    }

    // Prevent multiple simultaneous token acquisitions
    if (isAcquiringToken) {
      return accessToken;
    }

    setIsAcquiringToken(true);

    try {
      const response = await instance.acquireTokenSilent({
        ...apiRequest,
        account: accounts[0],
      });
      setAccessToken(response.accessToken);
      setIsAcquiringToken(false);
      return response.accessToken;
    } catch (error) {
      // Only fall back to interactive for interaction required errors
      if (error instanceof InteractionRequiredAuthError) {
        console.warn("Interaction required, falling back to popup:", error);
        try {
          const response = await instance.acquireTokenPopup(apiRequest);
          setAccessToken(response.accessToken);
          setIsAcquiringToken(false);
          return response.accessToken;
        } catch (popupError) {
          console.error("Failed to acquire token via popup:", popupError);
          setIsAcquiringToken(false);
          return null;
        }
      } else {
        // For other errors, log and rethrow
        console.error("Token acquisition failed:", error);
        setIsAcquiringToken(false);
        throw error;
      }
    }
  }, [instance, accounts, inProgress, isAcquiringToken, accessToken]);

  // Acquire token on mount and when accounts change
  useEffect(() => {
    if (accounts.length > 0 && inProgress === InteractionStatus.None) {
      acquireToken();
    }
  }, [accounts, inProgress]);

  // Re-acquire token periodically (every 4 minutes) to ensure fresh tokens
  // Access tokens typically expire after 1 hour, this ensures we get a new one before expiry
  useEffect(() => {
    if (accounts.length === 0) return;

    const refreshInterval = setInterval(() => {
      if (inProgress === InteractionStatus.None) {
        acquireToken();
      }
    }, 4 * 60 * 1000); // 4 minutes

    return () => clearInterval(refreshInterval);
  }, [accounts, inProgress, acquireToken]);

  return { accessToken, acquireToken };
}

// Hook for authentication actions
export function useAuth() {
  const { instance, accounts, inProgress } = useMsal();
  const isAuthenticatedMsal = useIsAuthenticated();
  
  // If auth is skipped, always return authenticated
  const isAuthenticated = SKIP_AUTH ? true : isAuthenticatedMsal;

  const login = useCallback(async () => {
    if (SKIP_AUTH) {
      console.log("Auth skipped - test mode enabled");
      return;
    }
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error("Login failed:", error);
    }
  }, [instance]);

  const logout = useCallback(async () => {
    if (SKIP_AUTH) {
      console.log("Auth skipped - test mode enabled");
      return;
    }
    try {
      await instance.logoutPopup({
        postLogoutRedirectUri: window.location.origin,
      });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }, [instance]);

  const user = accounts[0] || null;
  const isLoading = SKIP_AUTH ? false : inProgress !== InteractionStatus.None;

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    username: SKIP_AUTH ? "Test User" : (user?.username || user?.name || null),
    name: SKIP_AUTH ? "Test User" : (user?.name || user?.username || null),
  };
}
