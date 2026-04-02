"""
game/llm/engine.py
LLM loader and inference module for MUTABAR.
Wraps llama-cpp-python with thread-safe generation.
"""

import threading

_llm = None
_lock = threading.Lock()


def load_model(model_path, n_gpu_layers=-1, n_ctx=1024, n_threads=4):
    global _llm
    from llama_cpp import Llama
    _llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False,
    )


def apply_lora(lora_path):
    if _llm is None:
        raise RuntimeError("Model not loaded")
    # Note: llama-cpp-python LoRA API may vary; this is a placeholder
    # _llm.set_lora(lora_path)
    pass


def generate(prompt, max_tokens=80, temperature=0.7):
    if _llm is None:
        raise RuntimeError("Model not loaded")
    with _lock:
        result = _llm.create_completion(prompt, max_tokens=max_tokens, temperature=temperature)
    return result["choices"][0]["text"].strip()


def generate_stream(prompt, max_tokens=80, temperature=0.7):
    if _llm is None:
        raise RuntimeError("Model not loaded")
    with _lock:
        for chunk in _llm.create_completion(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        ):
            token = chunk["choices"][0]["text"]
            if token:
                yield token
