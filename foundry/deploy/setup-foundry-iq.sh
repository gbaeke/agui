#!/bin/bash

#################################################
# Azure AI Foundry IQ Setup Script
# This script creates:
# 1. Azure AI Search with system-managed identity
# 2. Storage Account with blob access for AI Search
# 3. Azure AI Foundry Hub and Project
# 4. Role assignments for managed identities
#################################################

set -e  # Exit on error

# Parse command line arguments
NO_WAIT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --nowait)
            NO_WAIT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--nowait]"
            exit 1
            ;;
    esac
done

# Configuration variables
RESOURCE_GROUP="rg-foundryiq-demo"  # Change as needed
LOCATION="eastus"  # Change as needed

# Get subscription ID first
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")

# Create deterministic hash from subscription ID and resource group
HASH_INPUT="${SUBSCRIPTION_ID}${RESOURCE_GROUP}"
DETERMINISTIC_HASH=$(echo -n "$HASH_INPUT" | md5 | cut -c1-8)

SEARCH_SERVICE_NAME="search-fiq-${DETERMINISTIC_HASH}"
STORAGE_ACCOUNT_NAME="stfiq${DETERMINISTIC_HASH}"
FOUNDRY_RESOURCE_NAME="foundry-fiq-${DETERMINISTIC_HASH}"
FOUNDRY_PROJECT_NAME="project-fiq-${DETERMINISTIC_HASH}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Azure AI Foundry IQ Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Deterministic Hash: $DETERMINISTIC_HASH"
echo "Search Service: $SEARCH_SERVICE_NAME"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Foundry Resource: $FOUNDRY_RESOURCE_NAME"
echo "Foundry Project: $FOUNDRY_PROJECT_NAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
echo -e "${YELLOW}Checking Azure CLI login status...${NC}"
az account show &> /dev/null || {
    echo -e "${RED}Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
}

echo -e "${GREEN}Using subscription: $SUBSCRIPTION_ID${NC}"
echo ""

#################################################
# Step 1: Create Resource Group
#################################################
echo -e "${YELLOW}Step 1: Creating resource group...${NC}"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none

echo -e "${GREEN}✓ Resource group created${NC}"
echo ""

#################################################
# Step 2: Create Azure AI Search with System Managed Identity
#################################################
echo -e "${YELLOW}Step 2: Creating Azure AI Search service with system-managed identity...${NC}"
az search service create \
    --name $SEARCH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku basic \
    --identity-type SystemAssigned \
    --location $LOCATION \
    --output none

echo -e "${GREEN}✓ AI Search service created${NC}"

# Get the principal ID of the search service managed identity
echo "Getting search service managed identity..."
SEARCH_PRINCIPAL_ID=$(az search service show \
    --name $SEARCH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query identity.principalId \
    -o tsv)

echo "Search Service Principal ID: $SEARCH_PRINCIPAL_ID"
echo ""

#################################################
# Step 3: Create Storage Account
#################################################
echo -e "${YELLOW}Step 3: Creating storage account...${NC}"

# Check if storage account already exists
if az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "Storage account already exists, skipping creation..."
else
    az storage account create \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --allow-blob-public-access false \
        --output none
fi

echo -e "${GREEN}✓ Storage account ready${NC}"

# Get storage account resource ID
STORAGE_ACCOUNT_ID=$(az storage account show \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id \
    -o tsv)

echo "Storage Account ID: $STORAGE_ACCOUNT_ID"
echo ""

#################################################
# Step 4: Assign Storage Blob Data Reader role to AI Search
#################################################
echo -e "${YELLOW}Step 4: Assigning Storage Blob Data Reader role to AI Search...${NC}"

# Wait a bit for the managed identity to propagate
if [ "$NO_WAIT" = false ]; then
    echo "Waiting 30 seconds for managed identity to propagate..."
    sleep 30
else
    echo "Skipping identity propagation wait (--nowait flag set)..."
fi

az role assignment create \
    --assignee $SEARCH_PRINCIPAL_ID \
    --role "Storage Blob Data Reader" \
    --scope $STORAGE_ACCOUNT_ID \
    --output none

echo -e "${GREEN}✓ Storage Blob Data Reader role assigned to AI Search${NC}"
echo ""

#################################################
# Step 5: Create Foundry Resource (AIServices)
#################################################
echo -e "${YELLOW}Step 5: Creating Foundry Resource...${NC}"

az cognitiveservices account create \
    --name $FOUNDRY_RESOURCE_NAME \
    --resource-group $RESOURCE_GROUP \
    --kind AIServices \
    --sku S0 \
    --location $LOCATION \
    --custom-domain $FOUNDRY_RESOURCE_NAME \
    --allow-project-management true \
    --yes \
    --output none

echo -e "${GREEN}✓ Foundry Resource created${NC}"

# Get Foundry resource ID
FOUNDRY_RESOURCE_ID=$(az cognitiveservices account show \
    --name $FOUNDRY_RESOURCE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id \
    -o tsv)

echo "Foundry Resource ID: $FOUNDRY_RESOURCE_ID"
echo ""

#################################################
# Step 6: Create Foundry Project
#################################################
echo -e "${YELLOW}Step 6: Creating Foundry Project...${NC}"

az cognitiveservices account project create \
    --name $FOUNDRY_RESOURCE_NAME \
    --project-name $FOUNDRY_PROJECT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

echo -e "${GREEN}✓ Foundry Project created${NC}"
echo ""

#################################################
# Summary
#################################################
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Deterministic Hash: $DETERMINISTIC_HASH"
echo ""
echo "Azure AI Search:"
echo "  - Service Name: $SEARCH_SERVICE_NAME"
echo "  - Endpoint: https://$SEARCH_SERVICE_NAME.search.windows.net"
echo "  - Principal ID: $SEARCH_PRINCIPAL_ID"
echo "  - Roles: Storage Blob Data Reader on storage account"
echo ""
echo "Storage Account:"
echo "  - Name: $STORAGE_ACCOUNT_NAME"
echo "  - Resource ID: $STORAGE_ACCOUNT_ID"
echo ""
echo "Microsoft Foundry:"
echo "  - Resource Name: $FOUNDRY_RESOURCE_NAME"
echo "  - Project Name: $FOUNDRY_PROJECT_NAME"
echo "  - Resource ID: $FOUNDRY_RESOURCE_ID"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Enable semantic ranker on AI Search (required for Foundry IQ)"
echo "2. Create a knowledge source in AI Search"
echo "3. Create a knowledge base in AI Search"
echo "4. Connect the knowledge base to your Foundry project"
echo ""
echo "For more information, see: /Users/geertbaeke/projects/agui/foundry/foundryiq.md"
echo ""
