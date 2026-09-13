# Guida Completa: Integrare RecursiveMAS con OpenCode e Claude Code Desktop

> **Obiettivo**: Far sì che quando programmi con Claude o OpenCode, i modelli possano delegare automaticamente i task di ragionamento complesso a RecursiveMAS, mantenendo tutto il flusso dentro i due ambienti.

---

## Indice

1. [Panoramica Architetturale](#panoramica-architetturale)
2. [Prerequisiti Comuni](#prerequisiti-comuni)
3. [Parte A: Configurazione per OpenCode](#parte-a-configurazione-per-opencode)
4. [Parte B: Configurazione per Claude Code Desktop](#parte-b-configurazione-per-claude-code-desktop)
5. [Wrapper FastAPI per RecursiveMAS](#wrapper-fastapi-per-recursivemas)
6. [Script di Avvio Rapido](#script-di-avvio-rapido)
7. [Troubleshooting](#troubleshooting)
8. [Note Importanti e Limitazioni](#note-importanti-e-limitazioni)

---

## Panoramica Architetturale

### Il vincolo fondamentale

RecursiveMAS opera su **hidden states latenti** condivisi tra agenti tramite moduli `RecursiveLink` — non su testo generato [web:1][web:2]. Questo richiede accesso "white-box" ai pesi del modello (modelli open-weight locali come Qwen, Llama, Gemma).

**Cosa NON puoi fare:**
- Inserire Claude *dentro* la recursione stessa del sistema multi-agente
- Usare API commerciali (Claude, GPT-4) come agenti core (planner, critic, solver)

**Cosa PUOI fare:**
- Usare Claude/OpenCode come "cervello principale" per coding, tool-calling, gestione file
- Delegare i task di ragionamento complesso (matematica, scienza, logica avanzata) a un wrapper API locale che esegue RecursiveMAS
- Integrare le risposte di RecursiveMAS nel flusso di lavoro di Claude/OpenCode

### Architettura a due livelli

```
┌─────────────────────────────┐
│  Claude Code Desktop        │
│  o OpenCode CLI             │
│  (modello principale)       │
└─────────────┬───────────────┘
              │
              │ Prompt: "Risolvi questo problema complesso"
              ▼
┌─────────────────────────────┐
│  Wrapper FastAPI            │
│  (localhost:8001)           │
│  /v1/chat/completions       │
└─────────────┬───────────────┘
              │
              │ Carica pipeline RecursiveMAS
              ▼
┌─────────────────────────────┐
│  RecursiveMAS               │
│  (planner→critic→solver,    │
│   recursivo su hidden states)│
└─────────────┬───────────────┘
              │
              │ Risposta finale
              ▼
┌─────────────────────────────┐
│ Claude/OpenCode integra la  │
│ risposta nel flusso completo│
└─────────────────────────────┘
```

---

## Prerequisiti Comuni

### 1. Clonare RecursiveMAS

```bash
git clone https://github.com/RecursiveMAS/RecursiveMAS.git
cd RecursiveMAS
```

### 2. Installare le dipendenze

```bash
# Crea ambiente virtuale (consigliato)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installa requisiti
pip install -r requirements.txt

# Installa FastAPI e uvicorn per il wrapper
pip install fastapi uvicorn pydantic
```

### 3. Scaricare i checkpoint

I checkpoint sono disponibili su Hugging Face, organizzati per stile di collaborazione [web:1][web:34]:

| Stile | Modelli usati | Caso d'uso |
|-------|---------------|------------|
| `sequential_light` | Qwen3-1.7B, Llama3.2-1B, Qwen2.5-Math-1.5B | Velocità, testing rapido |
| `sequential_scaled` | Gemma3-4B, Llama3.2-3B, Qwen3.5-4B | Accuratezza bilanciata |
| `mixture` | DeepSeek-R1-Distill-Qwen-1.5B, Qwen2.5-Coder-3B, BioMistral-7B | Task eterogenei |
| `distillation` | Qwen3.5-9B (expert), Qwen3.5-4B (learner) | Knowledge transfer |
| `deliberation` | Qwen3.5-4B (reflector + tool-caller) | Ricerca + ragionamento |

Per scaricare, usa comandi espliciti (verifica i nomi repo su Hugging Face, gli esempi sotto sono template):

```bash
# login (serve token HF)
huggingface-cli login
# esempio template — sostituisci con ID reale dalla repo
huggingface-cli download RecursiveMAS/sequential-scaled --local-dir ./checkpoints/sequential-scaled
```

> ⚠️ ATTENZIONE: nomi come `Qwen3.5-9B`, `Gemma3-4B` nella tabella sotto vanno verificati su huggingface.co/RecursiveMAS. Al momento della scrittura non risultano confermati. Non scaricare nulla a cieco: controlla prima la pagina HF e il README al commit indicato in fondo.

### 4. Verificare GPU

RecursiveMAS richiede CUDA per essere pratico. Verifica:

```bash
python -c "import torch; print(f'CUDA disponibile: {torch.cuda.is_available()}')"
```

Se `False`, l'inferenza sarà molto lenta su CPU.

---

## Parte A: Configurazione per OpenCode

### Passo 1: Installare OpenCode

```bash
curl -fsSL https://opencode.ai/install | bash
```

Oppure scarica l'app desktop da [opencode.ai/download](https://opencode.ai/download) [web:31].

### Passo 2: Creare il file di configurazione

Crea o modifica `opencode.json`:

- **Globale**: `~/.config/opencode/opencode.json` (Windows: `%APPDATA%\opencode\opencode.json`)
- **Di progetto**: nella root del tuo progetto

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": {
      "options": { "apiKey": "{env:ANTHROPIC_API_KEY}" }
    },
    "openai": {
      "options": { "apiKey": "{env:OPENAI_API_KEY}" }
    },
    "recursivemas": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "RecursiveMAS Reasoning Engine",
      "options": {
        "baseURL": "http://localhost:8001/v1",
        "apiKey": "{env:RECURSIVEMAS_API_KEY}"
      },
      "models": {
        "sequential-scaled": { 
          "name": "RecursiveMAS Sequential-Scaled",
          "maxTokens": 2048
        },
        "sequential-light": { 
          "name": "RecursiveMAS Sequential-Light",
          "maxTokens": 1024
        }
      }
    }
  },
  "model": "anthropic/claude-sonnet-4-5"
}
```

**Note importanti:**
- Usa `{env:VARIABLE}` per le API key, non scriverle in chiaro [web:28]
- Se il tuo endpoint risponde su `/v1/chat/completions`, usa `@ai-sdk/openai-compatible` [web:25]
- Se invece implementa `/v1/responses`, usa `@ai-sdk/openai`

### Passo 3: Configurare le credenziali

```bash
# Windows (PowerShell)
$env:RECURSIVEMAS_API_KEY = "sk-recursivemas"
# Linux/Mac
# export RECURSIVEMAS_API_KEY=sk-recursivemas
```

Dentro OpenCode, lancia:

```
/connect
```

1. Scegli **Other** per il provider custom RecursiveMAS [web:25][web:32]
2. Inserisci una API key finta (es. `sk-recursivemas`) — il wrapper locale non la valida
3. Salva

### Passo 4: Usare RecursiveMAS in OpenCode

#### Selezione manuale del modello

1. Digita `/models` per vedere tutti i provider configurati [web:25][web:28]
2. Scegli `recursivemas/sequential-scaled` per task complessi
3. Formula il prompt: `Risolvi: [problema di matematica/scienza/logica]`
4. Per tornare a Claude: `/models` → `anthropic/claude-sonnet-4-5`

#### Automazione con script wrapper (opzionale)

Crea uno script Python `opencode-router.py` nella root del progetto:

```python
import requests
import sys

def call_recursivemas(question: str, style: str = "sequential-scaled") -> str:
    """Chiama il wrapper RecursiveMAS e restituisce la risposta."""
    url = "http://localhost:8001/v1/chat/completions"
    payload = {
        "model": style,
        "messages": [{"role": "user", "content": question}]
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Errore RecursiveMAS: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python opencode-router.py 'domanda da risolvere'")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    answer = call_recursivemas(question)
    print(answer)
```

Usalo da terminale mentre lavori in OpenCode:

```bash
python opencode-router.py "Dimostra che sqrt(2) è irrazionale"
```

Copia il risultato e incollalo nella chat di OpenCode.

### Passo 5: Verifica della configurazione

Dopo aver salvato `opencode.json`:

1. Riavvia OpenCode se il provider custom non appare [web:32]
2. Digita `/models` — dovresti vedere `recursivemas/sequential-scaled` e `recursivemas/sequential-light`
3. Assicurati che il server FastAPI sia in esecuzione (vedi sezione [Wrapper FastAPI](#wrapper-fastapi-per-recursivemas))

---

## Parte B: Configurazione per Claude Code Desktop

### Passo 1: Installare Claude Desktop

1. Scarica da [claude.com/download](https://claude.com/download) [web:23]
2. Installa per Windows (disponibile anche ARM64) [web:22]
3. Accedi con:
   - Piano Pro, Max, Team o Enterprise, **oppure**
   - API key Claude (Settings → API Keys)

### Passo 2: Abilitare il tab Code

1. Apri l'app desktop Claude
2. Clicca sul tab **Code** nella barra laterale [web:22][web:29]
3. Seleziona la cartella del progetto (es. la repo clonata di RecursiveMAS)

### Passo 3: Sfruttare le funzionalità avanzate

La versione ridisegnata (v1.2581.0+, aprile 2026) offre [web:18][web:29]:

- **Sidebar per sessioni multiple**: gestisci più task in parallelo
- **Drag-and-drop dei pannelli**: organizza chat, terminale, editor come preferisci
- **Terminale integrato**: esegui script Python, comandi git, ecc.
- **Editor file integrato**: modifica `server.py`, config, ecc. senza uscire dall'app
- **Browser integrato** (luglio 2026): Claude può consultare documentazione web mentre lavora [web:20][web:24]

### Passo 4: System prompt per routing automatico

Prima di iniziare una sessione Code, incolla questo system prompt nella chat:

```
Sei un assistente di programmazione esperto che integra Claude per coding, 
tool-calling e gestione file con un motore esterno di ragionamento complesso 
chiamato RecursiveMAS.

REGOLE DI ROUTING:
1. Per task di coding, file manipulation, shell commands, git: usa le tue capacità native.
2. Per problemi di ragionamento complesso (matematica, scienza, logica avanzata, 
   dimostrazioni formali, problemi di fisica/chimica):
   - Riconosci parole chiave: "risolvi", "dimostra", "calcola", "prova che", 
     "trova tutti i", "determina se"
   - Genera una chiamata HTTP POST a http://localhost:8001/v1/chat/completions
   - Body: {"model":"sequential-scaled","messages":[{"role":"user","content":"[problema]"}]}
   - Integra la risposta nel tuo output, citando esplicitamente "Risposta generata da RecursiveMAS"

FORMATO OUTPUT:
- Se usi RecursiveMAS, precedi la risposta con: "🔍 Delegato a RecursiveMAS per ragionamento complesso:"
- Per tutto il resto, rispondi normalmente come Claude.

NON CHIAMARE MAI RecursiveMAS per:
- Scrivere codice semplice
- Spiegare concetti generali
- Tradurre testo
- Riassumere documenti
```

### Passo 5: Chiedere a Claude di scrivere il codice di chiamata

Dopo aver impostato il system prompt, chiedi:

```
Scrivi uno script Python che chiama l'endpoint RecursiveMAS su localhost:8001 
e restituisce la risposta formattata. Lo script deve accettare il problema 
come argomento da riga di comando.
```

Claude genererà uno script simile a quello mostrato per OpenCode. Salvalo come `claude-router.py` nella root del progetto.

### Passo 6: Usare il routing in pratica

**Scenario tipico:**

1. Apri Claude Code Desktop, tab Code, cartella del progetto
2. Incolla il system prompt di routing (Passo 4)
3. Chiedi: "Aiutami a risolvere questo problema di ottimizzazione: [problema]"
4. Claude riconoscerà il pattern e:
   - O genererà la chiamata HTTP da eseguire tu manualmente
   - O (se hai configurato tool custom) chiamerà direttamente l'endpoint

**Esempio di output atteso:**

```
🔍 Delegato a RecursiveMAS per ragionamento complesso:

[La soluzione dettagliata generata da RecursiveMAS, con passaggi intermedi]

Questa risposta è stata generata dal sistema multi-agente recursivo. 
Posso ora aiutarti a implementare questa soluzione in codice Python se vuoi.
```

### Passo 7: Tool custom (metodo corretto: MCP)

> ❌ Il file `claude-code-tools.json` descritto in versioni precedenti della guida **non esiste** come meccanismo ufficiale. Il modo corretto è un **MCP server**.

Crea `mcp-recursivemas.py` (vedi file di esempio nella stessa cartella di questa guida) e registralo in `opencode.json`:

```json
{
  "mcp": {
    "recursivemas": {
      "type": "local",
      "command": ["python", "mcp-recursivemas.py"],
      "enabled": true
    }
  }
}
```

Il server espone i tool `call_recursivemas` e `plan_critic_solve`. Nel system prompt, aggiungi: "Per ragionamento complesso, usa SEMPRE il tool MCP `call_recursivemas`".

---

## Wrapper FastAPI per RecursiveMAS

Questo è il componente centrale che rende possibile l'integrazione.

### File: `server.py`

Salvalo nella root della repo `RecursiveMAS/`:

```python
"""
Wrapper FastAPI per esporre RecursiveMAS come endpoint OpenAI-compatible.
Permette a OpenCode e Claude Code di delegare task di ragionamento complesso.

Uso:
    python server.py

Endpoint:
    POST /v1/chat/completions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
import os

# Import dalla repo RecursiveMAS (adatta i path se necessario)
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from system_loader import load_mas_system
    from inference.run import run_mas_inference  # Verifica il nome esatto in inference/run.py
except ImportError as e:
    print(f"AVVISO import RecursiveMAS fallito ({e}). Il server parte ma rispondera' 500 finche' non sistemi i path.")
    load_mas_system = None
    run_mas_inference = None

app = FastAPI(
    title="RecursiveMAS Wrapper",
    description="Endpoint OpenAI-compatible per delegare ragionamento complesso a RecursiveMAS",
    version="1.0.1"
)

# Mappa nomi modello API (trattino) -> stili interni (underscore).
# Il client chiede "sequential-scaled", il sistema interno usa "sequential_scaled".
MODEL_STYLE_MAP = {
    "sequential-scaled": "sequential_scaled",
    "sequential-light": "sequential_light",
    "mixture": "mixture",
    "distillation": "distillation",
    "deliberation": "deliberation",
}

# Stile default se il client manda un model sconosciuto
MAS_STYLE = os.getenv("MAS_STYLE", "sequential_scaled")
MAS_DEVICE = os.getenv("MAS_DEVICE", "cuda")

# Caricamento lazy del sistema MAS
mas_system = None

def get_mas_system():
    """Carica il sistema MAS al primo utilizzo (singleton)."""
    global mas_system
    if mas_system is None:
        print(f"Caricamento RecursiveMAS con stile: {MAS_STYLE}, device: {MAS_DEVICE}")
        mas_system = load_mas_system(
            style=MAS_STYLE,
            device=MAS_DEVICE,
            trust_remote_code=True,
        )
        print("Sistema MAS caricato con successo")
    return mas_system

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.6
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.get("/health")
async def health_check():
    """Endpoint per verificare che il server sia attivo."""
    return {
        "status": "healthy",
        "mas_loaded": mas_system is not None,
        "style": MAS_STYLE,
        "device": MAS_DEVICE
    }

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(req: ChatCompletionRequest):
    """
    Endpoint principale: esegue RecursiveMAS sul problema fornito.
    
    Estrae l'ultimo messaggio utente, esegue la pipeline recursiva,
    e restituisce la risposta finale formattata come OpenAI chat completion.
    """
    if req.stream:
        raise HTTPException(status_code=400, detail="stream:true non supportato da questo wrapper. Richiama con stream:false.")
    if load_mas_system is None or run_mas_inference is None:
        raise HTTPException(status_code=500, detail="Moduli RecursiveMAS non importati. Controlla sys.path e nomi in inference/run.py")
    # Risolvi lo stile dal campo model (es. sequential-scaled -> sequential_scaled)
    requested_style = MODEL_STYLE_MAP.get(req.model, MAS_STYLE)
    mas = get_mas_system()
    
    # Estrai l'ultimo messaggio utente
    user_msg = None
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_msg = msg.content
            break
    
    if not user_msg:
        raise HTTPException(status_code=400, detail="Nessun messaggio utente trovato")
    
    print(f"Ricevuta richiesta: {user_msg[:100]}...")
    
    # Esegui RecursiveMAS
    try:
        result = run_mas_inference(
            mas_system=mas,
            question=user_msg,
            dataset="custom",  # Adatta se vuoi vincolare a domini specifici
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        
        # Estrai la risposta (adatta alla struttura reale del risultato)
        if isinstance(result, dict):
            final_answer = result.get("answer", result.get("response", str(result)))
        else:
            final_answer = str(result)
        
        print(f"Risposta generata: {final_answer[:100]}...")
        
    except Exception as e:
        print(f"Errore durante l'inferenza: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inferenza MAS fallita: {str(e)}")
    
    # Costruisci la risposta OpenAI-compatible
    return ChatCompletionResponse(
        id=f"recursivemas-{int(time.time())}",
        created=int(time.time()),
        model=req.model,
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": final_answer},
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": 0,  # Non tracciati in questa versione
            "completion_tokens": 0,
            "total_tokens": 0
        }
    )

if __name__ == "__main__":
    print("=" * 60)
    print("RecursiveMAS Wrapper - Server FastAPI")
    print("=" * 60)
    print(f"Stile MAS: {MAS_STYLE}")
    print(f"Device: {MAS_DEVICE}")
    print("Endpoint: http://localhost:8001/v1/chat/completions")
    print("Health check: http://localhost:8001/health")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

> 🔒 Sicurezza: usa `127.0.0.1` per restare solo locale. Usa `0.0.0.0` solo se vuoi esporre in LAN (e aggiungi auth).

### Test rapido (curl)

```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"sequential-scaled\",\"messages\":[{\"role\":\"user\",\"content\":\"Calcola 23 x 47\"}],\"max_tokens\":256,\"stream\":false}"
```

### Adattamenti necessari

Prima di eseguire, verifica i nomi esatti delle funzioni in `inference/run.py`:

1. Apri `RecursiveMAS/inference/run.py`
2. Cerca la funzione principale che esegue l'inferenza (potrebbe chiamarsi `run_mas_inference`, `inference`, `main`, ecc.)
3. Adatta l'import e la chiamata in `server.py` di conseguenza

Se `run.py` è uno script eseguibile (non modulare), potresti dover estrarre la logica in una funzione riutilizzabile o chiamare lo script come subprocesso.

### Variabili d'ambiente

Puoi configurare il server tramite variabili d'ambiente:

```bash
# Windows (PowerShell)
$env:MAS_STYLE = "sequential_scaled"
$env:MAS_DEVICE = "cuda"
python server.py

# Linux/Mac
export MAS_STYLE=sequential_scaled
export MAS_DEVICE=cuda
python server.py
```

Stili disponibili: `sequential_light`, `sequential_scaled`, `mixture`, `distillation`, `deliberation` [web:1].

---

## Script di Avvio Rapido

### File: `start-recursivemas.bat` (Windows)

```batch
@echo off
echo ============================================
echo  Avvio Wrapper RecursiveMAS
echo ============================================
echo.

cd /d "%~dp0"

REM Attiva ambiente virtuale se esiste
if exist "venv\Scripts\activate.bat" (
    echo Attivazione ambiente virtuale...
    call venv\Scripts\activate.bat
)

REM Imposta variabili d'ambiente (opzionale)
set MAS_STYLE=sequential_scaled
set MAS_DEVICE=cuda

echo Avvio server su http://localhost:8001
echo Premi Ctrl+C per fermare
echo.

python server.py

pause
```

### File: `start-recursivemas.sh` (Linux/Mac)

```bash
#!/bin/bash

echo "============================================"
echo " Avvio Wrapper RecursiveMAS"
echo "============================================"
echo

cd "$(dirname "$0")"

# Attiva ambiente virtuale se esiste
if [ -f "venv/bin/activate" ]; then
    echo "Attivazione ambiente virtuale..."
    source venv/bin/activate
fi

# Imposta variabili d'ambiente (opzionale)
export MAS_STYLE=sequential_scaled
export MAS_DEVICE=cuda

echo "Avvio server su http://localhost:8001"
echo "Premi Ctrl+C per fermare"
echo

python server.py
```

Rendi eseguibile (Linux/Mac):

```bash
chmod +x start-recursivemas.sh
```

---

## Troubleshooting

### Il server non si avvia

**Errore: `ModuleNotFoundError: No module named 'system_loader'`**

- Assicurati di essere nella root della repo `RecursiveMAS/`
- Verifica che `system_loader.py` esista nella root
- Se il modulo è in una sottocartella, aggiungi il path:

```python
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

**Errore: `CUDA out of memory`**

- Riduci lo stile: usa `sequential_light` invece di `sequential_scaled`
- Abbassa `max_tokens` nelle richieste
- Chiudi altre applicazioni GPU-intensive

### OpenCode non vede il provider custom

1. Verifica che `opencode.json` sia nella posizione corretta [web:28]
2. Riavvia OpenCode completamente [web:32]
3. Digita `/models` e controlla se `recursivemas/...` appare
4. Verifica che il server sia in esecuzione: `http://localhost:8001/health`

### Claude non chiama l'endpoint

1. Controlla che il system prompt di routing sia stato incollato correttamente
2. Verifica che Claude abbia riconosciuto le parole chiave ("risolvi", "dimostra", ecc.)
3. Se usi tool custom, assicurati che il file JSON sia nella cartella del progetto
4. Prova a chiedere esplicitamente: "Chiama l'endpoint RecursiveMAS per risolvere: [problema]"

### Le risposte sono lente

- RecursiveMAS esegue più round di recursione — è normale [web:1]
- Usa `sequential_light` per testing rapido
- Assicurati di usare GPU (CUDA), non CPU

### Il server restituisce errore 500

1. Controlla i log del server (stdout) per il messaggio di errore dettagliato
2. Verifica che i checkpoint siano scaricati correttamente
3. Prova con un problema semplice per isolare il bug
4. Controlla che `run_mas_inference` sia chiamata con gli argomenti corretti

---

## Note Importanti e Limitazioni

### Dominio di efficacia

RecursiveMAS è stato addestrato e testato su [web:1][web:33]:

- ✅ Matematica (MATH, GSM8K)
- ✅ Scienze (fisica, chimica, biologia)
- ✅ Medicina (QA clinici)
- ✅ Ricerca (ragionamento su paper)
- ✅ Generazione di codice (HumanEval, MBPP)

**Meno efficace su:**
- ❌ Ragionamento generico non strutturato
- ❌ Creatività (scrittura creativa, brainstorming)
- ❌ Task che richiedono conoscenza del mondo in tempo reale
- ❌ Conversazione aperta (chat generico)

### Requisiti hardware

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| GPU | 8 GB VRAM | 16+ GB VRAM (RTX 3090/4090) |
| RAM | 16 GB | 32+ GB |
| Storage | 20 GB liberi (checkpoint) | SSD NVMe |

Senza GPU, l'inferenza sarà impraticabile per uso interattivo.

### Confronto con alternative

| Approccio | Pro | Contro |
|-----------|-----|--------|
| **RecursiveMAS nativo** (questa guida) | Massima accuratezza (+8-12% su benchmark) [web:1][web:40] | Richiede GPU, setup complesso |
| **Versione "testo-level"** (LangGraph + prompt) | Nessun requisito GPU, setup semplice | Minore accuratezza, non usa hidden states [web:44] |
| **Solo Claude/GPT-4** | Setup zero, massima comodità | Meno accurato su ragionamento complesso strutturato |

### Aggiornamenti futuri

Il README di RecursiveMAS indica come "in completamento" [web:1]:

- ☑️ Supporto per famiglie di modelli aggiuntive
- ☑️ Pattern di collaborazione MAS aggiuntivi

Tieni d'occhio la repo per aggiornamenti che potrebbero semplificare l'integrazione.

---

## Riferimenti

- **Repo ufficiale**: [github.com/RecursiveMAS/RecursiveMAS](https://github.com/RecursiveMAS/RecursiveMAS) [web:1]
- **Paper**: "Recursive Multi-Agent Systems" (arXiv:2604.25917) [web:33]
- **Checkpoint Hugging Face**: [huggingface.co/RecursiveMAS](https://huggingface.co/RecursiveMAS) [web:34]
- **Doc OpenCode**: [opencode.ai/docs](https://opencode.ai/docs) [web:25][web:27]
- **Doc Claude Code**: [code.claude.com/docs](https://code.claude.com/docs) [web:22]

---

## Checklist Finale

Prima di iniziare a usare l'integrazione:

- [ ] Repo RecursiveMAS clonata e dipendenze installate
- [ ] Checkpoint scaricati per lo stile scelto
- [ ] GPU CUDA disponibile e verificata
- [ ] `server.py` creato e adattato alla tua configurazione
- [ ] Server in esecuzione su `http://localhost:8001`
- [ ] OpenCode: `opencode.json` configurato con provider `recursivemas`
- [ ] Claude Code: system prompt di routing incollato
- [ ] Testato con un problema semplice (es. "Calcola 23 × 47")

Se tutti i punti sono spuntati, sei pronto per usare RecursiveMAS come motore di ragionamento delegato dentro OpenCode e Claude Code Desktop.

---

*Ultimo aggiornamento: Settembre 2026*
*Questa guida si basa sulla versione del repository RecursiveMAS al commit `38f7da4` (29 giugno 2026) [web:1].*