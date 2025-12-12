import { CSSProperties } from "react";

interface QuoteCardProps {
  result?: string;
  status: "pending" | "complete" | "error";
}

export function QuoteCard({ result, status }: QuoteCardProps) {
  const containerStyle: CSSProperties = {
    padding: "16px",
    borderRadius: "12px",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "white",
    marginBottom: "16px",
    boxShadow: "0 2px 8px rgba(102, 126, 234, 0.3)",
  };

  const iconStyle: CSSProperties = {
    fontSize: "28px",
    marginRight: "12px",
  };

  const textStyle: CSSProperties = {
    fontSize: "16px",
    lineHeight: "1.6",
    margin: "0",
    fontStyle: "italic",
  };

  const authorStyle: CSSProperties = {
    fontSize: "14px",
    marginTop: "12px",
    opacity: 0.9,
    textAlign: "right" as const,
  };

  const loadingStyle: CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  };

  const pulseStyle: CSSProperties = {
    display: "inline-block",
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: "rgba(255, 255, 255, 0.7)",
    animation: "pulse 1.5s infinite",
  };

  return (
    <div style={containerStyle}>
      <div style={{ display: "flex", alignItems: "flex-start" }}>
        <span style={iconStyle}>✨</span>
        <div style={{ flex: 1 }}>
          {status === "pending" && (
            <div style={loadingStyle}>
              <span>Finding the perfect quote...</span>
              <span style={pulseStyle} />
            </div>
          )}
          {status === "complete" && result && (
            <>
              <p style={textStyle}>{result}</p>
              <style>{`
                @keyframes pulse {
                  0%, 100% { opacity: 1; }
                  50% { opacity: 0.5; }
                }
              `}</style>
            </>
          )}
          {status === "error" && (
            <p style={textStyle}>Failed to fetch quote. Please try again.</p>
          )}
        </div>
      </div>
    </div>
  );
}
