type ToolStatus = "pending" | "complete" | "error";

type A2AResult = {
  question?: string;
  goal?: string | null;
  draft?: string;
  critique?: string;
  final?: string;
};

function parseA2AResult(result: unknown): A2AResult | null {
  if (!result) return null;
  if (typeof result === "object") return result as A2AResult;
  if (typeof result === "string") {
    try {
      const parsed = JSON.parse(result);
      return typeof parsed === "object" && parsed ? (parsed as A2AResult) : null;
    } catch {
      return { final: result };
    }
  }
  return { final: String(result) };
}

export function A2ACard({
  status,
  result,
}: {
  status: ToolStatus;
  result?: unknown;
}) {
  const parsed = parseA2AResult(result);

  return (
    <div className="tool-card a2a-tool">
      <div className="tool-header">
        <span className="tool-icon">🤝</span>
        <span className="tool-name">A2A Collaboration</span>
        <span className={`tool-status ${status}`}>
          {status === "complete" ? "✓" : status === "error" ? "!" : "⏳"}
        </span>
      </div>

      <div className="tool-body">
        {status !== "complete" && (
          <p className="tool-loading">Two agents are collaborating…</p>
        )}

        {status === "complete" && parsed && (
          <>
            {parsed.draft && (
              <div style={{ marginBottom: 12 }}>
                <p><strong>Draft</strong></p>
                <p style={{ whiteSpace: "pre-wrap" }}>{parsed.draft}</p>
              </div>
            )}

            {parsed.critique && (
              <div style={{ marginBottom: 12 }}>
                <p><strong>Critique</strong></p>
                <p style={{ whiteSpace: "pre-wrap" }}>{parsed.critique}</p>
              </div>
            )}

            {parsed.final && (
              <div>
                <p><strong>Final</strong></p>
                <p style={{ whiteSpace: "pre-wrap" }}>{parsed.final}</p>
              </div>
            )}
          </>
        )}

        {status === "error" && (
          <p className="tool-loading">A2A failed. Please try again.</p>
        )}
      </div>
    </div>
  );
}
