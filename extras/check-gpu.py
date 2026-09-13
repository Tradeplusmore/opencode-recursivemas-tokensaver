"""Check in 10 secondi se il PC regge la RecursiveMAS vera (GPU + checkpoint).
Uso: python check-gpu.py
Esito: OK / PARZIALE / NO con motivi e prossimi passi.
"""
import os
import shutil
import sys

print("=" * 60)
print("Check MAS vera - GPU + RAM + disco + checkpoint + server")
print("=" * 60)

score = {"ok": [], "warn": [], "ko": []}

# 1. Python
print(f"\n[1] Python: {sys.version.split()[0]}")
score["ok"].append("python presente")

# 2. torch + CUDA
try:
    import torch
    cuda = torch.cuda.is_available()
    print(f"[2] torch {torch.__version__} - CUDA disponibile: {cuda}")
    if cuda:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            vram = p.total_memory / 1e9
            print(f"    GPU{i}: {p.name} - VRAM {vram:.1f} GB")
            if vram >= 14:
                score["ok"].append(f"GPU{i} {p.name} {vram:.0f}GB: ideale (>=14GB)")
            elif vram >= 7:
                score["warn"].append(f"GPU{i} {vram:.1f}GB: ok solo sequential_light (<8GB stretto)")
            else:
                score["ko"].append(f"GPU{i} {vram:.1f}GB: insufficiente (min 8GB)")
    else:
        score["ko"].append("CUDA non disponibile: MAS vera impraticabile su CPU")
except ImportError:
    print("[2] torch NON installato (pip install torch --index-url https://download.pytorch.org/whl/cu121)")
    score["warn"].append("torch mancante: installalo per testare CUDA")

# 3. RAM
try:
    import psutil
    ram = psutil.virtual_memory().total / 1e9
    print(f"[3] RAM: {ram:.1f} GB")
    (score["ok"] if ram >= 30 else score["warn"] if ram >= 14 else score["ko"]).append(
        f"RAM {ram:.0f}GB {'ok' if ram >= 16 else 'stretta/insufficiente (min 16GB)'}")
except ImportError:
    print("[3] RAM: psutil mancante, salto (pip install psutil)")
    score["warn"].append("psutil mancante")

# 4. Disco
free = shutil.disk_usage(os.path.expanduser("~")).free / 1e9
print(f"[4] Disco libero (home): {free:.1f} GB (servono ~20GB checkpoint)")
(score["ok"] if free >= 25 else score["warn"] if free >= 15 else score["ko"]).append(
    f"disco {free:.0f}GB {'ok' if free >= 20 else 'insufficiente'}")

# 5. huggingface-cli + checkpoint
hf = shutil.which("huggingface-cli")
print(f"[5] huggingface-cli: {'presente' if hf else 'mancante (pip install huggingface_hub)'}")
ckpts = []
for base in [os.getcwd(), os.path.expanduser("~/.config/opencode/recursivemas"),
             os.path.expanduser("~/RecursiveMAS")]:
    c = os.path.join(base, "checkpoints")
    if os.path.isdir(c):
        ckpts.append(c)
print(f"    cartelle checkpoints trovate: {ckpts if ckpts else 'nessuna'}")
if not ckpts:
    score["warn"].append("checkpoint assenti: da scaricare con huggingface-cli download")

# 6. Server locale 8001
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=3) as r:
        print(f"[6] server 8001: attivo ({r.status})")
        score["ok"].append("server 8001 attivo")
except Exception as e:
    print(f"[6] server 8001: spento ({type(e).__name__}) - normale se non serve MAS vera")
    score["warn"].append("server 8001 spento")

print("\n" + "=" * 60)
print(f"OK: {len(score['ok'])} | AVVISI: {len(score['warn'])} | BLOCCANTI: {len(score['ko'])}")
for s in score["ko"]:
    print(f"  [X] {s}")
for s in score["warn"]:
    print(f"  [!] {s}")
for s in score["ok"]:
    print(f"  [+] {s}")
print("=" * 60)
if score["ko"]:
    print("ESITO: NO - resta sul sistema text-level (quello attivo ora va benissimo).")
elif score["warn"]:
    print("ESITO: PARZIALE - text-level ok, MAS vera solo dopo aver sistemato gli avvisi.")
else:
    print("ESITO: OK - puoi installare checkpoint e accendere server.py.")
