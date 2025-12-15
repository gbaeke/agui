type CatalogSearchResult = {
  query?: string;
  count?: number;
  results?: Array<{
    productId?: string;
    name?: string;
    category?: string;
    price?: number | string;
    description?: string;
    punchLine?: string;
    imageUrl?: string;
    score?: number;
    debugKeys?: string[] | null;
  }>;
  error?: string;
};

function parseResult(raw: unknown): CatalogSearchResult | null {
  if (!raw) return null;

  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as CatalogSearchResult;
    } catch {
      return { error: String(raw) };
    }
  }

  if (typeof raw === "object") {
    return raw as CatalogSearchResult;
  }

  return { error: String(raw) };
}

export function CatalogSearchCard(props: { status: string; result: unknown }) {
  const parsed = parseResult(props.result);

  return (
    <div className="tool-card">
      <div className="tool-header">
        <span className="tool-icon">🔎</span>
        <span className="tool-name">Catalog Search</span>
        <span className={`tool-status ${props.status}`}>
          {props.status === "complete" ? "✓" : "⏳"}
        </span>
      </div>

      <div className="tool-body">
        {props.status !== "complete" && <p className="tool-loading">Searching catalog...</p>}

        {props.status === "complete" && parsed?.error && (
          <p className="tool-result">
            <strong>Error:</strong> {parsed.error}
          </p>
        )}

        {props.status === "complete" && !parsed?.error && (
          <>
            <p>
              <strong>Query:</strong> {parsed?.query || "(unknown)"}
            </p>

            {(parsed?.results?.length || 0) === 0 ? (
              <p className="tool-result">No matches found.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {parsed?.results?.map((p, idx) => (
                  <div
                    key={`${p.productId || p.name || "item"}-${idx}`}
                    style={{
                      display: "flex",
                      gap: "12px",
                      alignItems: "flex-start",
                    }}
                  >
                    {p.imageUrl ? (
                      <img
                        src={p.imageUrl}
                        alt={p.name || "Product"}
                        style={{
                          width: "64px",
                          height: "64px",
                          objectFit: "cover",
                          borderRadius: "8px",
                          flex: "0 0 auto",
                        }}
                      />
                    ) : null}

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                        <div style={{ fontWeight: 600 }}>
                          {p.name || p.productId || "(Unnamed product)"}
                          {p.productId ? (
                            <span style={{ opacity: 0.7, marginLeft: "8px", fontWeight: 400 }}>
                              {p.productId}
                            </span>
                          ) : null}
                        </div>
                        {p.price !== undefined && p.price !== null ? (
                          <div style={{ whiteSpace: "nowrap" }}>${String(p.price)}</div>
                        ) : null}
                      </div>

                      {p.category ? (
                        <div style={{ opacity: 0.8, fontSize: "13px", marginTop: "2px" }}>
                          {p.category}
                        </div>
                      ) : null}

                      {p.punchLine ? (
                        <div style={{ marginTop: "6px" }}>
                          <em>{p.punchLine}</em>
                        </div>
                      ) : null}

                      {p.description ? (
                        <div style={{ marginTop: "6px", opacity: 0.9 }}>
                          {p.description}
                        </div>
                      ) : null}

                      {p.debugKeys && p.debugKeys.length ? (
                        <div style={{ marginTop: "6px", fontSize: "12px", opacity: 0.7 }}>
                          Debug keys: {p.debugKeys.join(", ")}
                        </div>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
