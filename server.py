# server.py

import os
import glob
from typing import Optional
from mcp.server.fastmcp import FastMCP
from scripts.recall.__main__ import recall_query
from auto import run_workflow
from clients import call_groq, call_anthropic, call_cursor, call_takashi

# Initialize the MCP server
mcp = FastMCP(name="observer", version="0.1.0")

@mcp.tool()
async def recall_logs(query: str) -> str:
    """
    Quick‐path: if it's a logs query, run recall_query directly.
    """
    try:
        return recall_query(query) or "(no logs found)"
    except Exception as e:
        return f"Error in recall_logs: {e}"

@mcp.tool()
async def summarize_recent(duration_seconds: int = 10) -> str:
    """
    Run run_workflow for N seconds then return the last JSON log.
    """
    run_workflow(duration_seconds)
    latest = sorted(glob.glob("logs/*.json"), key=os.path.getctime)[-1]
    with open(latest, encoding="utf-8") as f:
        return f.read()

@mcp.tool()
async def chat(
    query: str,
    model: Optional[str] = "groq"
) -> str:
    """
    Generic chat endpoint: if query maps to log tools, handle that,
    otherwise dispatch to the named LLM or API.
    """
    # 1) Preprocess: direct‐tool shortcuts
    tool, args = recall_query.__globals__['preprocess_user_query'](query)
    if tool in ("search_logs", "search_logs_timewindow"):
        return recall_query(query)

    # 2) Dispatch to the selected model/back‐end
    try:
        if model == "groq":
            return call_groq([{"role": "user", "content": query}])
        elif model == "anthropic":
            return call_anthropic(query)
        elif model == "cursor":
            return call_cursor(query)
        elif model == "takashi":
            return call_takashi(query)
        else:
            return f"Unknown model '{model}'. Valid: groq, anthropic, cursor, takashi."
    except Exception as e:
        return f"Error calling {model}: {e}"

if __name__ == "__main__":
    # serve over stdio
    mcp.run(transport="stdio")
