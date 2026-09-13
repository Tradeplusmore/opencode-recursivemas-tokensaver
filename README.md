# OpenCode x RecursiveMAS — Token-Saver & Reasoning Router

Integrazione globale di OpenCode con la **logica RecursiveMAS** (planner -> critic -> solver):
risparmi token sul banale, migliori la qualita sul complesso, deleghi alla MAS-GPU solo quando serve.

> Stato: installazione globale verificata — `opencode mcp list -> recursivemas connected`,
> audit bug/sicurezza superato, server su `127.0.0.1:8001`.

## Preview

| Richiesta | Comportamento automatico | Costo |
|---|---|---|
| `traduci / riassumi / ciao` | risposta in max 8 righe, 0 tool | ~0 extra |
| coding normale, debug semplice | `PLAN -> CRITIC -> SOLVE`, budget 512 | basso |
| `dimostra / integrale / matrice / refactor >60 righe` | tool MCP `call_recursivemas` (porta 8001) | solo quando serve |
| stessa domanda ripetuta | `CACHE HIT` da `.recursivemas_cache.json` | 0 token |

## Architettura

```text
OpenCode (tuo model) -> instructions globali SIMPLE/MEDIUM/COMPLEX
  SIMPLE/MEDIUM -> formato rigido PLAN/CRITIC/SOLVE+RISULTATO
  COMPLEX -> MCP recursivemas (stdio) -> FastAPI 127.0.0.1:8001 -> RecursiveMAS GPU*
  *solo se server.py attivo con checkpoint reali, altrimenti fallback testuale
```

Porta **8001** (non 8000) per non confliggere con eventuali proxy locali.

## Struttura repo

```text
recursivemas/
  server.py            # wrapper FastAPI OpenAI-compatible (GET /health, POST /v1/chat/completions, solo stream:false)
  opencode-router.py   # CLI smart: classify->compress->cache->delega/fallback
  mcp-recursivemas.py  # MCP stdio: call_recursivemas + plan_critic_solve
instructions/
  AGENTS-RecursiveMAS.md   # regole da unire al tuo AGENTS.md
docs/
  guida-recursivemas-opencode-claude.md
  README-TOKEN-SAVER.md
  INSTALL-GLOBALE.md
scripts/
  start-recursivemas.bat / .sh
opencode.example.json  # template provider+MCP+instructions
```

## Flusso logico (router)

```text
domanda -> compress(4000ch) -> classify(SIMPLE/MEDIUM/COMPLEX)
  SIMPLE -> prompt cheap, nessuna chiamata
  MEDIUM -> sequential-light, 512 tok + cache SHA256
  COMPLEX -> sequential-scaled, 1024 tok (2048 con --deep) + cache
  MAS offline / URL non locale -> fallback prompt 3-step locale
```

## Schema operativo

1. Installazione globale una volta sola -> vale per **ogni** progetto.
2. Lavoro quotidiano: apri `opencode`, programmi. Niente da avviare.
3. Solo per math/scienza dura: accendi `server.py` in un secondo terminale.
4. Ripetizioni: la cache risponde senza spendere token.

## Installazione globale

```bash
pip install -r requirements.txt
mkdir -p ~/.config/opencode/recursivemas
cp recursivemas/* ~/.config/opencode/recursivemas/
# unisci opencode.example.json nel tuo ~/.config/opencode/opencode.jsonc
opencode mcp list   # deve dire recursivemas connected
```

Windows: `setx RECURSIVEMAS_API_KEY "sk-recursivemas"`, poi riavvia il terminale.

## Server GPU (opzionale)

```bash
MAS_STYLE=sequential_scaled MAS_DEVICE=cuda python recursivemas/server.py
curl http://127.0.0.1:8001/health
```

## Sicurezza

Vedi `SECURITY.md`. Mai esporre su `0.0.0.0` senza auth. Cache esclusa da git.

## Audit eseguito (2026-09-13)

- py_compile OK x3, JSON validi, deps OK
- classificazione SIMPLE/COMPLEX OK, SSRF guard blocca URL remoti + fallback OK
- server: /health OK, senza moduli MAS -> 500 generico, stream:true -> 400
- fix: typo eig, clamp token, truncate 8000ch, errori generici, chmod 600 cache, bind 127.0.0.1:8001
