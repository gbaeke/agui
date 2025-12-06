import { useMemo } from "react";

interface WeatherCardProps {
  location: string;
  status: "inProgress" | "executing" | "complete";
  result?: string | object;
}

interface WeatherData {
  location: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  condition: string;
  error?: string;
}

// Map weather conditions to icons and colors
const weatherConfig: Record<string, { icon: string; gradient: string }> = {
  sunny: { icon: "☀️", gradient: "linear-gradient(135deg, #f6d365 0%, #fda085 100%)" },
  cloudy: { icon: "☁️", gradient: "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)" },
  "partly cloudy": { icon: "⛅", gradient: "linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)" },
  rainy: { icon: "🌧️", gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)" },
  snowy: { icon: "❄️", gradient: "linear-gradient(135deg, #e6e9f0 0%, #eef1f5 100%)" },
  stormy: { icon: "⛈️", gradient: "linear-gradient(135deg, #373b44 0%, #4286f4 100%)" },
  foggy: { icon: "🌫️", gradient: "linear-gradient(135deg, #d7d2cc 0%, #304352 100%)" },
  default: { icon: "🌡️", gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" },
};

// Parse the weather result - handles both string and object
function parseWeatherResult(result: string | object): WeatherData | null {
  try {
    // If result is already an object, use it directly
    let data: Record<string, unknown>;
    if (typeof result === "object" && result !== null) {
      data = result as Record<string, unknown>;
    } else if (typeof result === "string") {
      // Try to parse as JSON string
      data = JSON.parse(result);
    } else {
      return null;
    }
    
    if (data.error) {
      return null;
    }
    
    // Validate required fields exist
    if (typeof data.temperature === "number" && typeof data.condition === "string") {
      return {
        location: String(data.location || ""),
        temperature: data.temperature,
        humidity: typeof data.humidity === "number" ? data.humidity : 0,
        wind_speed: typeof data.wind_speed === "number" ? data.wind_speed : 0,
        condition: data.condition,
      };
    }
    
    return null;
  } catch {
    // Fallback: try to parse old format "Weather in Paris: 22°C, sunny"
    if (typeof result === "string") {
      const match = result.match(/Weather in ([^:]+):\s*(\d+)°C,\s*(.+)$/);
      if (match) {
        return {
          location: match[1],
          temperature: parseInt(match[2], 10),
          humidity: 0,
          wind_speed: 0,
          condition: match[3].toLowerCase().trim(),
        };
      }
    }
    return null;
  }
}

export function WeatherCard({ location, status, result }: WeatherCardProps) {
  const weatherData = useMemo(() => {
    if (status === "complete" && result) {
      return parseWeatherResult(result);
    }
    return null;
  }, [status, result]);

  const config = weatherData
    ? weatherConfig[weatherData.condition] || weatherConfig.default
    : weatherConfig.default;

  const isLoading = status !== "complete";

  return (
    <div
      style={{
        background: isLoading ? "#f0f4f8" : config.gradient,
        borderRadius: "16px",
        padding: "20px",
        color: isLoading ? "#333" : "#fff",
        boxShadow: "0 10px 40px rgba(0,0,0,0.15)",
        minWidth: "280px",
        maxWidth: "320px",
        fontFamily: "system-ui, -apple-system, sans-serif",
        transition: "all 0.3s ease",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "20px" }}>📍</span>
          <span
            style={{
              fontSize: "18px",
              fontWeight: 600,
              textTransform: "capitalize",
            }}
          >
            {location || "Loading..."}
          </span>
        </div>
        {!isLoading && (
          <span
            style={{
              fontSize: "14px",
              opacity: 0.9,
              background: "rgba(255,255,255,0.2)",
              padding: "4px 8px",
              borderRadius: "8px",
            }}
          >
            Now
          </span>
        )}
      </div>

      {/* Main content */}
      {isLoading ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "20px 0",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              border: "4px solid #e0e0e0",
              borderTopColor: "#667eea",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <p style={{ marginTop: "12px", color: "#666" }}>
            Fetching weather data...
          </p>
          <style>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : weatherData ? (
        <>
          {/* Temperature and Icon */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                fontSize: "64px",
                fontWeight: 300,
                lineHeight: 1,
              }}
            >
              {Math.round(weatherData.temperature)}°
            </div>
            <div style={{ fontSize: "64px" }}>{config.icon}</div>
          </div>

          {/* Condition */}
          <div
            style={{
              fontSize: "20px",
              textTransform: "capitalize",
              fontWeight: 500,
              opacity: 0.95,
            }}
          >
            {weatherData.condition}
          </div>

          {/* Weather details footer */}
          <div
            style={{
              marginTop: "16px",
              paddingTop: "16px",
              borderTop: "1px solid rgba(255,255,255,0.3)",
              display: "flex",
              justifyContent: "space-between",
              fontSize: "13px",
              opacity: 0.9,
            }}
          >
            <span>💧 {weatherData.humidity}%</span>
            <span>💨 {weatherData.wind_speed} km/h</span>
          </div>
        </>
      ) : (
        <div style={{ textAlign: "center", padding: "20px 0", color: "#666" }}>
          <p>Unable to parse weather data</p>
          <p style={{ fontSize: "12px", marginTop: "8px" }}>
            {typeof result === "string" ? result : JSON.stringify(result)}
          </p>
        </div>
      )}
    </div>
  );
}
