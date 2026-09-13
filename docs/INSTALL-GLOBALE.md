# Installazione GLOBALE completata (automatica su tutti i progetti)

Data: 2026-09-13 — OpenCode v1.18.30

## Cosa è stato installato
1. `C:\Users\angel\.config\opencode\recursivemas\`
   - `opencode-router.py` (porta 8001)
   - `mcp-recursivemas.py` (porta 8001)
   - `server.py` (porta 8001)
   - `AGENTS-RecursiveMAS.md`
2. `C:\Users\angel\.config\opencode\opencode.jsonc` — riscritto con:
   - provider `recursivemas` su `http://127.0.0.1:8001/v1` (porta 8001 per NON confliggere col tuo proxy DeepSeek sulla 8000)
   - mcp `recursivemas` locale con path assoluto + env RECURSIVEMAS_URL
   - `instructions` globali con routing automatico SIMPLE/MEDIUM/COMPLEX
3. Env Windows `RECURSIVEMAS_API_KEY=sk-recursivemas` (via setx — riavvia il terminale)
4. Dipendenze: `pip install requests mcp fastapi uvicorn pydantic`

## Verifica
- `opencode mcp list` → `✓ recursivemas connected`
- `python ~/.config/opencode/recursivemas/opencode-router.py --prompt-only "test"` → ok

## Come funziona ora (automatico)
- Apri QUALSIASI progetto con `opencode` → le `instructions` globali sono sempre attive.
- Semplice → risposta corta, 0 tool.
- Medio → formato PLAN/CRITIC/SOLVE a budget ridotto.
- Complesso → chiama da solo il tool MCP `call_recursivemas`.
- Non devi copiare nulla nei singoli progetti.

## Server GPU (solo se/when hai checkpoint veri)
```powershell
$env:MAS_STYLE="sequential_scaled"; $env:MAS_DEVICE="cuda"
python C:\Users\angel\.config\opencode\recursivemas\server.py
# health: http://127.0.0.1:8001/health
```
Senza server attivo, il sistema resta in modalità text-level (risparmio token, qualità migliore) e fa fallback automatico.
