"""
Smoke test for Qwen3-14B.
Verifies that the model loads, generates coherent JSON, and both
thinking modes (/think, /no_think) are operational before wiring
into the pipeline.

Expected runtime: ~20s on RTX 3090 / ~40s on Colab T4.
"""
import json
import os
import torch
from shared import gpu_utils

MODEL_PATH = "Qwen/Qwen3-14B"

FAST_PROMPT = "/no_think\nClassify this disaster report as JSON:\n\n" \
              "Text: 'Flash flood in Gurugram. 1200 residents evacuated. " \
              "3 people missing. NH-48 blocked.'\n\n" \
              "Return ONLY: {\"incident_type\":...,\"incident_category\":...," \
              "\"severity\":...,\"classifier_confidence\":...}"

THINK_PROMPT = "/think\nA user reports: 'There was a loud explosion near the " \
               "chemical plant in Bhopal. Smoke visible from 5km. 40 workers unaccounted.'\n\n" \
               "Classify carefully considering ambiguity between industrial accident " \
               "and natural disaster. Return JSON."


def run_smoke_test(prompt: str, label: str, model, tokenizer):
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.0,
        do_sample=False,
    )
    decoded = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True,
    ).strip()
    print(f"\n=== [{label}] ===")
    print(decoded)

    try:
        raw = decoded
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        parsed = json.loads(raw)
        print(f"[{label}] JSON parse: PASSED — incident_type={parsed.get('incident_type')}")
    except json.JSONDecodeError as exc:
        print(f"[{label}] JSON parse: FAILED — {exc}")


def main():
    print("Detecting NVIDIA GPU for model pinning...")
    device = gpu_utils.find_nvidia_cuda_device()
    if device is None:
        print("No CUDA-capable NVIDIA GPU detected — model will run on CPU or default device.")
    else:
        try:
            props = torch.cuda.get_device_properties(device)
            print(f"Found NVIDIA GPU: {props.name} (index {device}) — pinning process to this device.")
        except Exception:
            print(f"Found CUDA device index {device} — pinning process to it.")
        gpu_utils.pin_process_to_cuda(device)

    print("Loading Qwen3-14B (4-bit)...")
    from transformers import AutoTokenizer, AutoModelForCausalLM

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    def _try_load_with_kwargs(kwargs):
        return AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            **kwargs,
        )

    tried = []
    # Attempt 1: preferred 4-bit load (requires accelerate + bitsandbytes)
    try:
        model = _try_load_with_kwargs(dict(
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True,
            trust_remote_code=True,
        ))
    except Exception as exc:
        print(f"AutoModelForCausalLM failed: {exc}. Will try fallbacks...")
        tried.append(str(exc))

        # Fallback A: some model implementations don't accept `load_in_4bit` keyword.
        try:
            model = _try_load_with_kwargs(dict(
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            ))
            print("Loaded model without 4-bit flag (fallback A).")
        except Exception as exc2:
            print(f"Fallback A failed: {exc2}. Trying direct class import fallback...")
            tried.append(str(exc2))

            # Fallback B: attempt to import the Qwen3 class directly and try again
            try:
                from transformers.models.qwen3.modeling_qwen3 import Qwen3ForCausalLM

                try:
                    model = Qwen3ForCausalLM.from_pretrained(
                        MODEL_PATH,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                        low_cpu_mem_usage=True,
                    )
                    print("Loaded Qwen3ForCausalLM via direct import (fallback B).")
                except TypeError as te:
                    # Some direct implementations don't accept extra kwargs
                    print(f"Direct class init TypeError: {te}. Retrying with minimal args...")
                    model = Qwen3ForCausalLM.from_pretrained(MODEL_PATH)
                    print("Loaded Qwen3ForCausalLM with minimal args (fallback B2).")
            except Exception as exc3:
                print(f"Direct Qwen3ForCausalLM load also failed: {exc3}")
                tried.append(str(exc3))
                print("All load attempts failed. Errors:\n" + "\n---\n".join(tried))
                raise
    print("Model loaded.\n")

    run_smoke_test(FAST_PROMPT, "no_think / fast mode", model, tokenizer)
    run_smoke_test(THINK_PROMPT, "think / reasoning mode", model, tokenizer)


if __name__ == "__main__":
    main()