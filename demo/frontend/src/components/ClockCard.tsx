import { useMemo } from "react";

interface ClockCardProps {
  status: "inProgress" | "executing" | "complete";
  result?: string;
}

// Parse the time result string: "Current date and time: 2025-12-04 18:30:45"
function parseTimeResult(result: string): { date: string; time: string; hours: number; minutes: number; seconds: number } | null {
  const match = result.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
  if (match) {
    return {
      date: match[1],
      time: `${match[2]}:${match[3]}:${match[4]}`,
      hours: parseInt(match[2], 10),
      minutes: parseInt(match[3], 10),
      seconds: parseInt(match[4], 10),
    };
  }
  return null;
}

// Format date nicely
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function ClockCard({ status, result }: ClockCardProps) {
  const timeData = useMemo(() => {
    if (status === "complete" && result) {
      return parseTimeResult(result);
    }
    return null;
  }, [status, result]);

  const isLoading = status !== "complete";

  // Calculate clock hand angles
  const hourAngle = timeData ? (timeData.hours % 12) * 30 + timeData.minutes * 0.5 : 0;
  const minuteAngle = timeData ? timeData.minutes * 6 : 0;
  const secondAngle = timeData ? timeData.seconds * 6 : 0;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        borderRadius: "16px",
        padding: "24px",
        color: "#fff",
        boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
        minWidth: "280px",
        maxWidth: "320px",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "20px",
          gap: "8px",
        }}
      >
        <span style={{ fontSize: "20px" }}>🕐</span>
        <span style={{ fontSize: "16px", fontWeight: 600, opacity: 0.9 }}>
          Current Time
        </span>
      </div>

      {isLoading ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "30px 0",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              border: "4px solid rgba(255,255,255,0.2)",
              borderTopColor: "#4facfe",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <p style={{ marginTop: "12px", opacity: 0.7 }}>Getting current time...</p>
          <style>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : timeData ? (
        <>
          {/* Analog Clock */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                width: "140px",
                height: "140px",
                borderRadius: "50%",
                background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
                position: "relative",
                boxShadow: "0 4px 20px rgba(0,0,0,0.3), inset 0 2px 10px rgba(255,255,255,0.5)",
              }}
            >
              {/* Clock face markers */}
              {[...Array(12)].map((_, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    width: i % 3 === 0 ? "3px" : "2px",
                    height: i % 3 === 0 ? "12px" : "8px",
                    background: i % 3 === 0 ? "#1a1a2e" : "#666",
                    left: "50%",
                    top: "8px",
                    transform: `translateX(-50%) rotate(${i * 30}deg)`,
                    transformOrigin: "center 62px",
                    borderRadius: "2px",
                  }}
                />
              ))}

              {/* Hour hand */}
              <div
                style={{
                  position: "absolute",
                  width: "6px",
                  height: "35px",
                  background: "#1a1a2e",
                  left: "50%",
                  bottom: "50%",
                  transform: `translateX(-50%) rotate(${hourAngle}deg)`,
                  transformOrigin: "center bottom",
                  borderRadius: "3px",
                }}
              />

              {/* Minute hand */}
              <div
                style={{
                  position: "absolute",
                  width: "4px",
                  height: "50px",
                  background: "#4facfe",
                  left: "50%",
                  bottom: "50%",
                  transform: `translateX(-50%) rotate(${minuteAngle}deg)`,
                  transformOrigin: "center bottom",
                  borderRadius: "2px",
                }}
              />

              {/* Second hand */}
              <div
                style={{
                  position: "absolute",
                  width: "2px",
                  height: "55px",
                  background: "#e74c3c",
                  left: "50%",
                  bottom: "50%",
                  transform: `translateX(-50%) rotate(${secondAngle}deg)`,
                  transformOrigin: "center bottom",
                  borderRadius: "1px",
                }}
              />

              {/* Center dot */}
              <div
                style={{
                  position: "absolute",
                  width: "12px",
                  height: "12px",
                  background: "#1a1a2e",
                  borderRadius: "50%",
                  left: "50%",
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  boxShadow: "0 0 0 2px #4facfe",
                }}
              />
            </div>
          </div>

          {/* Digital time */}
          <div
            style={{
              textAlign: "center",
              marginBottom: "12px",
            }}
          >
            <div
              style={{
                fontSize: "36px",
                fontWeight: 300,
                fontFamily: "monospace",
                letterSpacing: "2px",
              }}
            >
              {timeData.time}
            </div>
          </div>

          {/* Date */}
          <div
            style={{
              textAlign: "center",
              fontSize: "14px",
              opacity: 0.8,
              borderTop: "1px solid rgba(255,255,255,0.1)",
              paddingTop: "12px",
            }}
          >
            📅 {formatDate(timeData.date)}
          </div>
        </>
      ) : (
        <div style={{ textAlign: "center", padding: "20px 0", opacity: 0.7 }}>
          <p>Unable to parse time data</p>
          <p style={{ fontSize: "12px", marginTop: "8px" }}>{result}</p>
        </div>
      )}
    </div>
  );
}
