# Azure AI Search & Storage Permissions Setup

This guide shows you how to grant the necessary permissions for Azure AI Search to index blob storage data and for your application to query the search index.

## Prerequisites
- Azure CLI installed and logged in: `az login`
- Your subscription ID, resource group, search service name, and storage account name

## Step 1: Get Resource IDs

```bash
# Set your variables
SUBSCRIPTION_ID="<your-subscription-id>"
RESOURCE_GROUP="<your-resource-group>"
SEARCH_SERVICE_NAME="<your-search-service-name>"
STORAGE_ACCOUNT_NAME="<your-storage-account-name>"

# Get Search Service Principal ID (managed identity)
SEARCH_PRINCIPAL_ID=$(az search service show \
  --name $SEARCH_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId \
  --output tsv)

echo "Search Service Principal ID: $SEARCH_PRINCIPAL_ID"

# Get your current user/app principal ID (for development)
CURRENT_USER_ID=$(az ad signed-in-user show --query id --output tsv)
echo "Current User ID: $CURRENT_USER_ID"

# Or if using a service principal/managed identity for your app:
# APP_PRINCIPAL_ID=$(az identity show \
#   --name <your-managed-identity-name> \
#   --resource-group $RESOURCE_GROUP \
#   --query principalId \
#   --output tsv)
```

## Step 2: Grant Storage Blob Data Reader to Search Service

This allows the search service to read blobs from storage for indexing:

```bash
# Get storage account resource ID
STORAGE_ID=$(az storage account show \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

# Assign Storage Blob Data Reader role to Search Service
az role assignment create \
  --role "Storage Blob Data Reader" \
  --assignee $SEARCH_PRINCIPAL_ID \
  --scope $STORAGE_ID

echo "✓ Search service can now read blobs from storage"
```

## Step 3: Grant Search Index Data Reader to Your Application

This allows your app to query the search index:

```bash
# Get search service resource ID
SEARCH_ID=$(az search service show \
  --name $SEARCH_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

# Assign Search Index Data Reader to your app/user
az role assignment create \
  --role "Search Index Data Reader" \
  --assignee $CURRENT_USER_ID \
  --scope $SEARCH_ID

echo "✓ Your app can now read from search indexes"
```

## Step 4: Grant Search Index Data Contributor (Optional)

If your app needs to create/update indexes:

```bash
az role assignment create \
  --role "Search Index Data Contributor" \
  --assignee $CURRENT_USER_ID \
  --scope $SEARCH_ID

echo "✓ Your app can now create/update search indexes"
```

## Step 5: Grant Search Service Contributor (Optional)

If your app needs to manage the search service itself:

```bash
az role assignment create \
  --role "Search Service Contributor" \
  --assignee $CURRENT_USER_ID \
  --scope $SEARCH_ID

echo "✓ Your app can now manage the search service"
```

## Step 6: Enable Managed Identity on Search Service (if not enabled)

```bash
az search service update \
  --name $SEARCH_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --identity-type SystemAssigned
```

## Verification

Check role assignments:

```bash
# Verify storage access for search service
az role assignment list \
  --assignee $SEARCH_PRINCIPAL_ID \
  --scope $STORAGE_ID \
  --output table

# Verify search access for your app
az role assignment list \
  --assignee $CURRENT_USER_ID \
  --scope $SEARCH_ID \
  --output table
```

## For Production: Use Managed Identity

Replace `$CURRENT_USER_ID` with your app's managed identity:

```bash
# Create managed identity for your app
az identity create \
  --name agui-app-identity \
  --resource-group $RESOURCE_GROUP

# Get the principal ID
APP_PRINCIPAL_ID=$(az identity show \
  --name agui-app-identity \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

# Grant search permissions
az role assignment create \
  --role "Search Index Data Reader" \
  --assignee $APP_PRINCIPAL_ID \
  --scope $SEARCH_ID

# Update your app to use this identity
# (e.g., assign it to your App Service, Container App, etc.)
```

## Environment Variables

After setting up permissions, update your `.env`:

```bash
# Azure Search
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_INDEX_NAME=product-catalog

# Storage
AZURE_STORAGE_ACCOUNT_NAME=<your-storage-account>
AZURE_STORAGE_CONTAINER_NAME=catalog-data

# Authentication (use DefaultAzureCredential)
# No keys needed when using managed identity/RBAC
```

## Troubleshooting

**Error: "Authorization failed"**
- Wait 5-10 minutes for role assignments to propagate
- Verify principal IDs are correct
- Check if managed identity is enabled

**Error: "Forbidden"**
- Ensure you're logged in: `az login`
- Verify you have permissions to assign roles in the subscription

**Error: "Resource not found"**
- Check resource names and resource group are correct
- Ensure resources exist: `az search service show --name $SEARCH_SERVICE_NAME --resource-group $RESOURCE_GROUP`
