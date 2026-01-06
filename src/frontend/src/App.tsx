import { CopilotKit, useCoAgent, useFrontendTool, useHumanInTheLoop, useRenderToolCall } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useState } from "react";
import "@copilotkit/react-ui/styles.css";
import "./App.css";
import { WeatherCard } from "./components/WeatherCard";
import { ClockCard } from "./components/ClockCard";
import { useAuth, useAccessToken } from "./useAuth";

type AgentPreferences = {
  language?: "en" | "nl";
  style?: "regular" | "pirate";
};

function PreferencesPanel() {
  const { state, setState } = useCoAgent<AgentPreferences>({
    name: "agui_assistant",
    initialState: { language: "en", style: "regular" },
  });

  const language: "en" | "nl" = state?.language === "nl" ? "nl" : "en";
  const style: "regular" | "pirate" = state?.style === "pirate" ? "pirate" : "regular";

  // Be defensive: if state exists but lacks keys, fill them.
  useEffect(() => {
    const next: AgentPreferences = { ...(state ?? {}) };
    let changed = false;
    if (next.language !== "en" && next.language !== "nl") {
      next.language = "en";
      changed = true;
    }
    if (next.style !== "regular" && next.style !== "pirate") {
      next.style = "regular";
      changed = true;
    }
    if (changed) {
      setState({ ...(state ?? {}), ...next });
    }
  }, [state, setState]);

  const setPreference = (partial: AgentPreferences) => {
    setState({ ...(state ?? {}), ...partial });
  };

  return (
    <div className="prefs-card">
      <div className="prefs-header">
        <div className="prefs-title">Preferences</div>
        <div className="prefs-subtitle">Applied to every reply</div>
      </div>

      <div className="prefs-group">
        <div className="prefs-label">Style</div>
        <div className="segmented" role="group" aria-label="Style">
          <button
            type="button"
            className={style === "regular" ? "seg active" : "seg"}
            onClick={() => setPreference({ style: "regular" })}
          >
            Regular
          </button>
          <button
            type="button"
            className={style === "pirate" ? "seg active" : "seg"}
            onClick={() => setPreference({ style: "pirate" })}
          >
            Pirate
          </button>
        </div>
      </div>

      <div className="prefs-group">
        <div className="prefs-label">Language</div>
        <div className="segmented" role="group" aria-label="Language">
          <button
            type="button"
            className={language === "en" ? "seg active" : "seg"}
            onClick={() => setPreference({ language: "en" })}
          >
            EN
          </button>
          <button
            type="button"
            className={language === "nl" ? "seg active" : "seg"}
            onClick={() => setPreference({ language: "nl" })}
          >
            NL
          </button>
        </div>
      </div>

      <div className="prefs-hint">
        {language === "nl" ? "De assistent antwoordt in het Nederlands." : "The assistant replies in English."}
        {" "}
        {style === "pirate" ? "(Pirate style)" : ""}
      </div>
    </div>
  );
}

// Login screen component
function LoginScreen() {
  const { login, isLoading } = useAuth();

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: "20px",
    }}>
      <div style={{
        background: "white",
        borderRadius: "16px",
        padding: "48px",
        boxShadow: "0 4px 24px rgba(0, 0, 0, 0.15)",
        textAlign: "center",
        maxWidth: "400px",
        width: "100%",
      }}>
        <h1 style={{ 
          margin: "0 0 16px 0", 
          fontSize: "28px",
          color: "#333"
        }}>
          🤖 AG-UI Assistant
        </h1>
        <p style={{ 
          color: "#666", 
          marginBottom: "32px",
          lineHeight: "1.6"
        }}>
          Sign in with your Microsoft account to access the AI assistant.
        </p>
        <button
          onClick={login}
          disabled={isLoading}
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            border: "none",
            padding: "14px 32px",
            borderRadius: "8px",
            fontSize: "16px",
            fontWeight: "600",
            cursor: isLoading ? "wait" : "pointer",
            opacity: isLoading ? 0.7 : 1,
            transition: "transform 0.2s, box-shadow 0.2s",
            boxShadow: "0 2px 8px rgba(102, 126, 234, 0.4)",
          }}
          onMouseOver={(e) => {
            if (!isLoading) {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(102, 126, 234, 0.5)";
            }
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 2px 8px rgba(102, 126, 234, 0.4)";
          }}
        >
          {isLoading ? "Signing in..." : "🔐 Sign in with Microsoft"}
        </button>
      </div>
    </div>
  );
}

// User header component showing logged-in user
function UserHeader() {
  const { name, username, logout } = useAuth();

  return (
    <div style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      padding: "12px 16px",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      borderRadius: "16px 16px 0 0",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{
          width: "36px",
          height: "36px",
          borderRadius: "50%",
          background: "rgba(255,255,255,0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          fontWeight: "bold",
        }}>
          {name?.charAt(0).toUpperCase() || "U"}
        </div>
        <div>
          <div style={{ fontWeight: "600", fontSize: "14px" }}>{name || "User"}</div>
          <div style={{ fontSize: "12px", opacity: 0.8 }}>{username}</div>
        </div>
      </div>
      <button
        onClick={logout}
        style={{
          background: "rgba(255,255,255,0.2)",
          color: "white",
          border: "none",
          padding: "8px 16px",
          borderRadius: "6px",
          fontSize: "13px",
          cursor: "pointer",
          transition: "background 0.2s",
        }}
        onMouseOver={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.3)"}
        onMouseOut={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.2)"}
      >
        Sign out
      </button>
    </div>
  );
}

// Main chat component (only shown when authenticated)
function AuthenticatedChat() {
  const { accessToken, acquireToken } = useAccessToken();
  const { login } = useAuth();
  const [authError, setAuthError] = useState(false);

  // Acquire token on-demand when this authenticated experience is mounted.
  // Avoid periodic refresh to reduce background traffic.
  useEffect(() => {
    if (!accessToken) {
      acquireToken();
    }
  }, [accessToken, acquireToken]);

  if (authError) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "var(--app-bg)",
        padding: "20px",
        boxSizing: "border-box",
      }}>
        <div style={{
          width: "100%",
          maxWidth: "700px",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.1)",
          background: "white",
        }}>
          <UserHeader />
          <div style={{ padding: "20px", color: "#333" }}>
            <div style={{ fontWeight: 600, marginBottom: "8px" }}>Authentication problem</div>
            <div style={{ marginBottom: "16px" }}>
              The server rejected your token (expired/invalid). Please sign in again.
            </div>
            <div style={{ display: "flex", gap: "12px" }}>
              <button
                onClick={async () => {
                  setAuthError(false);
                  await acquireToken();
                }}
                style={{
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "1px solid #ddd",
                  background: "white",
                  cursor: "pointer",
                }}
              >
                Retry
              </button>
              <button
                onClick={async () => {
                  setAuthError(false);
                  await login();
                  await acquireToken();
                }}
                style={{
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#667eea",
                  color: "white",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Sign in again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // CopilotKit will call {runtimeUrl}/info on initialization. In practice that can happen
  // before we have an API access token available, which would fail auth and prevent
  // agent discovery. Keep the UI simple: wait until we have a token.
  if (!accessToken) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "var(--app-bg)",
        padding: "20px",
        boxSizing: "border-box",
      }}>
        <div style={{
          width: "100%",
          maxWidth: "700px",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.1)",
          background: "white",
        }}>
          <UserHeader />
          <div style={{ padding: "20px", color: "#333" }}>Acquiring API token…</div>
        </div>
      </div>
    );
  }

  // Build headers with the access token
  const headers = { Authorization: `Bearer ${accessToken}` };

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit" 
      agent="agui_assistant" 
      showDevConsole={false}
      headers={headers}
      onError={(errorEvent: any) => {
        const message =
          (typeof errorEvent?.error?.message === "string" && errorEvent.error.message) ||
          (typeof errorEvent?.error === "string" && errorEvent.error) ||
          "";

        // Best-effort detection: if the runtime/backend responds 401/403, CopilotKit will surface an error.
        if (/\b401\b/.test(message) || /\b403\b/.test(message) || /unauthorized/i.test(message)) {
          setAuthError(true);
        }
      }}
    >
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "var(--app-bg)",
        padding: "20px",
        boxSizing: "border-box",
      }}>
        <div style={{
          width: "100%",
          maxWidth: "1100px",
          height: "90vh",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.1)",
          display: "flex",
          flexDirection: "column",
          background: "white",
        }}>
          <UserHeader />
          <div className="app-shell">
            <div className="left-panel">
              <PreferencesPanel />
            </div>
            <div className="right-panel">
              <ToolRenderers />
              <CopilotChat
                className="chat-container"
                labels={{
                  title: "AG-UI Assistant",
                  initial: "Hi! 👋 I'm your AI assistant powered by AG-UI and Microsoft Agent Framework.\n\nI can help you with:\n• Weather information for any location\n• Current date and time\n• Mathematical calculations\n\nTry asking me something!",
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </CopilotKit>
  );
}

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}>
        <div style={{ color: "white", fontSize: "18px" }}>Loading...</div>
      </div>
    );
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  // Show chat when authenticated
  return <AuthenticatedChat />;
}

// Component to render tool calls in the chat
function ToolRenderers() {
  // Frontend tool: allow the agent to change the web app background color.
  // This executes in the browser only.
  useFrontendTool({
    name: "set_background_color",
    description: "Set the background color of the web app (CSS color string).",
    parameters: [
      { name: "color", type: "string", description: "CSS color value (e.g., '#111827', 'white', 'rgb(0,0,0)')", required: true },
    ],
    handler: ({ color }) => {
      const safeColor = typeof color === "string" ? color.trim() : "";
      if (!safeColor) {
        return { ok: false, error: "Missing color" };
      }

      document.documentElement.style.setProperty("--app-bg", safeColor);
      return { ok: true, color: safeColor };
    },
  });

  // Require human approval before fetching weather
  useHumanInTheLoop({
    name: "approve_weather_request",
    description: "Ask the user to approve fetching weather for a given location before calling get_weather.",
    parameters: [
      { name: "location", type: "string", description: "The location to fetch weather for", required: true },
    ],
    render: ({ args, respond }) => {
      if (!respond) return <></>;

      const location = args.location || "(unknown location)";

      return (
        <div className="tool-card story-agent">
          <div className="tool-header">
            <span className="tool-icon">✅</span>
            <span className="tool-name">Approve weather lookup</span>
            <span className="tool-status executing">⏳</span>
          </div>
          <div className="tool-body">
            <p>
              Fetch weather for: <strong>{location}</strong>?
            </p>
            <div style={{ display: "flex", gap: "12px", marginTop: "12px" }}>
              <button
                onClick={() => respond({ approved: false })}
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "1px solid #ddd",
                  background: "white",
                  cursor: "pointer",
                }}
              >
                Deny
              </button>
              <button
                onClick={() => respond({ approved: true })}
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#667eea",
                  color: "white",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      );
    },
  });

  // Render weather tool calls with nice weather card
  useRenderToolCall({
    name: "get_weather",
    parameters: [
      { name: "location", type: "string", description: "The location to get weather for" }
    ],
    render: ({ status, args, result }) => (
      <WeatherCard
        location={args.location || "..."}
        status={status}
        result={result}
      />
    ),
  });

  // Render time tool calls with clock card
  useRenderToolCall({
    name: "get_current_time",
    parameters: [],
    render: ({ status, result }) => (
      <ClockCard
        status={status}
        result={result ? String(result) : undefined}
      />
    ),
  });

  // Render calculator tool calls
  useRenderToolCall({
    name: "calculate",
    parameters: [
      { name: "expression", type: "string", description: "The math expression to calculate" }
    ],
    render: ({ status, args, result }) => (
      <div className="tool-card calc-tool">
        <div className="tool-header">
          <span className="tool-icon">🔢</span>
          <span className="tool-name">Calculator Tool</span>
          <span className={`tool-status ${status}`}>
            {status === "complete" ? "✓" : "⏳"}
          </span>
        </div>
        <div className="tool-body">
          <p><strong>Expression:</strong> <code>{args.expression || "..."}</code></p>
          {status !== "complete" && <p className="tool-loading">Calculating...</p>}
          {status === "complete" && result && (
            <p className="tool-result"><strong>Result:</strong> {String(result)}</p>
          )}
        </div>
      </div>
    ),
  });

  // Render bedtime story sub-agent invocation
  useRenderToolCall({
    name: "tell_bedtime_story",
    parameters: [
      { name: "theme", type: "string", description: "The theme for the bedtime story" }
    ],
    render: ({ status, args, result }) => (
      <div className="tool-card story-agent">
        <div className="tool-header">
          <span className="tool-icon">🌙</span>
          <span className="tool-name">BedTimeStory Agent</span>
          <span className={`tool-status ${status}`}>
            {status === "complete" ? "✓" : "⏳"}
          </span>
        </div>
        <div className="tool-body">
          <p><strong>Theme:</strong> {args.theme || "..."}</p>
          {status !== "complete" && (
            <div className="agent-thinking">
              <span className="pulse">✨</span>
              <p>Sub-agent crafting a bedtime story...</p>
            </div>
          )}
          {status === "complete" && result && (
            <div className="story-result">
              <p className="story-text">{String(result)}</p>
            </div>
          )}
        </div>
      </div>
    ),
  });

  return null;
}

export default App;
