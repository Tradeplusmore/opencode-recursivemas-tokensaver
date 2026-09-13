---
description: Risolvi con protocollo RecursiveMAS plan-critic-solve a budget ridotto
---

Applica il protocollo RECURSIVE alla richiesta `$ARGUMENTS` usando SOLO capacita' native (nessun tool esterno):
1) PLAN 3-5 punti (1 riga ciascuno) 2) CRITIC 1 rischio per punto 3) SOLVE + `RISULTATO:` in 2 righe.
Per codice: planner 3-6 step senza codice, refiner senza codice, solver con UN solo blocco codice. Per COMPLEX: 3 round (plan→critic→refined v1→avversario→v2→solve), tutto inline.
