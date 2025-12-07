#!/bin/bash

#################################################
# Upload Documents to Azure Storage Script
# This script uploads PDFs from the docs folder
# to a 'docs' container in the storage account
#################################################

set -e  # Exit on error

# Configuration variables
RESOURCE_GROUP="rg-foundryiq-demo"  # Must match setup-foundry-iq.sh
DOCS_FOLDER="./docs"  # Local folder with PDFs
CONTAINER_NAME="docs"  # Container name in storage account

# Get subscription ID to calculate the same deterministic hash
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")

# Create deterministic hash (same logic as setup-foundry-iq.sh)
HASH_INPUT="${SUBSCRIPTION_ID}${RESOURCE_GROUP}"
DETERMINISTIC_HASH=$(echo -n "$HASH_INPUT" | md5 | cut -c1-8)

STORAGE_ACCOUNT_NAME="stfiq${DETERMINISTIC_HASH}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upload Documents to Azure Storage${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Container Name: $CONTAINER_NAME"
echo "Docs Folder: $DOCS_FOLDER"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed.${NC}"
    exit 1
fi

# Check if logged in
echo -e "${YELLOW}Checking Azure CLI login status...${NC}"
az account show &> /dev/null || {
    echo -e "${RED}Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
}

# Check if docs folder exists
if [ ! -d "$DOCS_FOLDER" ]; then
    echo -e "${RED}Error: Docs folder '$DOCS_FOLDER' does not exist.${NC}"
    exit 1
fi

# Count PDF files
PDF_COUNT=$(find "$DOCS_FOLDER" -type f -name "*.pdf" | wc -l | tr -d ' ')
if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No PDF files found in $DOCS_FOLDER${NC}"
    exit 0
fi

echo -e "${GREEN}Found $PDF_COUNT PDF file(s) to upload${NC}"
echo ""

#################################################
# Step 1: Check if storage account exists
#################################################
echo -e "${YELLOW}Step 1: Verifying storage account exists...${NC}"

if ! az storage account show \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>/dev/null; then
    echo -e "${RED}Error: Storage account '$STORAGE_ACCOUNT_NAME' not found in resource group '$RESOURCE_GROUP'.${NC}"
    echo -e "${YELLOW}Please run setup-foundry-iq.sh first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Storage account verified${NC}"
echo ""

#################################################
# Step 2: Assign Storage Blob Data Contributor role to current user
#################################################
echo -e "${YELLOW}Step 2: Assigning Storage Blob Data Contributor role...${NC}"

# Get current user's object ID
CURRENT_USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Get storage account resource ID
STORAGE_ACCOUNT_ID=$(az storage account show \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id \
    -o tsv)

# Assign role (idempotent)
az role assignment create \
    --assignee $CURRENT_USER_ID \
    --role "Storage Blob Data Contributor" \
    --scope $STORAGE_ACCOUNT_ID \
    --output none 2>/dev/null || echo "  Role assignment already exists or completed"

echo -e "${GREEN}✓ Role assigned${NC}"
echo ""

#################################################
# Step 3: Create container if it doesn't exist
#################################################
echo -e "${YELLOW}Step 3: Creating container '$CONTAINER_NAME' if needed...${NC}"

# Create container (idempotent - won't fail if exists)
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT_NAME \
    --auth-mode login \
    --output none 2>/dev/null || true

echo -e "${GREEN}✓ Container ready${NC}"
echo ""

#################################################
# Step 4: Upload PDF files
#################################################
echo -e "${YELLOW}Step 4: Uploading PDF files...${NC}"

# Upload each PDF file
UPLOAD_COUNT=0
find "$DOCS_FOLDER" -type f -name "*.pdf" | while read -r pdf_file; do
    filename=$(basename "$pdf_file")
    echo "  Uploading: $filename"
    
    az storage blob upload \
        --account-name $STORAGE_ACCOUNT_NAME \
        --container-name $CONTAINER_NAME \
        --name "$filename" \
        --file "$pdf_file" \
        --auth-mode login \
        --overwrite \
        --output none
    
    UPLOAD_COUNT=$((UPLOAD_COUNT + 1))
done

echo -e "${GREEN}✓ All PDF files uploaded${NC}"
echo ""

#################################################
# Step 5: List uploaded files
#################################################
echo -e "${YELLOW}Uploaded files in container:${NC}"
az storage blob list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --container-name $CONTAINER_NAME \
    --auth-mode login \
    --query "[].name" \
    --output table

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upload completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Container URL:${NC}"
echo "https://${STORAGE_ACCOUNT_NAME}.blob.core.windows.net/${CONTAINER_NAME}/"
