"""
MCP server RecursiveMAS per OpenCode (protocollo MCP su stdio).
Espone 2 tool:
  - call_recursivemas(question, style): delega al wrapper FastAPI locale
  - plan_critic_solve(question): restituisce il prompt 3-step text-level (0 token extra)

Install:
    pip install mcp requests

Registrazione in opencode.json:
    { "mcp": { "recursivemas": { "type": "local", "command": ["python", "mcp-recursivemas.py"], "enabled": true } } }
"""
import os
import requests

BASE_URL = os.getenv("RECURSIVEMAS_URL", "http://127.0.0.1:8001/v1")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Manca il pacchetto 'mcp'. Installa con: pip install mcp requests")
    raise SystemExit(1)

mcp = FastMCP("recursivemas")


@mcp.tool()
def call_recursivemas(question: str, style: str = "sequential-scaled") -> str:
    """Delega problemi di ragionamento complesso a RecursiveMAS (wrapper locale)."""
    style = style if style in ("sequential-scaled", "sequential-light") else "sequential-scaled"
    question = question.strip()[:8000]  # limite anti-abuso
    if not (BASE_URL.startswith("http://127.0.0.1") or BASE_URL.startswith("http://localhost")):
        if os.getenv("ALLOW_REMOTE_MAS") != "1":
            return f"BASE_URL non locale ({BASE_URL}). Imposta ALLOW_REMOTE_MAS=1 per abilitarlo."
    max_tokens = 512 if style == "sequential-light" else 1024
    try:
        r = requests.post(f"{BASE_URL}/chat/completions",
                          json={"model": style, "messages": [{"role": "user", "content": question}],
                                "max_tokens": max_tokens, "stream": False}, timeout=120)
        r.raise_for_status()
        return "🔍 Delegato a RecursiveMAS:\n\n" + r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Errore RecursiveMAS ({e}). Assicurati che server.py sia attivo su {BASE_URL}."


@mcp.tool()
def plan_critic_solve(question: str, track: str = "general") -> str:
    """Prompt planner->refiner/critic->solver a budget ridotto (testuale, gratis).
    track: general | code | math | deliberation (wording ufficiale RecursiveMAS, testuale)."""
    q = question.strip()[:4000]
    if track == "code":
        return (
            "You are a planner agent in a multi-agent coding system. "
            f"Problem: {q} Provide a step-by-step plan (3-6 steps). Do not write code. "
            "Then act as refiner: refine it (3-6 steps, no code). "
            "Then as solver: final code in ONE markdown block."
        )
    if track == "math":
        return (
            "You are the math expert in a multi-agent system. "
            f"Question: {q} Solve and put the final answer inside \\boxed{{}}, e.g. \\boxed{{1}}."
        )
    if track == "deliberation":
        return (
            "Reason step by step. For external facts use available tools, reporting "
            f"<search>q</search>/<result>r</result>; for compute use scripts as <python>code</python>/<result>out</result>. "
            f"Question: {q} Close with exact answer in \\boxed{{}}."
        )
    q = question.strip()[:4000]
    return (
        "Applica RECURSIVE (planner->critic->solver). Planner max 5 righe, Critic max 5 righe, "
        f"Solver max 15 righe. Niente ripetizioni.\n\nDOMANDA:\n{q}\n\nFORMATO: 1) PLAN 2) CRITIC 3) SOLVE + RISULTATO in 2 righe."
    )


if __name__ == "__main__":
    mcp.run()
