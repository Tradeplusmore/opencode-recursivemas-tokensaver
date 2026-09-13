"""
Smart Router RecursiveMAS per OpenCode — risparmia token + migliora qualità.
Logica replicata (text-level, senza GPU):
  PLANNER -> CRITIC -> SOLVER, con budget token stretti + routing selettivo + cache.

Uso:
  python opencode-router.py "Dimostra che sqrt(2) e' irrazionale"
  python opencode-router.py --cheap "Calcola 23 x 47"
  python opencode-router.py --deep "Problema di ottimizzazione ..."
  python opencode-router.py --prompt-only "spiega ..."   # stampa solo il prompt 3-step, 0 chiamate
  python opencode-router.py --no-cache "domanda"

Richiede (solo se deve delegare davvero):
  server.py attivo su http://127.0.0.1:8001  (oppure variabile RECURSIVEMAS_URL)
"""
import argparse
import hashlib
import json
import os
import re
import sys

try:
    import requests
except ImportError:
    print("Installa requests: pip install requests")
    sys.exit(1)

BASE_URL = os.getenv("RECURSIVEMAS_URL", "http://127.0.0.1:8001/v1")
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".recursivemas_cache.json")

COMPLEX_PATTERNS = [
    r"\bdimostra\b", r"\bprova che\b", r"\bteorema\b", r"\bintegrale\b", r"\bderivata\b",
    r"\bequazione\b", r"\bottimizz", r"\bprobabilit", r"\bmatrice\b", r"\bautovalor",
    r"\bfisica\b", r"\bchimica\b", r"\bquantistic", r"\beigen", r"\blimite\b",
    r"\bcalcola\b.{40,}", r"\brisolvi\b", r"\btrova tutti\b", r"\bdetermina se\b",
    r"\binduzione\b", r"\bcontraddizione\b", r"\bricorrenza\b", r"\bcomplessit",
    r"\bdebugga\b.{60,}", r"\brefactor\b.{60,}",
]
SIMPLE_PATTERNS = [
    r"^(ciao|grazie|ok|si|no)[.!]?$",
    r"^traduci\b", r"^riassumi\b", r"^spiega (cos'è|cosa significa)",
    r"^scrivi una (email|lettera|bio)",
]


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def classify(question: str) -> str:
    q = question.strip().lower()
    if len(q) < 30:
        for p in SIMPLE_PATTERNS:
            if re.search(p, q):
                return "simple"
    for p in COMPLEX_PATTERNS:
        if re.search(p, q, re.IGNORECASE):
            return "complex"
    # euristica lunghezza: problemi lunghi e strutturati -> complessi
    if len(q) > 400 or q.count("?") >= 2 or len(re.findall(r"\d+", q)) >= 5:
        return "complex"
    return "medium"


def compress(text: str, max_chars: int = 4000) -> str:
    t = re.sub(r"[ \t]+", " ", text).strip()
    t = re.sub(r"\n{3,}", "\n\n", t)
    if len(t) > max_chars:
        return t[:max_chars] + f"\n\n[...troncato {len(t)-max_chars} caratteri per risparmiare token...]"
    return t


def build_recursive_prompt(question: str, budget: str = "cheap") -> str:
    """Prompt 3-step text-level che replica la logica RecursiveMAS dentro OpenCode.
    Budget cheap = risposte corte forzate -> meno token."""
    if budget == "cheap":
        limits = "Planner: max 5 righe. Critic: max 5 righe. Solver: max 15 righe. Niente ripetizioni."
    else:
        limits = "Planner: max 8 punti. Critic: max 8 punti. Solver: soluzione completa ma senza divagazioni."
    return f"""Applica il protocollo RECURSIVE (planner->critic->solver) alla domanda sotto. {limits}

DOMANDA:
{compress(question)}

FORMATO OBBLIGATORIO:
1) PLAN: scomponi in 3-5 sotto-problemi numerati.
2) CRITIC: per ogni punto indica 1 rischio/buco possibile in 1 riga.
3) SOLVE: risolvi seguendo il plan, correggendo i buchi. Chiudi con 'RISULTATO:' in 2 righe max.
Se la domanda e' banale, salta CRITIC e rispondi in 5 righe."""


def cache_get(key: str):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(key)
    except Exception:
        return None


def cache_set(key: str, value: str):
    data = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[key] = value[:8000]  # non gonfiare la cache con risposte enormi
    # tieni cache leggera: max 200 voci
    if len(data) > 200:
        for k in list(data.keys())[: len(data) - 200]:
            del data[k]
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    try:
        os.chmod(CACHE_FILE, 0o600)  # solo proprietario (puo' contenere prompt sensibili)
    except Exception:
        pass


def call_mas(question: str, style: str, max_tokens: int, timeout: int = 120) -> str:
    # Protezione SSRF: di default solo localhost. Per URL remoti imposta ALLOW_REMOTE_MAS=1 consapevolmente.
    if not (BASE_URL.startswith("http://127.0.0.1") or BASE_URL.startswith("http://localhost")):
        if os.getenv("ALLOW_REMOTE_MAS") != "1":
            raise RuntimeError(f"BASE_URL non locale ({BASE_URL}). Imposta ALLOW_REMOTE_MAS=1 per abilitarlo.")
    url = f"{BASE_URL}/chat/completions"
    payload = {"model": style, "messages": [{"role": "user", "content": question}],
               "max_tokens": max_tokens, "stream": False}
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser(description="Smart Router RecursiveMAS per OpenCode")
    ap.add_argument("question", nargs="*", help="domanda da risolvere")
    ap.add_argument("--cheap", action="store_true", help="forza sequential-light + 512 token")
    ap.add_argument("--deep", action="store_true", help="forza sequential-scaled + 2048 token")
    ap.add_argument("--prompt-only", action="store_true", help="stampa solo il prompt 3-step, nessuna chiamata")
    ap.add_argument("--code", action="store_true", help="pipeline code ufficiale planner->refiner->solver (testuale, no GPU)")
    ap.add_argument("--local", action="store_true", help="pipeline ruoli reale su CPU via Ollama (gemma3:4b default, 0 token API, ~1-2 min)")
    ap.add_argument("--no-cache", action="store_true", help="ignora cache")
    ap.add_argument("--max-chars", type=int, default=4000)
    args = ap.parse_args()

    question = " ".join(args.question).strip()
    if not question:
        print("Uso: python opencode-router.py \"domanda\" [--cheap|--deep|--prompt-only]")
        sys.exit(1)
    question = compress(question, args.max_chars)
    kind = classify(question)
    est = estimate_tokens(question)
    print(f"[router] tipo={kind} token-stimati-input~{est}", file=sys.stderr)

    # 1) Domande semplici: NON chiamare MAS, usa prompt corto -> risparmi tutto
    if kind == "simple" and not args.deep:
        print(build_recursive_prompt(question, budget="cheap"))
        print("\n[router] domanda semplice: incolla il prompt sopra in OpenCode, nessuna chiamata MAS.", file=sys.stderr)
        return

    if args.local:
        import subprocess
        mods = [os.getenv("OLLAMA_PLANNER", "gemma3:4b"), os.getenv("OLLAMA_CRITIC", "gemma3:4b"),
                os.getenv("OLLAMA_SOLVER", "gemma3:4b")]
        cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
               "cpu_roles_pipeline.py"), "--planner", mods[0], "--critic", mods[1],
               "--solver", mods[2]] + (["--code"] if args.code else []) + [question]
        print(f"[router] LOCAL-CPU: 3 chiamate Ollama ({'/'.join(mods)}), gratis, ~1-2 min...", file=sys.stderr)
        r = subprocess.run(cmd, capture_output=False)
        sys.exit(r.returncode)
        try:
            from code_pipeline import (code_planner_prompt, code_refiner_prompt, code_solver_prompt)
        except ImportError:
            from recursivemas.code_pipeline import (  # uso globale
                code_planner_prompt, code_refiner_prompt, code_solver_prompt)
        print("=" * 20 + " FASE 1/3: PLANNER (incolla in OpenCode, output -> fase 2) " + "=" * 20)
        print(code_planner_prompt(question))
        print("\n" + "=" * 20 + " FASE 2/3: REFINER (incolla output planner in <PLANNER_OUT>) " + "=" * 20)
        print(code_refiner_prompt(question, "<PLANNER_OUT>"))
        print("\n" + "=" * 20 + " FASE 3/3: SOLVER (incolla output refiner in <REFINED_PLAN>) " + "=" * 20)
        print(code_solver_prompt(question, "<REFINED_PLAN>"))
        return
        print(build_recursive_prompt(question, budget="deep" if args.deep else "cheap"))
        return

    # 2) Scelta stile in base a complessità
    if args.deep:
        style, max_tokens = "sequential-scaled", 2048
    elif args.cheap or kind == "medium":
        style, max_tokens = "sequential-light", 512
    else:
        style, max_tokens = "sequential-scaled", 1024  # complex ma con budget ridotto di default

    key = hashlib.sha256(f"{style}:{question}".encode()).hexdigest()[:32]
    if not args.no_cache:
        hit = cache_get(key)
        if hit:
            print(f"[router] CACHE HIT -> 0 token spesi (risparmiati ~{estimate_tokens(hit)}).", file=sys.stderr)
            print(hit)
            return

    # 3) Delega reale al wrapper
    try:
        answer = call_mas(build_recursive_prompt(question) if kind != "complex" else question,
                          style, max_tokens)
    except Exception as e:
        print(f"[router] MAS non raggiungibile ({e}). Fallback: uso prompt 3-step locale.", file=sys.stderr)
        print(build_recursive_prompt(question, budget="cheap"))
        return

    if not args.no_cache:
        cache_set(key, answer)
    print(answer)


if __name__ == "__main__":
    main()
