"""
Wrapper FastAPI per esporre RecursiveMAS come endpoint OpenAI-compatible.
Versione corretta: v1.0.1

Uso:
    set RECURSIVEMAS_API_KEY=sk-recursivemas  (solo per OpenCode, il server non valida)
    python server.py

Endpoint:
    GET  /health
    POST /v1/chat/completions  (solo stream:false)
"""
import os
import sys
import time
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

try:
    from system_loader import load_mas_system
    from inference.run import run_mas_inference  # VERIFICA nome reale in inference/run.py
except ImportError as e:
    print(f"AVVISO import RecursiveMAS fallito ({e}). Il server parte ma rispondera' 500.")
    load_mas_system = None
    run_mas_inference = None

app = FastAPI(
    title="RecursiveMAS Wrapper",
    description="Endpoint OpenAI-compatible per delegare ragionamento complesso a RecursiveMAS",
    version="1.0.1",
)

MODEL_STYLE_MAP = {
    "sequential-scaled": "sequential_scaled",
    "sequential-light": "sequential_light",
    "mixture": "mixture",
    "distillation": "distillation",
    "deliberation": "deliberation",
}

MAS_STYLE = os.getenv("MAS_STYLE", "sequential_scaled")
MAS_DEVICE = os.getenv("MAS_DEVICE", "cuda")

mas_system = None


def get_mas_system():
    global mas_system
    if mas_system is None:
        if load_mas_system is None:
            raise RuntimeError("Moduli RecursiveMAS non importati. Controlla sys.path e inference/run.py")
        print(f"Caricamento RecursiveMAS stile={MAS_STYLE} device={MAS_DEVICE}")
        mas_system = load_mas_system(style=MAS_STYLE, device=MAS_DEVICE, trust_remote_code=True)
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
    if load_mas_system is None or run_mas_inference is None:
        raise HTTPException(status_code=500, detail="Moduli RecursiveMAS non importati.")
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
        result = run_mas_inference(mas_system=mas, question=user_msg,
                                   dataset="custom",
                                   temperature=temp,
                                   max_tokens=max_tok)
        final_answer = result.get("answer", result.get("response", str(result))) if isinstance(result, dict) else str(result)
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
