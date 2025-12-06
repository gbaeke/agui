/**
 * CopilotKit Runtime Server
 * 
 * This server acts as a bridge between the React frontend (CopilotKit)
 * and the Python AG-UI backend (Microsoft Agent Framework).
 */

import "dotenv/config";
import express, { Request, Response, NextFunction } from "express";
import path from "path";
import { fileURLToPath } from "url";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNodeHttpEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import jwt from "jsonwebtoken";
import jwksRsa from "jwks-rsa";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;

// AG-UI backend URL (Python server)
const AGUI_BACKEND_URL = process.env.AGUI_BACKEND_URL || "http://127.0.0.1:8888/";

// Entra ID configuration
const ENTRA_TENANT_ID = process.env.ENTRA_TENANT_ID || "";
const ENTRA_AUDIENCE = process.env.ENTRA_AUDIENCE || "";

// JWKS client for fetching Microsoft's public keys
const jwksClient = jwksRsa({
  jwksUri: `https://login.microsoftonline.com/${ENTRA_TENANT_ID}/discovery/v2.0/keys`,
  cache: true,
  cacheMaxAge: 86400000, // 24 hours
  rateLimit: true,
});

// Function to get the signing key
function getSigningKey(header: jwt.JwtHeader, callback: jwt.SigningKeyCallback) {
  jwksClient.getSigningKey(header.kid, (err, key) => {
    if (err) {
      callback(err);
      return;
    }
    const signingKey = key?.getPublicKey();
    callback(null, signingKey);
  });
}

// Token validation middleware
async function validateToken(req: Request, res: Response, next: NextFunction): Promise<void> {
  // Skip validation if Entra ID is not configured
  if (!ENTRA_TENANT_ID || !ENTRA_AUDIENCE) {
    console.warn("⚠️  Entra ID not configured - skipping token validation");
    next();
    return;
  }

  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    res.status(401).json({ error: "Missing or invalid Authorization header" });
    return;
  }

  const token = authHeader.substring(7); // Remove "Bearer " prefix

  try {
    await new Promise<jwt.JwtPayload>((resolve, reject) => {
      jwt.verify(
        token,
        getSigningKey,
        {
          algorithms: ["RS256"],
          audience: ENTRA_AUDIENCE,
          issuer: `https://sts.windows.net/${ENTRA_TENANT_ID}/`,
        },
        (err, decoded) => {
          if (err) {
            reject(err);
          } else {
            resolve(decoded as jwt.JwtPayload);
          }
        }
      );
    });

    // Token is valid
    console.log(`[${new Date().toISOString()}] ✅ Token validated successfully`);
    next();
  } catch (error) {
    console.error(`[${new Date().toISOString()}] ❌ Token validation failed:`, error);
    res.status(401).json({ 
      error: "Invalid token",
      details: error instanceof Error ? error.message : "Unknown error"
    });
  }
}

// Create the service adapter (empty since we're using AG-UI agent)
const serviceAdapter = new ExperimentalEmptyAdapter();

// Handle CopilotKit requests with token validation
app.use("/api/copilotkit", validateToken, (req, res, next) => {
  console.log(`[${new Date().toISOString()}] Incoming request to /api/copilotkit`);
  
  // Get the Authorization header to forward to the backend
  const authHeader = req.headers.authorization;
  
  (async () => {
    // Create the CopilotRuntime inside the handler (per the docs)
    // Forward the Authorization header to the Python backend
    const runtime = new CopilotRuntime({
      agents: {
        agui_assistant: new HttpAgent({ 
          url: AGUI_BACKEND_URL,
          headers: authHeader ? { Authorization: authHeader } : undefined,
        }),
      },
    });

    const handler = copilotRuntimeNodeHttpEndpoint({
      endpoint: "/api/copilotkit",
      runtime,
      serviceAdapter,
    });

    return handler(req, res);
  })().catch(next);
});

// Health check
app.get("/health", (_, res) => {
  res.json({ status: "ok", aguiBackend: AGUI_BACKEND_URL });
});

// In production, serve static React files
if (process.env.NODE_ENV === "production") {
  const publicPath = path.join(__dirname, "..", "public");
  app.use(express.static(publicPath));
  
  // Fallback to index.html for client-side routing (Express 5 syntax)
  app.get("/{*splat}", (_, res) => {
    res.sendFile(path.join(publicPath, "index.html"));
  });
}

app.listen(PORT, () => {
  const externalPort = process.env.EXTERNAL_PORT || PORT;
  console.log(`🚀 CopilotKit Runtime server running at http://localhost:${externalPort}`);
  console.log(`   (internal port: ${PORT})`);
  console.log(`📡 Connected to AG-UI backend at ${AGUI_BACKEND_URL}`);
  
  if (ENTRA_TENANT_ID && ENTRA_AUDIENCE) {
    console.log(`🔐 Entra ID authentication enabled`);
    console.log(`   Tenant: ${ENTRA_TENANT_ID}`);
    console.log(`   Audience: ${ENTRA_AUDIENCE}`);
  } else {
    console.log(`⚠️  Entra ID authentication NOT configured (ENTRA_TENANT_ID or ENTRA_AUDIENCE missing)`);
  }
  
  console.log(`\nEndpoints:`);
  console.log(`  - POST /api/copilotkit - CopilotKit requests`);
  console.log(`  - GET  /health        - Health check`);
  if (process.env.NODE_ENV === "production") {
    console.log(`  - GET  /*             - React frontend`);
  }
});
