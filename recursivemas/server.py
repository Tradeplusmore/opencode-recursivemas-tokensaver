"""
Wrapper FastAPI per esporre RecursiveMAS come endpoint OpenAI-compatible.
Versione corretta: v1.1.0 (allineata alla repo ufficiale RecursiveMAS/RecursiveMAS)

Repo ufficiale: https://github.com/RecursiveMAS/RecursiveMAS
Layout reale: inference/system_loader.py, inference/run.py (CLI eval), inference/inference_utils/,
  inference/load_from_repo.py (STYLE_SPECS), inference/prompts.py, train/

Setup MAS vera:
    git clone https://github.com/RecursiveMAS/RecursiveMAS.git
    set MAS_REPO=C:\path\RecursiveMAS
    set MAS_STYLE=sequential_scaled  (keys reali: sequential_light, sequential_scaled, mixture, distillation, deliberation)
    set MAS_DATASET=math500  (math500, medqa, gpqa, mbppplus, aime25, aime26, livecodebench, bamboogle, hotpotqa)
    python server.py

NOTA ONESTA: run.py ufficiale e' un harness eval su dataset, NON ha una API a singola domanda.
La funzione run_single_question() sotto e' l'ADATTATORE da completare usando
inference/prompts.py + inference/inference_utils/inference_mas*.py. Senza, il server
carica il sistema reale ma risponde 501 con istruzioni. Il sistema text-level
(router+MCP+agent, senza GPU) resta il default per l'uso quotidiano.
"""
import os
import sys
import time
from typing import List, Optional

MAS_REPO = os.getenv("MAS_REPO", "")
if MAS_REPO:
    sys.path.insert(0, MAS_REPO)
    sys.path.insert(0, os.path.join(MAS_REPO, "inference"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import REALI (repo ufficiale): inference/system_loader.py -> load_mas_system(style, dataset, *, device, ...)
try:
    from system_loader import load_mas_system  # funziona se MAS_REPO/inference e' in sys.path
    _import_err = None
except ImportError as e:
    try:
        from inference.system_loader import load_mas_system  # fallback se MAS_REPO root e' in path
        _import_err = None
    except ImportError as e2:
        print(f"AVVISO: RecursiveMAS ufficiale non trovata ({e2}). Clona la repo e imposta MAS_REPO.")
        load_mas_system = None
        _import_err = str(e2)

app = FastAPI(
    title="RecursiveMAS Wrapper",
    description="Endpoint OpenAI-compatible per delegare ragionamento complesso a RecursiveMAS",
    version="1.1.0",
)

MODEL_STYLE_MAP = {
    "sequential-scaled": "sequential_scaled",
    "sequential-light": "sequential_light",
    "mixture": "mixture",
    "distillation": "distillation",
    "deliberation": "deliberation",
}

MAS_STYLE = os.getenv("MAS_STYLE", "sequential_scaled")
MAS_DATASET = os.getenv("MAS_DATASET", "math500")
MAS_DEVICE = os.getenv("MAS_DEVICE", "cuda")

mas_system = None


def run_single_question(mas, question: str, temperature: float, max_tokens: int) -> str:
    """ADATTATORE singola-domanda (DA COMPLETARE sulla repo ufficiale).
    run.py e' solo CLI eval su dataset; qui va costruito il giro singolo usando:
      - inference/prompts.py (prompt di ruolo planner/critic/solver per style+dataset)
      - inference/inference_utils/inference_mas*.py (recursione su hidden states)
    Solleva NotImplementedError finche' non lo colleghi: il server risponde 501 onesto."""
    raise NotImplementedError(
        "run_single_question() non collegata: usa inference/prompts.py + "
        "inference/inference_utils/inference_mas*.py della repo ufficiale per costruire "
        "il giro planner->critic->solver sulla domanda. Vedi MAS_REPO/inference/."
    )


def get_mas_system():
    global mas_system
    if mas_system is None:
        if load_mas_system is None:
            raise RuntimeError(
                f"Repo ufficiale non trovata ({_import_err}). "
                "git clone https://github.com/RecursiveMAS/RecursiveMAS.git e imposta MAS_REPO."
            )
        print(f"Caricamento RecursiveMAS stile={MAS_STYLE} dataset={MAS_DATASET} device={MAS_DEVICE}")
        mas_system = load_mas_system(style=MAS_STYLE, dataset=MAS_DATASET, device=MAS_DEVICE, trust_remote_code=True)
        print("Sistema MAS caricato.")
    return mas_system


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.6
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mas_loaded": mas_system is not None,
            "style": MAS_STYLE, "device": MAS_DEVICE}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    if req.stream:
        raise HTTPException(status_code=400, detail="stream:true non supportato. Usa stream:false.")
    if load_mas_system is None:
        raise HTTPException(status_code=500, detail="Repo ufficiale non trovata. Clona RecursiveMAS e imposta MAS_REPO.")
    requested_style = MODEL_STYLE_MAP.get(req.model, MAS_STYLE)
    _ = requested_style  # usato nel log; il sistema caricato resta MAS_STYLE (singleton). Riavvia con MAS_STYLE diverso per cambiare.
    mas = get_mas_system()

    user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), None)
    if not user_msg:
        raise HTTPException(status_code=400, detail="Nessun messaggio utente trovato")
    # Protezioni: limita input e budget per evitare abusi/DoS (solo localhost, ma difendiamoci comunque)
    user_msg = user_msg[:8000]
    max_tok = min(max(req.max_tokens or 512, 1), 2048)
    temp = min(max(req.temperature if req.temperature is not None else 0.6, 0.0), 1.5)
    print(f"Richiesta model={req.model} style={requested_style}: {user_msg[:120]}...")

    try:
        final_answer = run_single_question(mas, user_msg, temp, max_tok)
    except NotImplementedError as e:
        print(f"Adattatore da completare: {e}")
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        print(f"Errore inferenza: {e}")
        # Dettaglio interno solo nei log, al client messaggio generico (no info disclosure)
        raise HTTPException(status_code=500, detail="Inferenza MAS fallita. Controlla i log del server.")

    return {
        "id": f"recursivemas-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": final_answer}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


if __name__ == "__main__":
    print("=" * 60)
    print("RecursiveMAS Wrapper  v1.0.1")
    print(f"Stile: {MAS_STYLE}  Device: {MAS_DEVICE}")
    print("Endpoint: http://127.0.0.1:8001/v1/chat/completions")
    print("Health:   http://127.0.0.1:8001/health")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8001)
