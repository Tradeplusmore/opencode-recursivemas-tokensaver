# Pesi-ruolo ufficiali su CPU (testato, funzionante, 0 GPU)

I 3 modelli-ruolo ufficiali `sequential_light` girano sulla tua CPU via Ollama:
- `recursivemas-planner` = Sequential-Light-Planner-Qwen3-1.7B (GGUF Q8, 2.2GB)
- `recursivemas-critic` = Sequential-Light-Critic-Llama3.2-1B (GGUF Q8, 1.3GB)
- `recursivemas-solver` = Sequential-Light-Solver-Qwen2.5-Math-1.5B (GGUF Q8, 1.6GB)

## Test eseguito (2026-09-13, i7-like 6 thread, 17GB RAM, solo CPU)
`--local --code "fattoriale"` = 87s, SOLVE corretto (`factorial` + `\boxed{120}`).
Planner tende a ripetersi senza canale latente, critic+refiner lo riparano.

## Come replicare (serve ~20GB disco, git + python)
```powershell
cd $env:USERPROFILE\.config\opencode\recursivemas\cpu-roles
git clone https://huggingface.co/RecursiveMAS/Sequential-Light-Planner-Qwen3-1.7B planner
git clone https://huggingface.co/RecursiveMAS/Sequential-Light-Critic-Llama3.2-1B critic
git clone https://huggingface.co/RecursiveMAS/Sequential-Light-Solver-Qwen2.5-Math-1.5B solver
# NOTA: huggingface-cli ha problemi SSL dietro proxy -> usare git clone (usa cert store Windows).
# Conversione (serve llmtools/ + gguf + transformers==4.57.1):
#  critic: fix tokenizer_class TokenizersBackend->LlamaTokenizerFast, specials fissati, vocab 128256
#  planner/solver: extra_special_tokens []->{} , padding tokenizer a 151936 dummy
python llmtools/convert_hf_to_gguf.py critic_conv --outfile critic-q8.gguf --outtype q8_0
# ... idem planner/solver, poi:
ollama create recursivemas-planner -f Modelfile.planner  # ecc.
```

## Uso quotidiano
```powershell
ollama serve
$env:PYTHONUTF8=1
python ...\recursivemas\opencode-router.py --local [--code] "domanda"
```

## Limiti onesti
- Lento (~1-2 min/domanda). Per il quotidiano resta meglio l'agent nativo istantaneo.
- Adapter latenti (`adapter*.pt`, `innerlink_config.json`) NON usati: richiedono torch+CUDA.
  Senza, il planner a volte loopa; il critic lo corregge quasi sempre.
- GGUF e pesi NON committati (vedi .gitignore).
