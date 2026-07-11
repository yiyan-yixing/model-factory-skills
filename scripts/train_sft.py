#!/usr/bin/env python3
"""
SFT Fine-tuning for Qwen2.5-0.5B Chinese Sentiment Classification
Memory-constrained CPU environment.

Key optimizations:
- 4-bit QLoRA with device_map='auto' and max_memory
- Gradient checkpointing
- LoRA rank=8 on q_proj+v_proj only
- SGD optimizer (less memory than AdamW)
- batch_size=1, grad_accum=8
- max_seq_length=64
- Pre-tokenized data
- Aggressive GC
"""

import json
import os
import time
import gc
import numpy as np

import torch
from torch.utils.data import DataLoader, Dataset as TorchDataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training

# ============================================================
# Configuration
# ============================================================
MODEL_PATH = "/workspace/model-factory-skills/models/Qwen2.5-0.5B-base"
DATA_DIR = "/workspace/model-factory-skills/data"
OUTPUT_DIR = "/workspace/model-factory-skills/models/sentiment-0.5b-v1/sft-checkpoint"

LEARNING_RATE = 5e-5
NUM_EPOCHS = 3
BATCH_SIZE = 1
GRAD_ACCUM = 8
LORA_RANK = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
MAX_SEQ_LEN = 64
SEED = 42
LOG_EVERY = 10
EVAL_EVERY = 50

LABEL_MAP = {0: "negative", 1: "positive"}


class SFTDataset(TorchDataset):
    """Pre-tokenized SFT dataset."""

    def __init__(self, data, tokenizer, max_length):
        self.encoded = []
        for item in data:
            text = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n{item['output']}"
            enc = tokenizer(text, truncation=True, max_length=max_length, padding="max_length")
            ids = torch.tensor(enc["input_ids"], dtype=torch.long)
            mask = torch.tensor(enc["attention_mask"], dtype=torch.long)
            labels = ids.clone()
            labels[labels == tokenizer.pad_token_id] = -100
            self.encoded.append({"input_ids": ids, "attention_mask": mask, "labels": labels})

    def __len__(self):
        return len(self.encoded)

    def __getitem__(self, idx):
        return self.encoded[idx]


def main():
    print("=" * 60)
    print("SFT Fine-tuning: Qwen2.5-0.5B (CPU, 4-bit QLoRA)")
    print("=" * 60)
    start_time = time.time()

    # ============================================================
    # Tokenizer
    # ============================================================
    print("\n--- Loading Tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, padding_side='right',
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"Vocab: {len(tokenizer)}")

    # ============================================================
    # Data (load and tokenize BEFORE model to save memory)
    # ============================================================
    print("\n--- Preparing Data ---")
    with open(os.path.join(DATA_DIR, "sft/sft_1k.json"), 'r') as f:
        sft_data = json.load(f)
    print(f"SFT data: {len(sft_data)}")

    # Load train.json and convert
    with open(os.path.join(DATA_DIR, "processed/train.json"), 'r') as f:
        raw_data = json.load(f)

    np.random.seed(SEED)
    converted = []
    for item in raw_data:
        label_str = LABEL_MAP[item['label']]
        conf = round(np.random.uniform(0.85, 0.99), 2)
        converted.append({
            "instruction": "请判断以下文本的情感倾向，以JSON格式输出。",
            "input": item['text'],
            "output": json.dumps({"label": label_str, "confidence": conf}, ensure_ascii=False)
        })

    combined = sft_data + converted
    del sft_data, raw_data, converted

    # Balance
    pos = [d for d in combined if '"positive"' in d.get('output', '')]
    neg = [d for d in combined if '"negative"' in d.get('output', '')]
    print(f"Before balance: pos={len(pos)}, neg={len(neg)}")

    neg_up = [neg[i] for i in np.random.choice(len(neg), size=len(pos), replace=True)]
    balanced = pos + neg_up
    np.random.shuffle(balanced)
    del combined, pos, neg, neg_up

    # Subsample to keep training time manageable
    MAX_SAMPLES = 800
    if len(balanced) > MAX_SAMPLES:
        idx = np.random.choice(len(balanced), size=MAX_SAMPLES, replace=False)
        balanced = [balanced[i] for i in idx]
    print(f"Training on: {len(balanced)} samples")

    # Split 90/10
    split = int(len(balanced) * 0.9)
    train_ds = SFTDataset(balanced[:split], tokenizer, MAX_SEQ_LEN)
    val_ds = SFTDataset(balanced[split:], tokenizer, MAX_SEQ_LEN)
    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}")
    del balanced

    gc.collect()

    # ============================================================
    # Model (4-bit QLoRA with memory limits)
    # ============================================================
    print("\n--- Loading Model (4-bit QLoRA) ---")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        trust_remote_code=True,
        device_map="auto",
        max_memory={"cpu": "2GiB"},
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    # LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_RANK, lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "v_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    gc.collect()

    # ============================================================
    # Training
    # ============================================================
    print("\n--- Training ---")
    model.train()

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    # Use SGD with momentum (much less memory than AdamW)
    optimizer = torch.optim.SGD(trainable_params, lr=LEARNING_RATE, momentum=0.9, weight_decay=0.01)

    total_steps = (len(train_ds) // (BATCH_SIZE * GRAD_ACCUM)) * NUM_EPOCHS
    warmup_steps = int(total_steps * 0.1)
    # Simple linear warmup + constant
    print(f"Total steps: {total_steps}, Warmup: {warmup_steps}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=1, num_workers=0)

    global_step = 0
    running_loss = 0.0
    log_count = 0
    best_eval_loss = float('inf')
    all_losses = []

    for epoch in range(NUM_EPOCHS):
        print(f"\n=== Epoch {epoch+1}/{NUM_EPOCHS} ===")
        epoch_loss = 0.0
        epoch_batches = 0
        optimizer.zero_grad(set_to_none=True)

        for batch_idx, batch in enumerate(train_loader):
            # Warmup LR
            if global_step < warmup_steps:
                lr_scale = (global_step + 1) / warmup_steps
                for pg in optimizer.param_groups:
                    pg['lr'] = LEARNING_RATE * lr_scale

            input_ids = batch["input_ids"]
            attention_mask = batch["attention_mask"]
            labels = batch["labels"]

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss / GRAD_ACCUM
            loss.backward()

            batch_loss = outputs.loss.item()
            running_loss += batch_loss
            epoch_loss += batch_loss
            log_count += 1
            epoch_batches += 1
            all_losses.append(batch_loss)

            del outputs, input_ids, attention_mask, labels, loss

            if (batch_idx + 1) % GRAD_ACCUM == 0:
                torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

                if global_step % LOG_EVERY == 0:
                    avg = running_loss / log_count
                    lr = optimizer.param_groups[0]['lr']
                    print(f"  Step {global_step}/{total_steps} | Loss: {avg:.4f} | LR: {lr:.2e}")
                    running_loss = 0.0
                    log_count = 0

                if global_step % EVAL_EVERY == 0:
                    # Eval
                    model.eval()
                    eval_loss = 0
                    n = 0
                    with torch.no_grad():
                        for vb in val_loader:
                            vo = model(input_ids=vb["input_ids"], attention_mask=vb["attention_mask"], labels=vb["labels"])
                            eval_loss += vo.loss.item()
                            n += 1
                            del vo
                            if n >= 30:
                                break
                    eval_loss /= max(n, 1)
                    model.train()
                    flag = " (best!)" if eval_loss < best_eval_loss else ""
                    if eval_loss < best_eval_loss:
                        best_eval_loss = eval_loss
                        os.makedirs(OUTPUT_DIR, exist_ok=True)
                        model.save_pretrained(OUTPUT_DIR)
                        tokenizer.save_pretrained(OUTPUT_DIR)
                    print(f"  >> Eval step {global_step}: {eval_loss:.4f}{flag}")

            # GC every 20 batches
            if batch_idx % 20 == 0:
                gc.collect()

        avg_epoch = epoch_loss / max(epoch_batches, 1)
        print(f"Epoch {epoch+1} avg loss: {avg_epoch:.4f}")

    # Final save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Final eval
    model.eval()
    eval_loss = 0
    n = 0
    with torch.no_grad():
        for vb in val_loader:
            vo = model(input_ids=vb["input_ids"], attention_mask=vb["attention_mask"], labels=vb["labels"])
            eval_loss += vo.loss.item()
            n += 1
            del vo
    eval_loss /= max(n, 1)

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed/60:.1f} min | Final eval loss: {eval_loss:.4f} | Best: {best_eval_loss:.4f}")

    # Save metrics
    metrics = {
        "final_eval_loss": eval_loss,
        "best_eval_loss": best_eval_loss,
        "final_train_loss": all_losses[-1] if all_losses else 0,
        "avg_train_loss_last100": np.mean(all_losses[-100:]) if len(all_losses) >= 100 else np.mean(all_losses) if all_losses else 0,
        "total_elapsed_seconds": elapsed,
        "num_epochs": NUM_EPOCHS,
        "learning_rate": LEARNING_RATE,
        "lora_rank": LORA_RANK,
        "lora_alpha": LORA_ALPHA,
        "batch_size": BATCH_SIZE,
        "gradient_accumulation_steps": GRAD_ACCUM,
        "max_seq_length": MAX_SEQ_LEN,
        "seed": SEED,
        "device": "cpu",
        "quantization": "4-bit QLoRA (nf4) + gradient checkpointing",
        "model": "Qwen2.5-0.5B",
        "task": "Chinese sentiment classification",
        "optimizer": "SGD (momentum=0.9)",
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "target_modules": ["q_proj", "v_proj"],
        "loss_curve_sample": all_losses[::max(1, len(all_losses)//20)],
    }
    with open(os.path.join(OUTPUT_DIR, "training_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_DIR}")

    return OUTPUT_DIR


if __name__ == "__main__":
    main()
