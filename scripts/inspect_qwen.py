#!/usr/bin/env python3
import importlib
import traceback
from transformers import AutoConfig, AutoModelForCausalLM

try:
    cfg = AutoConfig.from_pretrained("Qwen/Qwen3-14B")
    print('config model_type:', cfg.model_type, 'config class', type(cfg))
    mapping = AutoModelForCausalLM._model_mapping
    print('mapping keys sample:', list(mapping.keys())[:5])
    print('has type?', type(cfg) in mapping)
    module = mapping.get(type(cfg))
    print('module', module)
    if module:
        mod = importlib.import_module(module)
        print('module file', getattr(mod, '__file__', None))
        print([n for n in dir(mod) if 'Qwen' in n or 'ForCausal' in n or 'Qwen3' in n])
    try:
        cls = AutoModelForCausalLM._get_model_class(cfg, mapping)
        print('Resolved class:', cls)
    except Exception:
        traceback.print_exc()
except Exception:
    traceback.print_exc()
