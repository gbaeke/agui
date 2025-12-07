#!/usr/bin/env python3
"""
Query Azure AI Foundry Knowledge Base
Requires: azure-search-documents>=11.7.0b2
"""
import json
import os
import sys
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def main():
    # Configuration from environment variables
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    knowledge_base_name = os.getenv("KNOWLEDGE_BASE_NAME", "agent-knowledge")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    query = os.getenv("QUERY", "What information is available in this knowledge base?")

    if not search_endpoint:
        raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")

    # Create client with appropriate credential
    if api_key:
        print("Using API Key authentication", file=sys.stderr)
        credential = AzureKeyCredential(api_key)
    else:
        print("Using DefaultAzureCredential (managed identity/az login)", file=sys.stderr)
        print("Make sure you're logged in: az login", file=sys.stderr)
        print("And have the 'Search Index Data Reader' role on the search service", file=sys.stderr)
        credential = DefaultAzureCredential()
    
    kb_client = KnowledgeBaseRetrievalClient(
        endpoint=search_endpoint,
        knowledge_base_name=knowledge_base_name,
        credential=credential,
    )

    # Build retrieval request
    request = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user",
                content=[KnowledgeBaseMessageTextContent(text=query)],
            )
        ],
        include_activity=True,
    )

    # Retrieve from knowledge base
    try:
        result = kb_client.retrieve(request)
        display_results(result)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("1. Ensure you're logged in: az login", file=sys.stderr)
        print("2. Verify you have the 'Search Index Data Reader' role", file=sys.stderr)
        print("3. Or set AZURE_SEARCH_API_KEY in .env file", file=sys.stderr)
        sys.exit(1)


def display_results(result):
    """Display results using rich formatting"""
    console = Console()
    result_dict = result.as_dict()
    
    # Display response content
    if result_dict.get("response"):
        for idx, resp in enumerate(result_dict["response"]):
            for content in resp.get("content", []):
                if content.get("type") == "text":
                    text = content.get("text", "")
                    
                    # Try to parse as JSON if it looks like an array
                    if text.startswith("["):
                        try:
                            chunks = json.loads(text)
                            console.print(f"\n[bold cyan]Response with {len(chunks)} chunks:[/bold cyan]")
                            
                            for chunk in chunks:
                                ref_id = chunk.get("ref_id", "?")
                                content_text = chunk.get("content", "")
                                
                                # Truncate long content
                                display_text = content_text[:100] + "..." if len(content_text) > 100 else content_text
                                
                                console.print(Panel(
                                    display_text,
                                    title=f"[yellow]Chunk {ref_id}[/yellow]",
                                    border_style="blue"
                                ))
                        except json.JSONDecodeError:
                            console.print(Panel(text[:100] + "..." if len(text) > 100 else text, title="Response"))
                    else:
                        console.print(Panel(text, title="[green]Response[/green]", border_style="green"))
    
    # Display activity
    if result_dict.get("activity"):
        console.print("\n[bold magenta]Activity Log:[/bold magenta]")
        activity_table = Table(show_header=True)
        activity_table.add_column("Step", style="cyan")
        activity_table.add_column("Type", style="yellow")
        activity_table.add_column("Time (ms)", justify="right", style="green")
        activity_table.add_column("Details", style="white")
        
        for activity in result_dict["activity"]:
            step = str(activity.get("id", ""))
            act_type = activity.get("type", "")
            elapsed = str(activity.get("elapsed_ms", ""))
            
            details = []
            if "input_tokens" in activity:
                details.append(f"in:{activity['input_tokens']}")
            if "output_tokens" in activity:
                details.append(f"out:{activity['output_tokens']}")
            if "reasoning_tokens" in activity:
                details.append(f"reasoning:{activity['reasoning_tokens']}")
            if "count" in activity:
                details.append(f"count:{activity['count']}")
            
            activity_table.add_row(step, act_type, elapsed, " ".join(details))
        
        console.print(activity_table)
    
    # Display references
    if result_dict.get("references"):
        console.print(f"\n[bold cyan]References ({len(result_dict['references'])}):[/bold cyan]")
        ref_table = Table(show_header=True)
        ref_table.add_column("ID", style="yellow")
        ref_table.add_column("Type", style="cyan")
        ref_table.add_column("Score", justify="right", style="green")
        ref_table.add_column("Source", style="blue")
        
        for ref in result_dict["references"]:
            ref_id = ref.get("id", "")
            ref_type = ref.get("type", "")
            score = f"{ref.get('reranker_score', 0):.3f}"
            source = ref.get("blob_url", "").split("/")[-1] if "blob_url" in ref else ""
            
            ref_table.add_row(ref_id, ref_type, score, source)
        
        console.print(ref_table)


if __name__ == "__main__":
    main()
