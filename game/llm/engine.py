"""
game/llm/engine.py
LLM loader and inference module for MUTABAR.
Wraps llama-cpp-python with thread-safe generation using chat completion.
"""

import threading

_llm = None
_lock = threading.Lock()


def load_model(model_path, n_gpu_layers=-1, n_ctx=4096, n_threads=4):
    global _llm
    from llama_cpp import Llama
    _llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False,
    )


def is_loaded() -> bool:
    return _llm is not None


def generate(prompt, max_tokens=60, temperature=0.8):
    """Generate narration using chat completion format for Qwen3."""
    if _llm is None:
        raise RuntimeError("Model not loaded")
    with _lock:
        result = _llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You narrate creature battles. "
                        "Write exactly 1-2 short, vivid sentences. "
                        "No instructions. No meta. Just narrate."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt + " /no_think",
                },
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
    text = result["choices"][0]["message"]["content"].strip()
    text = _strip_think_tags(text)
    return text


def _strip_think_tags(text: str) -> str:
    """Remove Qwen3 <think>...</think> reasoning blocks from output."""
    import re
    # Case 1: complete <think>...</think> block
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # Case 2: unclosed <think> (model hit max_tokens before closing)
    if "<think>" in text:
        text = text[:text.index("<think>")].strip()
    # Case 3: text starts after </think> (thinking was at the start)
    if "</think>" in text:
        text = text[text.index("</think>") + len("</think>"):].strip()
    return text
