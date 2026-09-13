@echo off
REM Setup pesi-ruolo ufficiali RecursiveMAS per CPU via Ollama (GGUF Q4, ~2.5GB RAM, 0 GPU).
REM Richiede: ollama serve attivo + python + ~8GB disco temporanei + huggingface-cli login.
REM Esecuzione lunga (download+conversione, anche 1h). Alla fine:
REM   set OLLAMA_PLANNER=recursivemas-planner & set OLLAMA_CRITIC=recursivemas-critic & set OLLAMA_SOLVER=recursivemas-solver
setlocal
set ROLES_DIR=%~dp0..\cpu-roles
mkdir "%ROLES_DIR%" 2>nul
cd /d "%ROLES_DIR%"
echo [1/4] Download repo ruolo sequential_light (planner/critic/solver)...
huggingface-cli download RecursiveMAS/Sequential-Light-Planner-Qwen3-1.7B --local-dir planner
huggingface-cli download RecursiveMAS/Sequential-Light-Critic-Llama3.2-1B --local-dir critic
huggingface-cli download RecursiveMAS/Sequential-Light-Solver-Qwen2.5-Math-1.5B --local-dir solver
echo [2/4] Tool conversione llama.cpp...
git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
pip install -q -r llama.cpp\requirements\requirements-convert_hf_to_gguf.txt
echo [3/4] Conversione + quantizzazione Q4_K_M...
python llama.cpp\convert_hf_to_gguf.py planner --outfile planner-f16.gguf --outtype f16
llama.cpp\build\bin\Release\llama-quantize.exe planner-f16.gguf planner-q4.gguf Q4_K_M
python llama.cpp\convert_hf_to_gguf.py critic --outfile critic-f16.gguf --outtype f16
llama.cpp\build\bin\Release\llama-quantize.exe critic-f16.gguf critic-q4.gguf Q4_K_M
python llama.cpp\convert_hf_to_gguf.py solver --outfile solver-f16.gguf --outtype f16
llama.cpp\build\bin\Release\llama-quantize.exe solver-f16.gguf solver-q4.gguf Q4_K_M
echo [4/4] Import in Ollama...
ollama create recursivemas-planner -f ..\scripts\Modelfile.planner
ollama create recursivemas-critic -f ..\scripts\Modelfile.critic
ollama create recursivemas-solver -f ..\scripts\Modelfile.solver
echo FATTO. Usa: opencode-router.py --local con OLLAMA_* impostati sui 3 modelli.
