"""
Downloads the Q4_K_M quantized GGUF of Qwen3-14B for Ollama / llama.cpp.

Q4_K_M at 14B parameters:
  - VRAM: ~7–9 GB (fits RTX 3060 12GB, Colab T4 16GB)
  - Quality: ~97% of FP16 on classification tasks
  - Speed: 135 tok/s on RTX 4090, ~60–80 tok/s on RTX 3090

This is the recommended quantization for hackathon and single-GPU deployments.
"""
import os
from huggingface_hub import hf_hub_download

REPO_ID = "bartowski/Qwen3-14B-GGUF"
FILENAME = "Qwen3-14B-Q4_K_M.gguf"
LOCAL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "gguf")


def download():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=LOCAL_DIR,
        token=os.getenv("HF_TOKEN"),
    )
    print(f"[download_gguf] GGUF saved → {path}")


if __name__ == "__main__":
    download()