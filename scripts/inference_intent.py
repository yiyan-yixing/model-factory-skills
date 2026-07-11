#!/usr/bin/env python3
"""
Interactive inference for intent classification + query rewriting.

Usage:
  python3 scripts/inference_intent.py                    # Interactive mode
  python3 scripts/inference_intent.py "帮我画个猫"         # Single query
  python3 scripts/inference_intent.py --batch             # Run batch examples
"""

import json
import os
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
CHECKPOINT_DIR = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "sft-checkpoint")

BATCH_EXAMPLES = [
    "你好",
    "画个好看的",
    "帮我写个快排",
    "什么是量子计算",
    "1+1等于几",
    "设个闹钟明天7点",
    "帮我P一下这张图",
    "代码跑不通怎么办",
    "解方程x²-5x+6=0",
    "翻译一下这段话",
    "今天心情不好",
    "做个短视频",
    "无聊想聊天",
    "怎么学英语",
    "帮我整理一下文件",
    "算一下平均数",
]


def parse_output(text):
    """Parse model output to extract intent JSON."""
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

    # Try to find partial JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if "intent" in result:
                return result
        except json.JSONDecodeError:
            pass

    return None


def load_model():
    """Load model and tokenizer."""
    print("Loading model...")
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
    print("Model loaded!")
    return model, tokenizer


def predict(model, tokenizer, query):
    """Predict intent and rewrite for a single query."""
    prompt = (
        f"### Instruction:\n分析用户输入的意图，输出意图分类和改写后的查询。\n\n"
        f"### Input:\n{query}\n\n"
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

    parsed = parse_output(generated_text)
    return parsed, generated_text


def format_result(query, parsed):
    """Format result for display."""
    if parsed:
        return (
            f"  📥 输入: {query}\n"
            f"  🏷️  意图: {parsed.get('intent', '?')} / {parsed.get('sub_intent', '?')}\n"
            f"  ✏️  改写: {parsed.get('rewritten_query', '?')}"
        )
    else:
        return f"  📥 输入: {query}\n  ❌ 解析失败"


def main():
    model, tokenizer = load_model()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--batch":
            # Batch mode
            print("\n" + "=" * 60)
            print("Batch Inference Results")
            print("=" * 60)
            results = []
            for query in BATCH_EXAMPLES:
                parsed, raw = predict(model, tokenizer, query)
                print(format_result(query, parsed))
                print()
                results.append({"input": query, "parsed": parsed, "raw": raw[:200]})

            # Save examples
            examples_path = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "examples.json")
            os.makedirs(os.path.dirname(examples_path), exist_ok=True)
            with open(examples_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Examples saved to {examples_path}")
        else:
            # Single query mode
            query = arg
            parsed, raw = predict(model, tokenizer, query)
            print(format_result(query, parsed))
    else:
        # Interactive mode
        print("\n" + "=" * 60)
        print("Interactive Intent Recognition + Query Rewriting")
        print("Type your query (or 'quit' to exit)")
        print("=" * 60)
        while True:
            try:
                query = input("\n🔍 Query: ").strip()
                if query.lower() in ('quit', 'exit', 'q'):
                    break
                if not query:
                    continue
                parsed, raw = predict(model, tokenizer, query)
                print(format_result(query, parsed))
            except (EOFError, KeyboardInterrupt):
                break

        print("\nBye!")


if __name__ == "__main__":
    main()
