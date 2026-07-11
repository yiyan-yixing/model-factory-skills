#!/usr/bin/env python3
"""
Evaluate intent classification + query rewriting model.

Metrics:
- Coarse intent accuracy (6 classes)
- Fine intent accuracy (sub_intent)
- Per-class F1 score
- Rewrite quality (JSON parse rate)
"""

import json
import os
import re
import sys
import numpy as np
from collections import Counter

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
CHECKPOINT_DIR = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "sft-checkpoint")
DATA_DIR = os.path.join(PROJECT_DIR, "data", "intent")


def parse_output(text):
    """Parse model output to extract intent JSON."""
    # Try to find JSON in the response
    # Look for content after ### Response:
    if "### Response:" in text:
        text = text.split("### Response:")[-1].strip()

    # Try direct JSON parse
    try:
        result = json.loads(text)
        if "intent" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return result
        except json.JSONDecodeError:
            pass

    return None


def evaluate():
    print("=" * 60)
    print("Evaluation: Intent Classification + Query Rewriting")
    print("=" * 60)

    # Load test data
    test_path = os.path.join(DATA_DIR, "test.json")
    with open(test_path, 'r') as f:
        test_data = json.load(f)
    print(f"Test samples: {len(test_data)}")

    # Load model
    print("\n--- Loading Model ---")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT_DIR, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(model, CHECKPOINT_DIR)
    model.eval()
    print("Model loaded")

    # Evaluate
    print("\n--- Running Evaluation ---")
    correct_coarse = 0
    correct_fine = 0
    parse_success = 0
    total = len(test_data)

    y_true_coarse = []
    y_pred_coarse = []
    y_true_fine = []
    y_pred_fine = []

    errors = []

    for i, item in enumerate(test_data):
        # Ground truth
        gt = json.loads(item["output"])

        # Generate
        prompt = (
            f"### Instruction:\n{item['instruction']}\n\n"
            f"### Input:\n{item['input']}\n\n"
            f"### Response:\n"
        )
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                temperature=1.0,
                pad_token_id=tokenizer.pad_token_id,
            )

        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        # Parse
        parsed = parse_output(generated_text)

        if parsed is not None:
            parse_success += 1
            pred_intent = parsed.get("intent", "unknown")
            pred_sub = parsed.get("sub_intent", "unknown")

            if pred_intent == gt["intent"]:
                correct_coarse += 1
            if pred_sub == gt["sub_intent"]:
                correct_fine += 1

            y_true_coarse.append(gt["intent"])
            y_pred_coarse.append(pred_intent)
            y_true_fine.append(gt["sub_intent"])
            y_pred_fine.append(pred_sub)
        else:
            y_true_coarse.append(gt["intent"])
            y_pred_coarse.append("parse_error")
            y_true_fine.append(gt["sub_intent"])
            y_pred_fine.append("parse_error")
            if len(errors) < 10:
                errors.append({
                    "input": item["input"],
                    "gt": gt,
                    "raw_output": generated_text[:200],
                })

        if (i + 1) % 50 == 0:
            print(f"  Evaluated {i+1}/{total} | Coarse acc: {correct_coarse/(i+1):.3f} | Parse rate: {parse_success/(i+1):.3f}")

    # ============================================================
    # Results
    # ============================================================
    coarse_acc = correct_coarse / total
    fine_acc = correct_fine / total
    parse_rate = parse_success / total

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Coarse intent accuracy: {coarse_acc:.4f} ({correct_coarse}/{total})")
    print(f"Fine intent accuracy:   {fine_acc:.4f} ({correct_fine}/{total})")
    print(f"JSON parse rate:        {parse_rate:.4f} ({parse_success}/{total})")

    # Per-class F1 (coarse)
    print("\n--- Per-class Coarse Intent ---")
    all_intents = sorted(set(y_true_coarse + y_pred_coarse))
    for intent in all_intents:
        tp = sum(1 for t, p in zip(y_true_coarse, y_pred_coarse) if t == intent and p == intent)
        fp = sum(1 for t, p in zip(y_true_coarse, y_pred_coarse) if t != intent and p == intent)
        fn = sum(1 for t, p in zip(y_true_coarse, y_pred_coarse) if t == intent and p != intent)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"  {intent:12s} | P: {precision:.3f} | R: {recall:.3f} | F1: {f1:.3f} | support: {tp+fn}")

    # Go/No-Go
    print("\n--- Go/No-Go ---")
    go = coarse_acc >= 0.90 and fine_acc >= 0.85 and parse_rate >= 0.90
    if go:
        print(f"✅ GO — Coarse acc {coarse_acc:.2%} (≥90%), Fine acc {fine_acc:.2%} (≥85%), Parse rate {parse_rate:.2%} (≥90%)")
    else:
        reasons = []
        if coarse_acc < 0.90:
            reasons.append(f"Coarse acc {coarse_acc:.2%} < 90%")
        if fine_acc < 0.85:
            reasons.append(f"Fine acc {fine_acc:.2%} < 85%")
        if parse_rate < 0.90:
            reasons.append(f"Parse rate {parse_rate:.2%} < 90%")
        print(f"❌ NO-GO — {'; '.join(reasons)}")

    # Show parse errors
    if errors:
        print(f"\n--- Parse Errors ({len(errors)} shown) ---")
        for e in errors:
            print(f"  Input: {e['input']}")
            print(f"  GT: {e['gt']}")
            print(f"  Raw: {e['raw_output']}")
            print()

    # Save results
    results = {
        "coarse_accuracy": coarse_acc,
        "fine_accuracy": fine_acc,
        "parse_rate": parse_rate,
        "total_samples": total,
        "go_no_go": "Go" if go else "No-Go",
    }
    results_path = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "eval_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    evaluate()
