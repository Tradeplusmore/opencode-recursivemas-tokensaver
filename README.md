# OpenCode × RecursiveMAS — logica ufficiale, zero dipendenze

Tutta la **logica** di [RecursiveMAS](https://github.com/RecursiveMAS/RecursiveMAS) (MIT)
replicata come procedura nativa OpenCode: nessun server, nessun MCP, nessuno script,
nessuna GPU. Ogni regola cita il file ufficiale da cui deriva.

> Stato verificato: config globale minima, agent 9 sezioni (11 citazioni),
> comando `/recursive`, repo allineata al locale.

## Indice

1. [Preview](#1-preview)
2. [Architettura](#2-architettura)
3. [Struttura repo](#3-struttura-repo)
4. [Installazione](#4-installazione)
5. [Agent `recursive` — le 9 sezioni](#5-agent-recursive--le-9-sezioni)
6. [Comando `/recursive`](#6-comando-recursive)
7. [Flusso logico](#7-flusso-logico)
8. [Schema operativo](#8-schema-operativo)
9. [Fonti ufficiali e vendor](#9-fonti-ufficiali-e-vendor)
10. [Cosa NON è incluso (e perché)](#10-cosa-non-è-incluso-e-perché)
11. [Extra opzionali](#11-extra-opzionali)

## 1. Preview

| Richiesta | Cosa fa OpenCode in automatico |
|---|---|
| Codice/test | Planner (3-6 step, no codice) → refiner pure-plan → solver (1 blocco) |
| Opzioni A-D | Stesso giro, risposta `\boxed{A}` |
| Math/scienza | Stesso giro, risposta `\boxed{1}` |
| Domanda mista | 3 esperti (math/code/science) → summarizer |
| Piano da eseguire con vincoli | Expert → learner ("prioritize the task constraints") |
| Ricerca esterna | Reflector `<search>/<python>` → `<result>` → `\boxed{}` |
| Problema duro | 3 round con feedback + judge JSON |
| Fuori scope | Risposta normale |

## 2. Architettura

```text
tu scrivi in OpenCode (qualsiasi progetto)
  └─▶ instructions globali (routing, 1 riga per regola)
        └─▶ agent recursive (primary, temp 0.6 ufficiale)
              ├─▶ §1 routing code/choice/math  (infer_hie_task, infer_distill_task)
              ├─▶ §2 sequential + feedback     (prompts.py planner/refiner/solver)
              ├─▶ §3 mixture + summarizer      (prompts.py hie)
              ├─▶ §4 distillation learner      (prompts.py distill)
              ├─▶ §5 deliberation reflector    (reflector_tool_notes.py, TOOL_RE)
              ├─▶ §6 passaggi = slot ufficiali (FEEDBACK/REFINED/DISTILL/HIE slots)
              ├─▶ §7 log esiti result_jsonl    (run.py) in memory/recursive-results.jsonl
              ├─▶ §8 temperature 0.6 / 0.2     (run.py, MBPPPLUS_TEMPERATURE)
              └─▶ §9 judge {"true_false"}      (llm_judge.py)
```

## 3. Struttura repo

```text
agent/recursive.md              # agent globale: 9 sezioni, ogni regola citata
command/recursive.md            # /recursive: forza il protocollo
opencode.example.json           # config minima: $schema + instructions
memory/recursive-results.jsonl  # log esiti (schema result_jsonl ufficiale)
docs/                           # guide (guida completa, token-saver, installazione, CPU roles)
recursivemas/                   # sorgenti extra archiviati + vendor/ (file ufficiali MIT)
scripts/                        # start server, setup CPU roles, Modelfile
```

## 4. Installazione

```bash
mkdir -p ~/.config/opencode/agent ~/.config/opencode/command
cp agent/recursive.md ~/.config/opencode/agent/
cp command/recursive.md ~/.config/opencode/command/
# unisci "instructions" da opencode.example.json nel tuo ~/.config/opencode/opencode.jsonc
```

Verifica: apri `opencode` in un progetto qualsiasi, chiedi codice + math e controlla
che segua planner → refiner → solver con `\boxed{}`.

## 5. Agent `recursive` — le 9 sezioni

- **§1 Routing** — task code/choice/math come `infer_hie_task`/`infer_distill_task`;
  dataset ufficiali (math500, medqa, gpqa, mbppplus, aime25/26, livecodebench,
  bamboogle, hotpotqa); search-QA → deliberation.
- **§2 Sequential** — wording originale planner/refiner/solver (code 3-6 step
  "Do not write code"; math "Give a plan"); solver 1 blocco codice o `\boxed{}`;
  feedback-slot; round da tabella release (3 default, 2 su task veloci).
- **§3 Mixture** — esperti testuali + summarizer ufficiale ("You may reference
  the three expert information").
- **§4 Distillation** — learner ufficiale ("Use the expert plan as guidance,
  but prioritize the task constraints"), judge a chiudere il loop.
- **§5 Deliberation** — reflector ufficiale (think in mind, tag search/python/result,
  `\boxed{}` latex), tool eseguiti con quelli OpenCode.
- **§6 Passaggi inter-round** — solo ciò che gli slot ufficiali trasportano
  (Initial/Refined Plan, feedback, result). Nient'altro.
- **§7 Log esiti** — schema `result_jsonl` di run.py
  (question/gold/pred/raw_output + verdetto); rilettura ultime 20 su task duri.
- **§8 Temperature** — 0.6 default, 0.2 code con test nascosti.
- **§9 Judge** — JSON `{"true_false": bool}` (llm_judge.py); false → 1 riparazione,
  max 2 giudizi.

## 6. Comando `/recursive`

Forza il protocollo sulla richiesta `$ARGUMENTS` con lo stesso routing e le stesse
chiusure dell'agent. Nessun tool esterno.

## 7. Flusso logico

```text
richiesta → routing (§1) → famiglia (§2/3/4/5)
  → round con feedback via slot (§6, conteggi §2)
  → judge (§9) → false? 1 riparazione : fine
  → append log (§7)
```

## 8. Schema operativo

1. Installi una volta (vedi §4) → vale per OGNI progetto.
2. Programmi normale: il protocollo scatta da solo.
3. `/recursive ...` solo per forzarlo.
4. Niente da accendere, niente da aggiornare: è testo in config.

## 9. Fonti ufficiali e vendor

`recursivemas/vendor/` contiene (MIT, (c) 2026 RecursiveMAS, vedi ATTRIBUTION.txt):
`official_prompts.py`, `official_mas_prompt.py`, `off_notes.py` (reflector),
`off_judge.py` (llm_judge). Studiati anche `inference_mas*.py` (6985 righe),
`load_from_repo.py` (STYLE_SPECS), `run.py` (dataset, temperature, result_jsonl).

## 10. Cosa NON è incluso (e perché)

Non è logica replicabile ma calcolo fisico o attività separata:
- Esecuzione latente (`modeling.py` RecursiveLink, adapter `.pt`, pesi) → richiede GPU/VRAM.
- Training (`train/`) → richiede cluster per gradienti.
- Eval harness eseguito → richiede i pesi; la sua logica (routing, temperature,
  result_jsonl, judge) È inclusa sopra.

## 11. Extra opzionali

In `extras/` (richiedono dipendenze, non servono all'uso nativo): wrapper FastAPI
OpenAI-compatible, router CLI, pipeline ruoli CPU via Ollama (testata), MCP server,
setup Colab T4, code pipeline, check-gpu. Dettagli in `docs/`.
