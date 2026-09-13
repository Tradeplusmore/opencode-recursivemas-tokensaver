"""Soluzione MAS vera SENZA GPU locale: Google Colab (T4 gratis) + ngrok.

La recursione latente (modeling.py + adapter + pesi) NON gira senza GPU.
Questa e' la via verificata-carta per averla comunque da OpenCode terminale:
il motore gira su Colab, OpenCode lo usa via URL remota.

PASSI (10 min, gratis):
  1. Apri https://colab.research.google.com -> nuovo notebook -> Runtime T4 GPU.
  2. Carica questo file + server.py della repo (o clona la repo GitHub).
  3. Esegui le celle SEZIONE 1..4 qui sotto (in Colab: copia ogni blocco in una cella).
  4. Copia l'URL ngrok stampato (https://xxxx.ngrok-free.app).
  5. Sul TUO pc (terminale OpenCode):
       set RECURSIVEMAS_URL=https://xxxx.ngrok-free.app/v1
       set ALLOW_REMOTE_MAS=1
       python %USERPROFILE%\\.config\\opencode\\recursivemas\\opencode-router.py --deep "domanda"
     MCP: aggiungi RECURSIVEMAS_URL + ALLOW_REMOTE_MAS=1 all'env del server MCP in opencode.jsonc.

Costi/limiti onesti: Colab free scade (~ore) e va riavviato; ngrok free ha URL che cambia;
latenza piu' alta. Per uso serio: RunPod/Vast GPU oraria (~0.30-0.50$/h), stesso schema.

Test locale possibile: python scripts/colab-mas.py --check (verifica solo i prerequisiti).
"""

# ============ SEZIONE 1 (cella Colab): dipendenze + repo ufficiale ============
COLAB_SETUP = r"""
!pip -q install torch --index-url https://download.pytorch.org/whl/cu121
!pip -q install fastapi uvicorn pydantic requests pyngrok huggingface_hub
!git clone https://github.com/RecursiveMAS/RecursiveMAS.git
!git clone https://github.com/Tradeplusmore/opencode-recursivemas-tokensaver.git
"""

# ============ SEZIONE 2 (cella Colab): login HF + avvio server + tunnel ============
COLAB_RUN = r"""
import os
os.environ["MAS_REPO"] = "/content/RecursiveMAS"
os.environ["MAS_STYLE"] = "sequential_light"   # T4 16GB: light ok, scaled stretto
os.environ["MAS_DATASET"] = "math500"
os.environ["MAS_DEVICE"] = "cuda"
# incolla il tuo token HF (read-only basta) e ngrok:
# https://huggingface.co/settings/tokens | https://dashboard.ngrok.com/get-started/your-authtoken
from huggingface_hub import login; login("HF_TOKEN_QUI")
from pyngrok import ngrok; ngrok.set_auth_token("NGROK_TOKEN_QUI")

import threading, sys
sys.path.insert(0, "/content/opencode-recursivemas-tokensaver/recursivemas")
import server as mas_server, uvicorn
threading.Thread(target=lambda: uvicorn.run(mas_server.app, host="127.0.0.1", port=8001),
                 daemon=True).start()
url = ngrok.connect(8001, "http")
print("COPIA QUESTO URL SU PC LOCALE:", str(url).replace("http://", "https://"))
print("Health locale colab:", "http://127.0.0.1:8001/health")
"""

# ============ SEZIONE 3 (pc locale): test connessione remota ============
LOCAL_TEST = r"""
# PowerShell sul tuo pc:
#   $env:RECURSIVEMAS_URL="https://xxxx.ngrok-free.app/v1"
#   $env:ALLOW_REMOTE_MAS="1"
#   curl "$env:RECURSIVEMAS_URL/../health".Replace('/v1','')
#   python %USERPROFILE%\.config\opencode\recursivemas\opencode-router.py --deep "Calcola 23 x 47"
"""

if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        import shutil
        print("pyngrok:", "ok" if shutil.which("ngrok") else "manca (pip install pyngrok)")
        print("Istruzioni stampate sopra: SEZIONE 1/2 in Colab, SEZIONE 3 in locale.")
        print("NOTA: template verificato-sintassi, esecuzione Colab da fare con T4 attivo.")
    else:
        print(COLAB_SETUP)
        print(COLAB_RUN)
        print(LOCAL_TEST)
