"""Pipeline ruoli RecursiveMAS su CPU via Ollama — ZERO GPU (locale o remota).

Esegue planner -> critic/refiner -> solver come 3 chiamate reali a modelli
distinti (o stesso modello con prompt di ruolo), con i prompt ufficiali
testuali (code_pipeline.py). Sostituisce il canale latente con testo:
perde la recursione hidden-state, mantiene specializzazione e struttura.

Uso:
    ollama serve
    python cpu_roles_pipeline.py --planner gemma3:4b --critic gemma3:4b --solver gemma3:4b "domanda"
    python cpu_roles_pipeline.py --code --planner gemma3:4b --critic gemma3:4b --solver gemma3:4b "problema"

Con i pesi-ruolo ufficiali convertiti in GGUF (scripts/setup-cpu-roles.*):
    --planner recursivemas-planner --critic recursivemas-critic --solver recursivemas-solver
"""
import argparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import urllib.request
import json

OLLAMA_URL = "http://127.0.0.1:11434"


def chat(model: str, prompt: str, num_predict: int = 400, temperature: float = 0.4) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"num_predict": num_predict, "temperature": temperature}}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode()).get("response", "").strip()


def run_pipeline(question: str, planner_m: str, critic_m: str, solver_m: str, code: bool = False) -> str:
    if code:
        from code_pipeline import code_planner_prompt, code_refiner_prompt, code_solver_prompt
        plan = chat(planner_m, code_planner_prompt(question), 300)
        refined = chat(critic_m, code_refiner_prompt(question, plan), 350)
        answer = chat(solver_m, code_solver_prompt(question, refined), 600)
    else:
        plan = chat(planner_m,
                    f"You are a planner agent. Break this into 3-5 steps (1 line each), no solution:\n{question}", 250)
        refined = chat(critic_m,
                       f"You are a critic agent. Question: {question}\nPlan:\n{plan}\n"
                       "List 1 risk per step (1 line each), then give the corrected plan.", 300)
        answer = chat(solver_m,
                      f"You are a solver agent. Question: {question}\nCorrected plan:\n{refined}\n"
                      "Solve following the plan. End with RISULTATO: in 2 lines.", 500)
    return f"### PLAN\n{plan}\n\n### CRITIC/REFINED\n{refined}\n\n### SOLVE\n{answer}\n"


def main():
    ap = argparse.ArgumentParser(description="Pipeline ruoli CPU via Ollama (no GPU)")
    ap.add_argument("question", nargs="*", help="domanda")
    ap.add_argument("--planner", default="recursivemas-planner")
    ap.add_argument("--critic", default="recursivemas-critic")
    ap.add_argument("--solver", default="recursivemas-solver")
    ap.add_argument("--code", action="store_true")
    args = ap.parse_args()
    q = " ".join(args.question).strip()
    if not q:
        print("Uso: python cpu_roles_pipeline.py [--code] [--planner M --critic M --solver M] \"domanda\"")
        sys.exit(1)
    try:
        print(run_pipeline(q, args.planner, args.critic, args.solver, args.code))
    except Exception as e:
        print(f"Errore Ollama ({e}). Avvia prima: ollama serve", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
