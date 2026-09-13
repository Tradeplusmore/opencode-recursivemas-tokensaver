---
description: Protocollo RecursiveMAS dai file ufficiali citati
---

Applica il protocollo RECURSIVE alla richiesta `$ARGUMENTS` (fonti in agent/recursive.md):
- Routing ufficiale: CODE / CHOICE (A-D) / MATH / ricerca-esterna / mista / trasferimento.
- CODE/MATH: planner (Step 1..n, "Do not write code" per codice) → refiner pure-plan →
  solver (1 blocco codice, o \boxed{} per math/choice). Round con feedback da tabella release.
- MISTA: esperti math/code/science → summarizer ("You may reference the three expert information").
- Trasferimento: learner ("Use the expert plan as guidance, but prioritize the task constraints").
- Ricerca: reflector <search>/<python> → <result> → \boxed{}.
- Passaggi inter-round = slot ufficiali (Initial/Refined Plan, feedback, result).
- Log esito in memory/recursive-results.jsonl nella root del progetto (crealo se manca; schema result_jsonl). Non cercare altri file: lavora inline. + judge {"true_false": bool}.
