import { CopilotKit, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import "./App.css";
import { WeatherCard } from "./components/WeatherCard";
import { ClockCard } from "./components/ClockCard";

function App() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="agui_assistant" showDevConsole={false}>
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "#f5f5f5",
        padding: "20px",
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
    </CopilotKit>
  );
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
        result={result ? String(result) : undefined}
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

  return null;
}

export default App;
