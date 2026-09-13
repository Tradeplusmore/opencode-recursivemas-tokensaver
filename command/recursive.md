---
description: Protocollo RecursiveMAS nativo (4 famiglie, zero dipendenze)
---

Applica il protocollo RECURSIVE alla richiesta `$ARGUMENTS`, solo capacita' native:
- Classifica: SIMPLE (8 righe) / CODE / MATH / MISTA / RICERCA / DURO.
- CODE/MATH: planner Step 1..n senza soluzione → refiner pure-plan → solver (1 blocco codice o \boxed{}).
- MISTA: 3 esperti (math/code/science) in parallelo → summarizer con RISULTATO.
- RICERCA: cicli think <search>/<python> → <result>, max 3, chiudi \boxed{}.
- DURO: 3 round con feedback (v1 → avversario → v2 → solve).
- Mai tool esterni, mai ripetizioni.
