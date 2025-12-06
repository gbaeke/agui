#!/bin/bash

# Entra ID App Registration Setup Script
# This script creates the necessary app registrations for the CopilotKit demo
# Prerequisites: Azure CLI installed and logged in with sufficient permissions

set -e

# Configuration - customize these values
APP_NAME_PREFIX="${APP_NAME_PREFIX:-copilotkit-demo}"
FRONTEND_REDIRECT_URI="${FRONTEND_REDIRECT_URI:-http://localhost:5173}"
PRODUCTION_REDIRECT_URI="${PRODUCTION_REDIRECT_URI:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Entra ID App Registration Setup${NC}"
echo -e "${GREEN}======================================${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
echo -e "\n${YELLOW}Checking Azure CLI login status...${NC}"
ACCOUNT=$(az account show --query name -o tsv 2>/dev/null || true)
if [ -z "$ACCOUNT" ]; then
    echo -e "${RED}Error: Not logged in to Azure CLI. Please run 'az login' first.${NC}"
    exit 1
fi
echo -e "${GREEN}Logged in to: $ACCOUNT${NC}"

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo -e "${GREEN}Tenant ID: $TENANT_ID${NC}"

# ======================================
# Create Frontend SPA App Registration
# ======================================
echo -e "\n${YELLOW}Creating Frontend SPA App Registration...${NC}"

# Check if app already exists
EXISTING_APP=$(az ad app list --display-name "${APP_NAME_PREFIX}-frontend" --query "[0].appId" -o tsv 2>/dev/null || true)

if [ -n "$EXISTING_APP" ]; then
    echo -e "${YELLOW}App '${APP_NAME_PREFIX}-frontend' already exists with ID: $EXISTING_APP${NC}"
    echo -e "${YELLOW}Do you want to delete and recreate it? (y/n)${NC}"
    read -r RECREATE
    if [ "$RECREATE" = "y" ]; then
        echo -e "${YELLOW}Deleting existing app...${NC}"
        az ad app delete --id "$EXISTING_APP"
        EXISTING_APP=""
    else
        FRONTEND_CLIENT_ID="$EXISTING_APP"
    fi
fi

if [ -z "$EXISTING_APP" ]; then
    # Create the SPA app registration
    FRONTEND_CLIENT_ID=$(az ad app create \
        --display-name "${APP_NAME_PREFIX}-frontend" \
        --sign-in-audience "AzureADMyOrg" \
        --query appId -o tsv)

    echo -e "${GREEN}Created frontend app with Client ID: $FRONTEND_CLIENT_ID${NC}"

    # Configure as SPA with redirect URIs
    REDIRECT_URIS="[\"$FRONTEND_REDIRECT_URI\"]"
    if [ -n "$PRODUCTION_REDIRECT_URI" ]; then
        REDIRECT_URIS="[\"$FRONTEND_REDIRECT_URI\", \"$PRODUCTION_REDIRECT_URI\"]"
    fi

    # Update the app to be a SPA
    az ad app update --id "$FRONTEND_CLIENT_ID" \
        --set spa="{\"redirectUris\": $REDIRECT_URIS}"

    echo -e "${GREEN}Configured SPA redirect URIs${NC}"

    # Add optional claims for ID token (useful for getting user info)
    az ad app update --id "$FRONTEND_CLIENT_ID" \
        --set optionalClaims="{\"idToken\": [{\"name\": \"email\", \"essential\": false}, {\"name\": \"preferred_username\", \"essential\": false}]}"

    echo -e "${GREEN}Added optional claims${NC}"
fi

# ======================================
# Create Backend API App Registration
# ======================================
echo -e "\n${YELLOW}Creating Backend API App Registration...${NC}"

# Check if backend app already exists
EXISTING_BACKEND=$(az ad app list --display-name "${APP_NAME_PREFIX}-backend" --query "[0].appId" -o tsv 2>/dev/null || true)

if [ -n "$EXISTING_BACKEND" ]; then
    echo -e "${YELLOW}App '${APP_NAME_PREFIX}-backend' already exists with ID: $EXISTING_BACKEND${NC}"
    echo -e "${YELLOW}Do you want to delete and recreate it? (y/n)${NC}"
    read -r RECREATE_BACKEND
    if [ "$RECREATE_BACKEND" = "y" ]; then
        echo -e "${YELLOW}Deleting existing backend app...${NC}"
        az ad app delete --id "$EXISTING_BACKEND"
        EXISTING_BACKEND=""
    else
        BACKEND_CLIENT_ID="$EXISTING_BACKEND"
    fi
fi

if [ -z "$EXISTING_BACKEND" ]; then
    # Create the backend API app registration
    BACKEND_CLIENT_ID=$(az ad app create \
        --display-name "${APP_NAME_PREFIX}-backend" \
        --sign-in-audience "AzureADMyOrg" \
        --query appId -o tsv)

    echo -e "${GREEN}Created backend app with Client ID: $BACKEND_CLIENT_ID${NC}"

    # Generate a unique scope ID
    SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

    # Expose an API with a scope
    az ad app update --id "$BACKEND_CLIENT_ID" \
        --identifier-uris "api://$BACKEND_CLIENT_ID"

    # Add the access_as_user scope
    az ad app update --id "$BACKEND_CLIENT_ID" \
        --set api="{\"oauth2PermissionScopes\": [{\"adminConsentDescription\": \"Allow the application to access the backend API on behalf of the signed-in user\", \"adminConsentDisplayName\": \"Access Backend API\", \"id\": \"$SCOPE_ID\", \"isEnabled\": true, \"type\": \"User\", \"userConsentDescription\": \"Allow the application to access the backend API on your behalf\", \"userConsentDisplayName\": \"Access Backend API\", \"value\": \"access_as_user\"}]}"

    echo -e "${GREEN}Exposed API with scope: api://$BACKEND_CLIENT_ID/access_as_user${NC}"
fi

# ======================================
# Grant Frontend permission to Backend API
# ======================================
echo -e "\n${YELLOW}Granting frontend app permission to backend API...${NC}"

# Get the backend app's service principal
BACKEND_SP_ID=$(az ad sp list --filter "appId eq '$BACKEND_CLIENT_ID'" --query "[0].id" -o tsv 2>/dev/null || true)

if [ -z "$BACKEND_SP_ID" ]; then
    # Create service principal for backend if it doesn't exist
    BACKEND_SP_ID=$(az ad sp create --id "$BACKEND_CLIENT_ID" --query id -o tsv)
    echo -e "${GREEN}Created service principal for backend app${NC}"
fi

# Get the scope ID from the backend app
SCOPE_ID=$(az ad app show --id "$BACKEND_CLIENT_ID" --query "api.oauth2PermissionScopes[0].id" -o tsv)

# Add API permission to frontend app
az ad app permission add \
    --id "$FRONTEND_CLIENT_ID" \
    --api "$BACKEND_CLIENT_ID" \
    --api-permissions "$SCOPE_ID=Scope" 2>/dev/null || true

echo -e "${GREEN}Added API permission to frontend app${NC}"

# Also add Microsoft Graph User.Read permission
GRAPH_API_ID="00000003-0000-0000-c000-000000000000"
USER_READ_SCOPE_ID="e1fe6dd8-ba31-4d61-89e7-88639da4683d"

az ad app permission add \
    --id "$FRONTEND_CLIENT_ID" \
    --api "$GRAPH_API_ID" \
    --api-permissions "$USER_READ_SCOPE_ID=Scope" 2>/dev/null || true

echo -e "${GREEN}Added Microsoft Graph User.Read permission${NC}"

# ======================================
# Output Configuration
# ======================================
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"

echo -e "\n${YELLOW}Frontend Configuration:${NC}"
echo -e "  Client ID:     ${GREEN}$FRONTEND_CLIENT_ID${NC}"
echo -e "  Tenant ID:     ${GREEN}$TENANT_ID${NC}"
echo -e "  Authority:     ${GREEN}https://login.microsoftonline.com/$TENANT_ID${NC}"
echo -e "  Redirect URI:  ${GREEN}$FRONTEND_REDIRECT_URI${NC}"

echo -e "\n${YELLOW}Backend Configuration:${NC}"
echo -e "  Client ID:     ${GREEN}$BACKEND_CLIENT_ID${NC}"
echo -e "  API Scope:     ${GREEN}api://$BACKEND_CLIENT_ID/access_as_user${NC}"

echo -e "\n${YELLOW}Environment Variables (add to .env files):${NC}"
echo -e "${GREEN}# Frontend (.env)${NC}"
echo "VITE_ENTRA_CLIENT_ID=$FRONTEND_CLIENT_ID"
echo "VITE_ENTRA_TENANT_ID=$TENANT_ID"
echo "VITE_ENTRA_REDIRECT_URI=$FRONTEND_REDIRECT_URI"
echo "VITE_ENTRA_API_SCOPE=api://$BACKEND_CLIENT_ID/access_as_user"

echo -e "\n${GREEN}# Backend (.env)${NC}"
echo "ENTRA_CLIENT_ID=$BACKEND_CLIENT_ID"
echo "ENTRA_TENANT_ID=$TENANT_ID"
echo "ENTRA_AUDIENCE=api://$BACKEND_CLIENT_ID"

# Update the demo/.env file
ENV_FILE="demo/.env"

# Remove existing Entra ID configuration if present (to avoid duplicates)
if [ -f "$ENV_FILE" ]; then
    # Create a temp file without existing Entra config
    grep -v "^# Entra ID" "$ENV_FILE" | grep -v "^VITE_ENTRA_" | grep -v "^ENTRA_" > "${ENV_FILE}.tmp" || true
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
fi

# Append Entra ID configuration to .env
cat >> "$ENV_FILE" << EOF

# Entra ID Configuration - Generated $(date)
# Frontend Configuration
VITE_ENTRA_CLIENT_ID=$FRONTEND_CLIENT_ID
VITE_ENTRA_TENANT_ID=$TENANT_ID
VITE_ENTRA_REDIRECT_URI=$FRONTEND_REDIRECT_URI
VITE_ENTRA_API_SCOPE=api://$BACKEND_CLIENT_ID/access_as_user

# Backend Configuration
ENTRA_CLIENT_ID=$BACKEND_CLIENT_ID
ENTRA_TENANT_ID=$TENANT_ID
ENTRA_AUDIENCE=api://$BACKEND_CLIENT_ID
EOF

echo -e "\n${GREEN}Configuration added to: $ENV_FILE${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Install MSAL packages in frontend: cd demo/frontend && npm install @azure/msal-react @azure/msal-browser"
echo -e "2. Configure MSAL in your React app"
echo -e "3. Add token validation to your backend"

echo -e "\n${YELLOW}Note:${NC} You may need to grant admin consent for the API permissions."
echo -e "Run: ${GREEN}az ad app permission admin-consent --id $FRONTEND_CLIENT_ID${NC}"
