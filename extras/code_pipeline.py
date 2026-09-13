"""Port testuale (senza GPU/torch) dei prompt ufficiali RecursiveMAS.

Fonte: https://github.com/RecursiveMAS/RecursiveMAS (MIT, (c) 2026 RecursiveMAS)
File originali: inference/prompts.py + train/mas_prompt.py (659+664 righe).
Vendored in recursivemas/vendor/ per riferimento.

Cosa e' integrabile SENZA GPU: tutti i builder testuali sotto (planner/refiner/solver
code, expert math/code/science, final instruction boxed, deliberation tool pattern).
Cosa NON e' integrabile senza GPU/pesi: gli SLOT latenti (<<LATENT_*>>) — la collaborazione
vera avviene negli hidden states via RecursiveLink (inference/modeling.py). Qui gli slot
sono sostituiti dal passaggio testuale planner->refiner->solver.

Uso da terminale OpenCode:
    from code_pipeline import code_planner_prompt, code_refiner_prompt, code_solver_prompt
    python opencode-router.py --code "scrivi funzione fibonacci"
"""


def code_interface(task_type: str = "complete", fn_name=None) -> str:
    mode = "function" if str(task_type or "").lower() in {"function", "functional"} else "complete"
    if mode == "function":
        return f"Implement and return the function `{fn_name}` only." if fn_name else \
            "Implement and return the required function only."
    return "Write a complete program that reads from stdin and prints to stdout."


def code_planner_prompt(question: str, task_type: str = "complete", fn_name=None) -> str:
    interface = code_interface(task_type, fn_name)
    return (
        "You are a planner agent in a multi-agent coding system.\n"
        f"{interface}\n"
        "The programming problem is:\n"
        f"{question}\n"
        "Provide a clear step-by-step plan (within 3-6 steps) to solve the problem.\n"
        "Do not write code.\n"
        "Your response should be in the format of:\n"
        "Step 1: ...\n"
        "...\n"
        "Step n: ..."
    )


def code_refiner_prompt(question: str, planner_output: str,
                        task_type: str = "complete", fn_name=None) -> str:
    interface = code_interface(task_type, fn_name)
    return (
        "You are a refiner agent in a multi-agent coding system.\n"
        f"{interface}\n"
        "\n---\nThe programming problem is:\n"
        f"{question}\n"
        "The initial plan from the planner:\n"
        "Initial Plan:\n"
        f"{planner_output}\n"
        "Refine the plan into a clearer and stronger step-by-step plan (within 3-6 steps).\n"
        "Do not write code.\n"
        "Your response should be in the format of:\n"
        "Step 1: ...\n"
        "...\n"
        "Step n: ..."
    )


def code_solver_prompt(question: str, refined_plan: str,
                       task_type: str = "complete", fn_name=None) -> str:
    interface = code_interface(task_type, fn_name)
    return (
        "You are a solver agent in a multi-agent coding system.\n"
        f"{interface}\n"
        "Here is the refined plan:\n"
        "Refined Plan:\n"
        f"{refined_plan}\n"
        "\n---\nThe programming problem is:\n"
        f"{question}\n"
        "Solve the problem and put the final code inside one markdown code block, "
        "for example ```python\n<your solution code>\n```."
    )


def expert_prompt(question: str, role: str = "math", mas_task: str = "math") -> str:
    labels = {"math": "math expert", "code": "code expert", "science": "science expert"}
    if role not in labels:
        raise ValueError(f"role deve essere math/code/science, non {role}")
    return (
        f"You are the {labels[role]} in a multi-agent system.\n"
        "The question is:\nQuestion:\n"
        f"{question}\n"
        "Solve the question and put the final answer inside \\boxed{}, for example \\boxed{1}."
    )


DELIBERATION_NOTE = (
    "Deliberation pattern (ufficiale, adattato a OpenCode senza GPU): "
    "ragiona passo-passo; per fatti esterni usa i tool disponibili (web/file) e "
    "riporta query e risultati come <search>q</search>/<result>r</result>; "
    "per calcoli usa script/python e riporta come <python>code</python>/<result>out</result>; "
    "chiudi con risposta esatta in \\boxed{}."
)
