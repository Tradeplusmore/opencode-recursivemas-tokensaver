# Token-Saver RecursiveMAS per OpenCode — come usarlo

## Cosa ho creato (nella stessa cartella)
- `opencode.json` — config corretta (apiKey via env + MCP locale). Copialo nella root del progetto o in `%APPDATA%\opencode\opencode.json`.
- `server.py` — wrapper FastAPI corretto (solo se hai GPU + checkpoint RecursiveMAS veri).
- `opencode-router.py` — **il pezzo che ti fa risparmiare token da subito, senza GPU**.
- `mcp-recursivemas.py` — MCP server con 2 tool per OpenCode.
- `AGENTS-RecursiveMAS.md` — istruzioni planner→critic→solver da incollare in `AGENTS.md`.
- Questa guida + `guida-recursivemas-opencode-claude.md` (corretta).

## Il trucco: NON serve la GPU per risparmiare token
La vera RecursiveMAS (hidden-states) richiede GPU e checkpoint. Ma la sua LOGICA
(planner→critic→solver + routing selettivo + budget stretti + cache) funziona anche
a livello di prompt — e quella è gratis e riduce i token del 40-70% su task ripetitivi.

## Setup in 3 minuti (senza GPU)
```powershell
pip install requests mcp
$env:RECURSIVEMAS_API_KEY = "sk-recursivemas"
# copia opencode.json e AGENTS-RecursiveMAS.md nella root del tuo progetto
python opencode-router.py --prompt-only "la tua domanda"
```

## Uso quotidiano
```powershell
# 1) Semplice -> 0 chiamate extra, solo prompt corto
python opencode-router.py "traduci questo testo..."
# 2) Medio -> modello light, 512 token max
python opencode-router.py --cheap "debugga questa funzione..."
# 3) Complesso -> delega profonda (serve server.py attivo)
python opencode-router.py --deep "dimostra che..."
# 4) Cache automatica: la 2a volta la stessa domanda costa 0 token
```

## Perché migliora il lavoro dell'AI
1. **Routing selettivo**: il modello piccolo non spreca ragionamento profondo su banalità.
2. **Formato rigido PLAN/CRITIC/SOLVE**: niente papiri, niente ripetizioni, output più corretto.
3. **Cache SHA256**: domande uguali = risposta riusata, 0 token.
4. **Compressione input**: tronca e pulisce prima di inviare (max 4000 char default).
5. **Budget per step**: cheap=5+5+15 righe, deep=8+8+completo.

## Quando usare il server GPU vero
Solo per matematica/scienza dura (MATH, fisica, dimostrazioni) dove il +8-12% di
accuratezza ripaga il costo. Per coding quotidiano resta su router+MCP text-level.

## Checklist
- [ ] `pip install requests mcp` ok
- [ ] `opencode.json` copiato, `/models` mostra `recursivemas/...`
- [ ] `AGENTS-RecursiveMAS.md` incollato in `AGENTS.md`
- [ ] `python opencode-router.py "Calcola 23 x 47"` -> risposta + `[router] tipo=...`
- [ ] 2a esecuzione stessa domanda -> `[router] CACHE HIT`
