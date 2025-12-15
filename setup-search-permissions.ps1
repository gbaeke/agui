# Quick setup script for Azure AI Search & Storage permissions

Write-Host "🔐 Azure AI Search & Storage Permissions Setup" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if logged in
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Host "✓ Logged in to Azure CLI as: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Azure CLI. Please run: az login" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Prompt for required information
$SUBSCRIPTION_ID = "8e634b7c-a328-47ad-8df7-721035f015e6"
$RESOURCE_GROUP = "rg-ai-shared"
$SEARCH_SERVICE_NAME = "sserv"
$STORAGE_ACCOUNT_NAME = "schindex"
# Optional: Foundry (Azure OpenAI / Cognitive Services) account for embeddings
$FOUNDRY_ACCOUNT_NAME = Read-Host "Foundry (Azure OpenAI) Account Name [leave blank to skip]"
$FOUNDRY_RESOURCE_GROUP = if ([string]::IsNullOrWhiteSpace($FOUNDRY_ACCOUNT_NAME)) { "" } else { Read-Host "Foundry Resource Group (enter to reuse $RESOURCE_GROUP)" }
if (-not [string]::IsNullOrWhiteSpace($FOUNDRY_ACCOUNT_NAME) -and [string]::IsNullOrWhiteSpace($FOUNDRY_RESOURCE_GROUP)) {
  $FOUNDRY_RESOURCE_GROUP = $RESOURCE_GROUP
}

Write-Host ""
Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "  Subscription: $SUBSCRIPTION_ID"
Write-Host "  Resource Group: $RESOURCE_GROUP"
Write-Host "  Search Service: $SEARCH_SERVICE_NAME"
Write-Host "  Storage Account: $STORAGE_ACCOUNT_NAME"
if (-not [string]::IsNullOrWhiteSpace($FOUNDRY_ACCOUNT_NAME)) {
  Write-Host "  Foundry Account: $FOUNDRY_ACCOUNT_NAME"
  Write-Host "  Foundry RG: $FOUNDRY_RESOURCE_GROUP"
}
Write-Host ""

$confirm = Read-Host "Proceed? (y/n)"
if ($confirm -ne "y") {
    exit 0
}

# Set subscription
Write-Host ""
Write-Host "🔄 Setting subscription..." -ForegroundColor Yellow
az account set --subscription $SUBSCRIPTION_ID

# Enable managed identity on search service
Write-Host "🔄 Enabling managed identity on search service..." -ForegroundColor Yellow
az search service update `
  --name $SEARCH_SERVICE_NAME `
  --resource-group $RESOURCE_GROUP `
  --identity-type SystemAssigned

# Get principal IDs
Write-Host "🔄 Getting principal IDs..." -ForegroundColor Yellow
$SEARCH_PRINCIPAL_ID = az search service show `
  --name $SEARCH_SERVICE_NAME `
  --resource-group $RESOURCE_GROUP `
  --query identity.principalId `
  --output tsv

$CURRENT_USER_ID = az ad signed-in-user show --query id --output tsv

Write-Host "  Search Principal ID: $SEARCH_PRINCIPAL_ID"
Write-Host "  Current User ID: $CURRENT_USER_ID"

# Get resource IDs
$STORAGE_ID = az storage account show `
  --name $STORAGE_ACCOUNT_NAME `
  --resource-group $RESOURCE_GROUP `
  --query id `
  --output tsv

$SEARCH_ID = az search service show `
  --name $SEARCH_SERVICE_NAME `
  --resource-group $RESOURCE_GROUP `
  --query id `
  --output tsv

$FOUNDRY_ID = $null
if (-not [string]::IsNullOrWhiteSpace($FOUNDRY_ACCOUNT_NAME)) {
  $FOUNDRY_ID = az cognitiveservices account show `
    --name $FOUNDRY_ACCOUNT_NAME `
    --resource-group $FOUNDRY_RESOURCE_GROUP `
    --query id `
    --output tsv
}

# Grant Storage Blob Data Reader to Search Service
Write-Host ""
Write-Host "🔄 Granting Storage Blob Data Reader to Search Service..." -ForegroundColor Yellow
try {
    az role assignment create `
      --role "Storage Blob Data Reader" `
      --assignee $SEARCH_PRINCIPAL_ID `
      --scope $STORAGE_ID `
      2>$null
} catch {
    Write-Host "  (Role may already exist)" -ForegroundColor Gray
}

Write-Host "✅ Search service can read blobs from storage" -ForegroundColor Green

# Grant Search Index Data Reader to current user
Write-Host ""
Write-Host "🔄 Granting Search Index Data Reader to your account..." -ForegroundColor Yellow
try {
    az role assignment create `
      --role "Search Index Data Reader" `
      --assignee $CURRENT_USER_ID `
      --scope $SEARCH_ID `
      2>$null
} catch {
    Write-Host "  (Role may already exist)" -ForegroundColor Gray
}

Write-Host "✅ You can read from search indexes" -ForegroundColor Green

# Grant Search Index Data Contributor to current user
Write-Host ""
Write-Host "🔄 Granting Search Index Data Contributor to your account..." -ForegroundColor Yellow
try {
    az role assignment create `
      --role "Search Index Data Contributor" `
      --assignee $CURRENT_USER_ID `
      --scope $SEARCH_ID `
      2>$null
} catch {
    Write-Host "  (Role may already exist)" -ForegroundColor Gray
}

Write-Host "✅ You can create/update search indexes" -ForegroundColor Green

# Grant Cognitive Services OpenAI User on Foundry to Search MI and current user (if provided)
if ($FOUNDRY_ID) {
  Write-Host ""
  Write-Host "🔄 Granting Cognitive Services OpenAI User on Foundry to Search MI..." -ForegroundColor Yellow
  try {
      az role assignment create `
        --role "Cognitive Services OpenAI User" `
        --assignee $SEARCH_PRINCIPAL_ID `
        --scope $FOUNDRY_ID `
        2>$null
  } catch {
      Write-Host "  (Role may already exist)" -ForegroundColor Gray
  }
  Write-Host "✅ Search service can call Foundry embeddings" -ForegroundColor Green

  Write-Host ""
  Write-Host "🔄 Granting Cognitive Services OpenAI User on Foundry to your account..." -ForegroundColor Yellow
  try {
      az role assignment create `
        --role "Cognitive Services OpenAI User" `
        --assignee $CURRENT_USER_ID `
        --scope $FOUNDRY_ID `
        2>$null
  } catch {
      Write-Host "  (Role may already exist)" -ForegroundColor Gray
  }
  Write-Host "✅ You can call Foundry embeddings" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update your .env file with:"
Write-Host "   AZURE_SEARCH_ENDPOINT=https://$SEARCH_SERVICE_NAME.search.windows.net"
Write-Host "   AZURE_SEARCH_INDEX_NAME=product-catalog"
Write-Host "   AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME"
Write-Host "   AZURE_STORAGE_CONTAINER_NAME=catalog-data"
if ($FOUNDRY_ID) {
  Write-Host "   AZURE_FOUNDRY_ENDPOINT=https://$FOUNDRY_ACCOUNT_NAME.cognitiveservices.azure.com"
  Write-Host "   AZURE_FOUNDRY_EMBEDDING_DEPLOYMENT=<your-embedding-deployment>"
}
Write-Host ""
Write-Host "2. Wait 5-10 minutes for permissions to propagate"
Write-Host ""
Write-Host "3. Upload your CSV to blob storage:"
Write-Host "   az storage blob upload ``"
Write-Host "     --account-name $STORAGE_ACCOUNT_NAME ``"
Write-Host "     --container-name catalog-data ``"
Write-Host "     --name updated_product_catalog.csv ``"
Write-Host "     --file updated_product_catalog.csv ``"
Write-Host "     --auth-mode login"
Write-Host ""
Write-Host "4. Run the indexer setup script"
