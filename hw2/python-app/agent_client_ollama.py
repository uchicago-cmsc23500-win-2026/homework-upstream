"""Ollama-based client for interactive board game recommendations.

Implements an interactive chat client that uses an Ollama LLM to process
user queries about board game recommendations. Converts MCP tools to OpenAI
tool format and manages multi-turn conversations with tool execution.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

import requests
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

DEFAULT_OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
console = Console()

SEARCH_LIMIT = 10

def start_server() -> subprocess.Popen:
    """Start the MCP server as a subprocess.
    
    Launches the server.py module in a separate process with stdin/stdout
    piping configured for JSON-RPC communication.
    
    Returns:
        Popen object for the server process.
        
    Raises:
        FileNotFoundError: If Python interpreter or server module not found.
    """
    # Open log file for server stderr
    log_file = open('mcp_server.log', 'a')
    
    return subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=log_file,
        text=True,
        env=os.environ.copy(),
        bufsize=1,
    )


def rpc(proc: subprocess.Popen, id_: int, method: str, params: Dict[str, Any]) -> Any:
    """Send JSON-RPC request to MCP server and receive response.
    
    Writes a JSON-RPC 2.0 request to the server process and reads back
    the response. Handles errors in response.
    
    Args:
        proc: MCP server process.
        id_: Request ID (must be unique within session).
        method: JSON-RPC method name (e.g., "tools/list", "tools/call").
        params: Method parameters dictionary.
        
    Returns:
        The result field from the JSON-RPC response.
        
    Raises:
        RuntimeError: If server doesn't respond or returns error.
        json.JSONDecodeError: If response is invalid JSON.
    """
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":id_,"method":method,"params":params}) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("No response from MCP server")
    resp = json.loads(line)
    if "error" in resp:
        raise RuntimeError(resp["error"])
    return resp["result"]


def to_openai_tools(mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert MCP tool format to OpenAI tool format.
    
    Transforms MCP tool definitions into OpenAI's function calling format,
    required for compatibility with Ollama's function calling support.
    
    Args:
        mcp_tools: List of MCP tool definitions with name, description,
            and inputSchema.
            
    Returns:
        List of OpenAI-format tool definitions:
        [
            {
                "type": "function",
                "function": {
                    "name": "...",
                    "description": "...",
                    "parameters": {...}
                }
            },
            ...
        ]
    """
    out = []
    for t in mcp_tools:
        out.append({
            "type":"function",
            "function":{
                "name": t["name"],
                "description": t.get("description",""),
                "parameters": t.get("inputSchema", {"type":"object","properties":{}}),
            }
        })
    return out


def chat(url: str, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send chat request to Ollama with tool availability.
    
    Makes an HTTP request to Ollama API with the conversation history
    and available tools. Uses temperature=0 for deterministic tool choice.
    Shows loading spinner during processing.
    
    Args:
        url: Ollama API endpoint URL.
        model: Model name (e.g., "qwen2.5:3b-instruct").
        messages: Conversation history as list of message dicts
            with "role" and "content".
        tools: List of tools in OpenAI format.
        
    Returns:
        Assistant message dict with optional "tool_calls" field if tools
        are to be executed.
        
    Raises:
        requests.RequestException: If HTTP request fails.
        json.JSONDecodeError: If response is invalid JSON.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Thinking...", total=None)
        r = requests.post(url, json={
            "model": model,
            "messages": messages,
            "temperature": 0,
            "tools": tools,
            "tool_choice": "auto",
        }, timeout=120)
        progress.stop()
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def main() -> None:
    """Run the interactive Ollama-based recommendation client.
    
    Parses command-line arguments for model and URL, starts the MCP server,
    lists available tools, and enters an interactive loop for user queries.
    
    Manages multi-turn conversations where:
    1. User provides query
    2. LLM decides which tool(s) to call
    3. Tools are executed via MCP
    4. Results are fed back to LLM
    5. LLM provides final response or calls more tools
    
    Prefers recommendation flow: find seed -> get profile -> candidates ->
    score_and_diversify -> fetch_game_cards.
    
    Exits on KeyboardInterrupt (Ctrl+C).
    
    Requires:
        - Database credentials set via environment variables:
          DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
        - Ollama running at specified URL
        - OLLAMA_MODEL env var or --model argument for model name
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("OLLAMA_MODEL","qwen2.5:3b-instruct"))
    ap.add_argument("--url", default=os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL))
    args = ap.parse_args()
    
    debug_mode = os.environ.get("AGENT_DEBUG", "").lower() in ("1", "true", "yes")

    if not all([os.environ.get("DB_HOST"), os.environ.get("DB_NAME"),
                os.environ.get("DB_USER"), os.environ.get("DB_PASSWORD")]):
        print("Database credentials not set. Required: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD", file=sys.stderr)
        sys.exit(2)

    proc = start_server()
    try:
        mcp_tools = rpc(proc, 1, "tools/list", {})
        tools = to_openai_tools(mcp_tools)

        system = (
            "You are a boardgame recommendation assistant. Use tools to access a boardgame database. "
            "Workflow for game seed: get_games_by_name -> get_game_profile -> extract category/designer IDs -> candidate_by_categories/designers -> score_candidates -> fetch_game_cards. "
            "Workflow for category/designer: search_categories/designers -> extract IDs -> candidate_by_categories/designers -> score_candidates -> fetch_game_cards. "
            "Always show game/category/designer names to user, never IDs."
            )

        messages: List[Dict[str, Any]] = [{"role":"system","content":system}]
        print("Ollama client ready. Example: Recommend games like \"Risk\" for 2 players under 60 minutes. Press Ctrl+C to Quit..")
        while True:
            try:
                q = input("\nYou> ").strip()
            except KeyboardInterrupt:
                break
            if not q:
                continue
            messages.append({"role":"user","content":q})
            
            for step in range(20):
                msg = chat(args.url, args.model, messages, tools)
                
                if msg.get("content") and debug_mode:
                    console.print(f"[dim italic]{msg.get('content')}[/dim italic]")
                
                if msg.get("tool_calls"):
                    tc = msg["tool_calls"][0]
                    fn = tc.get("function", {})
                    name = fn.get("name")
                    raw = fn.get("arguments", "{}")
                    try:
                        arguments = json.loads(raw) if isinstance(raw, str) else (raw or {})
                    except (json.JSONDecodeError, ValueError):
                        arguments = {}
                    
                    if debug_mode:
                        console.print(f"[dim italic]Tool Called: {name} with arguments: {arguments}[/dim italic]")
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[progress.description]Calling {name}..."),
                        console=console,
                    ) as progress:
                        progress.add_task("", total=None)
                        result = rpc(proc, 100+step, "tools/call", {"name":name,"arguments":arguments})
                    
                    if debug_mode:
                        console.print(f"[dim italic]Tool Response: {result}[/dim italic]")
                    
                    messages.append(msg)
                    messages.append({"role":"tool","name":name,"content":json.dumps(result)})
                else:
                    # No tool calls - final response
                    if msg.get("content"):
                        print("\nAssistant>\n" + msg.get("content"))
                        messages.append({"role":"assistant","content":msg.get("content")})
                    break
    finally:
        proc.kill()


if __name__ == "__main__":
    main()

