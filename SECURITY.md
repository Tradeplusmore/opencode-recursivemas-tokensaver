# Security Policy
- Il server FastAPI binda solo `127.0.0.1:8001`, nessuna auth (volutamente locale).
- Non esporre mai su `0.0.0.0` senza auth/reverse-proxy.
- Input troncato a 8000 char, `max_tokens` clampato 1-2048, errori generici al client.
- `RECURSIVEMAS_URL` remoto bloccato salvo `ALLOW_REMOTE_MAS=1`.
- Cache locale `.recursivemas_cache.json` con chmod 600, non committarla.
