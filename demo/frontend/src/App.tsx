import { CopilotKit, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import "./App.css";
import { WeatherCard } from "./components/WeatherCard";
import { ClockCard } from "./components/ClockCard";
import { useAuth, useAccessToken } from "./useAuth";

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
  const { accessToken } = useAccessToken();

  // Build headers with the access token
  const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined;

  return (
    <CopilotKit 
      runtimeUrl="/api/copilotkit" 
      agent="agui_assistant" 
      showDevConsole={false}
      headers={headers}
    >
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "#f5f5f5",
        padding: "20px",
        boxSizing: "border-box",
      }}>
        <div style={{
          width: "100%",
          maxWidth: "700px",
          height: "90vh",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.1)",
          display: "flex",
          flexDirection: "column",
          background: "white",
        }}>
          <UserHeader />
          <div style={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}>
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
  // Render weather tool calls with nice weather card
  useCopilotAction({
    name: "get_weather",
    available: "disabled", // This is render-only, backend handles execution
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
  useCopilotAction({
    name: "get_current_time",
    available: "disabled",
    parameters: [],
    render: ({ status, result }) => (
      <ClockCard
        status={status}
        result={result ? String(result) : undefined}
      />
    ),
  });

  // Render calculator tool calls
  useCopilotAction({
    name: "calculate",
    available: "disabled",
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
  useCopilotAction({
    name: "tell_bedtime_story",
    available: "disabled",
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
