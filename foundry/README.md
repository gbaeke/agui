# Query Azure AI Foundry Knowledge Base

A concise Python script to query Azure AI Foundry knowledge bases and return full JSON responses.

## Setup

1. Install dependencies:
```bash
uv pip install azure-search-documents==11.7.0b2 azure-identity
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Azure Search endpoint and credentials
```

## Usage

### Direct Python:
```bash
uv run python query_kb.py
```

### Using the wrapper script:
```bash
./query_kb.sh "What information is available?"
```

## Configuration

Set these environment variables in `.env`:

- `AZURE_SEARCH_ENDPOINT` - Your Azure AI Search endpoint (required)
- `KNOWLEDGE_BASE_NAME` - Knowledge base name (default: "agent-knowledge")
- `AZURE_SEARCH_API_KEY` - API key (optional, uses managed identity if not set)
- `QUERY` - Default query text

## SDK Version

Requires **azure-search-documents >= 11.7.0b2** (preview) for knowledge base support.
