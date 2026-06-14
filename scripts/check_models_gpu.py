#!/usr/bin/env python3
"""Check GPU availability and model backend configs.

This script performs lightweight checks to help ensure models are run on
an NVIDIA GPU (CUDA) rather than an integrated GPU. It checks:
 - PyTorch CUDA availability
 - bitsandbytes availability (for 4-bit loading)
 - whether docker-compose has GPU configured for Ollama

Run: `python scripts/check_models_gpu.py`
"""
import os
import sys
import json
import subprocess

def check_torch():
    try:
        import torch
        print(f"torch version: {torch.__version__}")
        cuda = torch.cuda.is_available()
        print(f"torch.cuda.is_available: {cuda}")
        if cuda:
            try:
                cnt = torch.cuda.device_count()
                names = [torch.cuda.get_device_name(i) for i in range(cnt)]
                print(f"CUDA devices ({cnt}): {names}")
            except Exception as e:
                print("Failed to enumerate CUDA devices:", e)
        else:
            print("CUDA not available. Ensure NVIDIA drivers + CUDA toolkit are installed.")
    except Exception as e:
        print("PyTorch not installed or import failed:", e)

def check_bitsandbytes():
    try:
        import bitsandbytes as bnb
        print("bitsandbytes available, version:", getattr(bnb, '__version__', 'unknown'))
    except Exception as e:
        print("bitsandbytes not available or failed to import:", e)

def check_docker_gpu_in_compose():
    # simple parse of docker-compose.full.yml to look for 'gpus' under 'ollama'
    comp = os.path.join(os.path.dirname(__file__), '..', 'docker-compose.full.yml')
    if not os.path.exists(comp):
        print("docker-compose.full.yml not found; skipping compose GPU check")
        return
    try:
        with open(comp, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        # naive check
        in_ollama = 'ollama:' in txt
        gpus = 'gpus:' in txt and 'ollama' in txt.split('gpus:')[0].split('\n')[-1]
        if 'ollama:' in txt and 'gpus:' in txt:
            print("docker-compose: ollama service declares 'gpus:' (good)")
        else:
            print("docker-compose: ollama service does not declare 'gpus:'. Add 'gpus: all' to enable GPU for Ollama.")
    except Exception as e:
        print("docker-compose parse failed:", e)

def check_nvidia_smi():
    try:
        out = subprocess.check_output(['nvidia-smi', '--query-gpu=name,index,memory.total', '--format=csv,noheader'], stderr=subprocess.STDOUT)
        print('nvidia-smi output:')
        print(out.decode())
    except FileNotFoundError:
        print('nvidia-smi not found on PATH — NVIDIA drivers may not be installed or not in PATH')
    except subprocess.CalledProcessError as e:
        print('nvidia-smi returned error:', e.output.decode() if e.output else e)

def main():
    print('--- GPU / model backend check ---')
    check_torch()
    print('')
    check_bitsandbytes()
    print('')
    check_nvidia_smi()
    print('')
    check_docker_gpu_in_compose()
    print('\nNotes:')
    print('- For Ollama Docker to use the GPU, run Docker with GPU support and ensure docker-compose has `gpus: all` for the ollama service.')
    print('- For Transformers (scripts/verify_model.py) the code uses device_map="auto" and load_in_4bit; ensure CUDA is available and bitsandbytes installed.')

if __name__ == '__main__':
    main()
