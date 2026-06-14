"""
Downloads Qwen3-14B from HuggingFace Hub into the local model cache.

Design rationale:
- Uses snapshot_download to fetch all shards and tokenizer files atomically.
- HF_TOKEN env var supports gated or rate-limited repos.
- LOCAL_DIR keeps models outside the app/ source tree.
"""
import os
from huggingface_hub import snapshot_download

MODEL_ID = "Qwen/Qwen3-14B"
LOCAL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "Qwen3-14B")


def download():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    print(f"[download] Pulling {MODEL_ID} → {LOCAL_DIR}")
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=LOCAL_DIR,
        local_dir_use_symlinks=False,
        token=os.getenv("HF_TOKEN"),
    )
    print("[download] Complete.")


if __name__ == "__main__":
    download()