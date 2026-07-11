#!/usr/bin/env python3
"""
Merge LoRA adapter into base model for standalone deployment.

Usage:
  python3 scripts/merge_lora.py                    # Merge with default paths
  python3 scripts/merge_lora.py --dtype float16    # Specify dtype (default: float16)

Output: models/intent-0.5b-v1/merged/ — standalone model, no peft dependency needed.
"""

import argparse
import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASE = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
DEFAULT_ADAPTER = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "sft-checkpoint")
DEFAULT_OUTPUT = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "merged")


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Path to base model")
    parser.add_argument("--adapter", default=DEFAULT_ADAPTER, help="Path to LoRA adapter checkpoint")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path for merged model")
    parser.add_argument("--dtype", default="float16", choices=["float16", "float32"], help="Output dtype")
    args = parser.parse_args()

    dtype_map = {"float16": torch.float16, "float32": torch.float32}
    torch_dtype = dtype_map[args.dtype]

    print("=" * 60)
    print("LoRA Merge: base + adapter → standalone model")
    print("=" * 60)
    print(f"  Base:    {args.base}")
    print(f"  Adapter: {args.adapter}")
    print(f"  Output:  {args.output}")
    print(f"  Dtype:   {args.dtype}")
    print()

    start = time.time()

    # 1. Load base model
    print("[1/4] Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        trust_remote_code=True,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )
    print(f"  Base model loaded ({args.dtype})")

    # 2. Load tokenizer
    print("[2/4] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.adapter, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"  Tokenizer loaded, vocab: {len(tokenizer)}")

    # 3. Load LoRA adapter and merge
    print("[3/4] Loading LoRA adapter and merging...")
    model = PeftModel.from_pretrained(model, args.adapter)
    print("  LoRA adapter loaded")

    model = model.merge_and_unload()
    print("  Merged! LoRA weights folded into base model")

    # 4. Save
    print("[4/4] Saving merged model...")
    os.makedirs(args.output, exist_ok=True)
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    print(f"  Saved to {args.output}")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")
    print(f"\nMerged model can now be loaded with:")
    print(f'  AutoModelForCausalLM.from_pretrained("{args.output}")')
    print(f"  (No peft dependency needed)")


if __name__ == "__main__":
    main()
