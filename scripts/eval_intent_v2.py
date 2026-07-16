#!/usr/bin/env python3
"""
Comprehensive evaluation for intent classification + query rewriting model (v2).

Evaluates on both eval.json and test.json, with:
- Coarse intent accuracy and macro F1
- Fine intent (sub_intent) accuracy and macro F1
- Per-intent F1 breakdown (focus on tool class)
- Per-sub_intent F1 breakdown
- JSON parse rate
- Go/No-Go decision

Output saved to biz/model/registry/intent-0.5b-v2/eval_results.json

P0-2 fix (2026-07-16): Accuracy denominator now uses evaluated count (not total),
excluding samples with unparseable ground truth.
P1-5 fix (2026-07-16): parse_error/generate_error excluded from F1 computation.
"""

import json
import os
import re
import sys
import numpy as np
from collections import Counter, defaultdict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
CHECKPOINT_DIR = os.path.join(PROJECT_DIR, "..", "..", "biz", "model", "registry", "intent-0.5b-v2", "best_model")
CHECKPOINT_DIR = os.path.abspath(CHECKPOINT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data", "intent")
RESULTS_DIR = os.path.join(PROJECT_DIR, "..", "..", "biz", "model", "registry", "intent-0.5b-v2")
RESULTS_DIR = os.path.abspath(RESULTS_DIR)

# Go/No-Go thresholds
COARSE_ACC_THRESHOLD = 0.90
FINE_ACC_THRESHOLD = 0.85
PARSE_RATE_THRESHOLD = 0.90

# Device auto-detection: MPS > CPU
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
    DEVICE_NAME = "MPS (Apple Silicon)"
else:
    DEVICE = torch.device("cpu")
    DEVICE_NAME = "CPU"


def parse_output(text):
    """Parse model output to extract intent JSON."""
    if "### Response:" in text:
        text = text.split("### Response:")[-1].strip()

    try:
        result = json.loads(text)
        if "intent" in result:
            return result
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return result
        except json.JSONDecodeError:
            pass

    return None


def compute_f1(y_true, y_pred, labels=None):
    """Compute per-class and macro F1. Excludes artificial classes (parse_error etc)."""
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))

    # Filter out artificial error classes from F1 computation
    skip_labels = {"parse_error", "generate_error", "unknown"}
    real_labels = [l for l in labels if l not in skip_labels]

    per_class = {}
    f1s = []
    for label in real_labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        support = tp + fn
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
        if support > 0:
            f1s.append(f1)

    macro_f1 = np.mean(f1s) if f1s else 0
    weighted_f1 = sum(per_class[l]["f1"] * per_class[l]["support"] for l in real_labels if l in per_class) / max(sum(per_class[l]["support"] for l in real_labels if l in per_class), 1)

    return per_class, round(macro_f1, 4), round(weighted_f1, 4)


def evaluate_split(model, tokenizer, data, split_name):
    """Evaluate model on a data split, return metrics dict."""
    print(f"\n{'='*60}")
    print(f"Evaluating on {split_name} ({len(data)} samples)")
    print(f"{'='*60}")

    correct_coarse = 0
    correct_fine = 0
    parse_success = 0
    evaluated = 0  # P0-2 fix: track actually evaluated samples
    skipped_gt = 0
    total = len(data)

    y_true_coarse = []
    y_pred_coarse = []
    y_true_fine = []
    y_pred_fine = []

    errors = []

    for i, item in enumerate(data):
        # Ground truth
        try:
            gt = json.loads(item["output"])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [!] Skipping sample {i}: invalid ground truth - {e}")
            skipped_gt += 1
            continue

        evaluated += 1  # P0-2 fix: only count samples with valid GT

        # Generate
        prompt = (
            f"### Instruction:\n{item['instruction']}\n\n"
            f"### Input:\n{item['input']}\n\n"
            f"### Response:\n"
        )
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        try:
            with torch.inference_mode():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=128,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )
        except RuntimeError as e:
            print(f"  [!] Generate failed for sample {i}: {e}")
            # P1-5 fix: exclude generate_error from F1
            y_true_coarse.append(gt["intent"])
            y_pred_coarse.append("generate_error")
            y_true_fine.append(gt["sub_intent"])
            y_pred_fine.append("generate_error")
            if DEVICE.type == "mps":
                torch.mps.empty_cache()
            continue

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
            # P1-5 fix: exclude parse_error from F1 computation
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
            print(f"  Evaluated {evaluated}/{total} | Coarse acc: {correct_coarse/evaluated:.3f} | Fine acc: {correct_fine/evaluated:.3f} | Parse rate: {parse_success/evaluated:.3f}")

    # P0-2 fix: use evaluated count (not total) as denominator
    coarse_acc = correct_coarse / max(evaluated, 1)
    fine_acc = correct_fine / max(evaluated, 1)
    parse_rate = parse_success / max(evaluated, 1)

    # Coarse intent F1 (parse_error/generate_error excluded by compute_f1)
    coarse_labels = sorted(set(y_true_coarse) | set(y_pred_coarse))
    coarse_per_class, coarse_macro_f1, coarse_weighted_f1 = compute_f1(y_true_coarse, y_pred_coarse, coarse_labels)

    # Fine intent F1
    fine_labels = sorted(set(y_true_fine) | set(y_pred_fine))
    fine_per_class, fine_macro_f1, fine_weighted_f1 = compute_f1(y_true_fine, y_pred_fine, fine_labels)

    # Print results
    print(f"\n--- {split_name} Results ---")
    print(f"Coarse intent accuracy:  {coarse_acc:.4f} ({correct_coarse}/{evaluated})")
    print(f"Fine intent accuracy:    {fine_acc:.4f} ({correct_fine}/{evaluated})")
    print(f"JSON parse rate:         {parse_rate:.4f} ({parse_success}/{evaluated})")
    print(f"Skipped (bad GT):        {skipped_gt}")
    print(f"Coarse macro F1:         {coarse_macro_f1:.4f}")
    print(f"Coarse weighted F1:      {coarse_weighted_f1:.4f}")
    print(f"Fine macro F1:           {fine_macro_f1:.4f}")
    print(f"Fine weighted F1:        {fine_weighted_f1:.4f}")

    # Per-class coarse F1
    print(f"\n--- Per-class Coarse Intent ({split_name}) ---")
    for intent in sorted(coarse_per_class.keys()):
        m = coarse_per_class[intent]
        marker = " <<<" if intent == "tool" else ""
        print(f"  {intent:12s} | P: {m['precision']:.3f} | R: {m['recall']:.3f} | F1: {m['f1']:.3f} | support: {m['support']}{marker}")

    # Per-class fine F1 (grouped by coarse intent)
    print(f"\n--- Per-class Sub-Intent F1 ({split_name}) ---")
    schema_path = os.path.join(DATA_DIR, "schema.json")
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    for coarse_intent in schema["sub_intents"]:
        print(f"\n  [{coarse_intent}]")
        for sub in schema["sub_intents"][coarse_intent]:
            if sub in fine_per_class:
                m = fine_per_class[sub]
                marker = " <<<" if coarse_intent == "tool" else ""
                print(f"    {sub:15s} | P: {m['precision']:.3f} | R: {m['recall']:.3f} | F1: {m['f1']:.3f} | support: {m['support']}{marker}")
            else:
                print(f"    {sub:15s} | (not in predictions/ground truth)")

    # Show parse errors
    if errors:
        print(f"\n--- Parse Errors ({len(errors)} shown, {split_name}) ---")
        for e in errors:
            print(f"  Input: {e['input']}")
            print(f"  GT: {e['gt']}")
            print(f"  Raw: {e['raw_output']}")
            print()

    return {
        "coarse_accuracy": round(coarse_acc, 4),
        "fine_accuracy": round(fine_acc, 4),
        "parse_rate": round(parse_rate, 4),
        "coarse_macro_f1": coarse_macro_f1,
        "coarse_weighted_f1": coarse_weighted_f1,
        "fine_macro_f1": fine_macro_f1,
        "fine_weighted_f1": fine_weighted_f1,
        "coarse_per_class": coarse_per_class,
        "fine_per_class": fine_per_class,
        "total_samples": total,
        "evaluated_samples": evaluated,
        "skipped_gt": skipped_gt,
        "parse_errors_count": evaluated - parse_success,
        "device": DEVICE_NAME,
    }


def main():
    print("=" * 60)
    print("Comprehensive Evaluation: Intent Classification V2")
    print(f"Checkpoint: {CHECKPOINT_DIR}")
    print(f"Device: {DEVICE_NAME}")
    print("=" * 60)

    # Load model
    print("\n--- Loading Model ---")
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT_DIR, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model = model.to(DEVICE)
    model = PeftModel.from_pretrained(model, CHECKPOINT_DIR)
    model.eval()
    print("Model loaded")

    # Load data
    eval_path = os.path.join(DATA_DIR, "eval.json")
    test_path = os.path.join(DATA_DIR, "test.json")

    with open(eval_path, 'r') as f:
        eval_data = json.load(f)
    with open(test_path, 'r') as f:
        test_data = json.load(f)

    # Evaluate on both splits
    eval_results = evaluate_split(model, tokenizer, eval_data, "eval")
    test_results = evaluate_split(model, tokenizer, test_data, "test")

    # Go/No-Go decision based on test set
    print(f"\n{'='*60}")
    print(f"Go/No-Go Decision (based on test set)")
    print(f"  Thresholds: coarse_acc >= {COARSE_ACC_THRESHOLD}, fine_acc >= {FINE_ACC_THRESHOLD}, parse_rate >= {PARSE_RATE_THRESHOLD}")
    print(f"{'='*60}")
    go = (test_results["coarse_accuracy"] >= COARSE_ACC_THRESHOLD and
          test_results["fine_accuracy"] >= FINE_ACC_THRESHOLD and
          test_results["parse_rate"] >= PARSE_RATE_THRESHOLD)
    if go:
        print(f"GO - Coarse acc {test_results['coarse_accuracy']:.2%} (>={COARSE_ACC_THRESHOLD:.0%}), Fine acc {test_results['fine_accuracy']:.2%} (>={FINE_ACC_THRESHOLD:.0%}), Parse rate {test_results['parse_rate']:.2%} (>={PARSE_RATE_THRESHOLD:.0%})")
    else:
        reasons = []
        if test_results["coarse_accuracy"] < COARSE_ACC_THRESHOLD:
            reasons.append(f"Coarse acc {test_results['coarse_accuracy']:.2%} < {COARSE_ACC_THRESHOLD:.0%}")
        if test_results["fine_accuracy"] < FINE_ACC_THRESHOLD:
            reasons.append(f"Fine acc {test_results['fine_accuracy']:.2%} < {FINE_ACC_THRESHOLD:.0%}")
        if test_results["parse_rate"] < PARSE_RATE_THRESHOLD:
            reasons.append(f"Parse rate {test_results['parse_rate']:.2%} < {PARSE_RATE_THRESHOLD:.0%}")
        print(f"NO-GO - {'; '.join(reasons)}")

    # V1 baseline comparison
    print(f"\n--- V1 Baseline Comparison ---")
    # Try loading from V1 results, fall back to hardcoded with warning
    v1_results_path = os.path.join(PROJECT_DIR, "..", "..", "biz", "model", "registry", "intent-0.5b-v1", "eval_results.json")
    v1_results_path = os.path.abspath(v1_results_path)
    if os.path.exists(v1_results_path):
        with open(v1_results_path, 'r') as f:
            v1_data = json.load(f)
        v1_coarse_acc = v1_data.get("coarse_accuracy", 0.9383)
        v1_fine_acc = v1_data.get("fine_accuracy", 0.8333)
        print(f"  (loaded from {v1_results_path})")
    else:
        v1_coarse_acc = 0.9383
        v1_fine_acc = 0.8333
        print(f"  (hardcoded fallback - V1 results file not found)")

    # V1 tool F1 must be hardcoded since v1 eval didn't compute per-class F1
    v1_tool_f1 = 0.828
    print(f"  V1 coarse acc:  {v1_coarse_acc:.4f} -> V2: {test_results['coarse_accuracy']:.4f} (delta: {test_results['coarse_accuracy']-v1_coarse_acc:+.4f})")
    print(f"  V1 fine acc:    {v1_fine_acc:.4f} -> V2: {test_results['fine_accuracy']:.4f} (delta: {test_results['fine_accuracy']-v1_fine_acc:+.4f})")
    v2_tool_f1 = test_results["coarse_per_class"].get("tool", {}).get("f1", 0)
    print(f"  V1 tool F1:     {v1_tool_f1:.4f} -> V2: {v2_tool_f1:.4f} (delta: {v2_tool_f1-v1_tool_f1:+.4f})")

    # Save combined results
    combined = {
        "eval": {k: v for k, v in eval_results.items() if k not in ("coarse_per_class", "fine_per_class")},
        "test": {k: v for k, v in test_results.items() if k not in ("coarse_per_class", "fine_per_class")},
        "test_coarse_per_class": test_results["coarse_per_class"],
        "test_fine_per_class": test_results["fine_per_class"],
        "eval_coarse_per_class": eval_results["coarse_per_class"],
        "eval_fine_per_class": eval_results["fine_per_class"],
        "go_no_go": "Go" if go else "No-Go",
        "go_no_go_thresholds": {
            "coarse_accuracy": COARSE_ACC_THRESHOLD,
            "fine_accuracy": FINE_ACC_THRESHOLD,
            "parse_rate": PARSE_RATE_THRESHOLD,
        },
        "v1_baseline": {
            "coarse_accuracy": v1_coarse_acc,
            "fine_accuracy": v1_fine_acc,
            "tool_f1": v1_tool_f1,
        },
        "v2_tool_f1": v2_tool_f1,
        "tool_f1_delta": round(v2_tool_f1 - v1_tool_f1, 4),
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_path = os.path.join(RESULTS_DIR, "eval_results.json")
    with open(results_path, 'w') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()
