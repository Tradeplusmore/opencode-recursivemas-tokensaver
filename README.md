# OpenCode x RecursiveMAS — logica integrata, zero dipendenze

Tutta la logica RecursiveMAS (planner -> critic/refiner -> solver) integrata in
OpenCode nativo: **agent globale + comando + istruzioni**. Nessun MCP, nessun
server, nessuno script, nessuna GPU. Apri `opencode` e funziona.

## Come funziona (automatico, ogni progetto)

| Richiesta | Comportamento |
|---|---|
| banale (saluti, traduzioni, codice breve) | risposta in max 8 righe |
| normale | PLAN 3-5 punti / CRITIC / SOLVE + RISULTATO |
| codice | planner 3-6 step senza codice -> refiner -> solver con UN blocco codice |
| math/scienza | esperto + risposta in boxed |
| complessa (dimostra, matrici, refactor grossi) | versione DEEP estesa, tutto inline |
| `/recursive ...` | forza il protocollo |

## Installazione (una volta)

```bash
mkdir -p ~/.config/opencode/agent ~/.config/opencode/command
cp agent/recursive.md ~/.config/opencode/agent/
cp command/recursive.md ~/.config/opencode/command/
# unisci "instructions" da opencode.example.json nel tuo opencode.jsonc
```

`opencode.example.json` = solo `$schema` + `instructions`. Niente provider, niente MCP.

## Struttura

```text
agent/recursive.md      # agent globale (primary): tutti i track, zero tool esterni
command/recursive.md    # /recursive
opencode.example.json   # template config minima
docs/                   # guide complete
extras/                 # OPZIONALI (richiedono dipendenze): server FastAPI, router CLI,
                        # pipeline CPU Ollama, MCP server, colab GPU, code pipeline, check-gpu
recursivemas/           # sorgenti originali degli extra
```

## Extra opzionali (solo se vuoi: server GPU/Colab/CPU/MCP)

Vedi `docs/` e `extras/`. Non servono per l'uso quotidiano.
