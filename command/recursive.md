---
description: Protocollo RecursiveMAS dai file ufficiali citati
---

Applica il protocollo RECURSIVE alla richiesta `$ARGUMENTS` (fonti in agent/recursive.md):
- Routing ufficiale: CODE / CHOICE (A-D) / MATH / ricerca-esterna / mista / trasferimento.
- CODE/MATH: planner ("Do not write code" per codice, Step 1..n) → refiner pure-plan →
  solver (1 blocco codice, o \boxed{} per math/choice). Round con feedback: 3 default (2 su task veloci).
- MISTA: esperti math/code/science → summarizer ("You may reference the three expert information").
- Trasferimento: learner ("Use the expert plan as guidance, but prioritize the task constraints").
- Ricerca: reflector <search>/<python> → <result> → \boxed{}.
- Chiudi con judge JSON {"true_false": bool}; false → 1 riparazione.
