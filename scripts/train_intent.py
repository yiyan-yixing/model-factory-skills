#!/usr/bin/env python3
"""
SFT Fine-tuning for Qwen2.5-0.5B Intent Classification + Query Rewriting
CPU training on Mac 48GB (0.5B model fits easily in memory).

Key design:
- fp16 model on CPU (48GB RAM is plenty for 0.5B + LoRA)
- LoRA rank=16 on q_proj+v_proj+k_proj+o_proj
- AdamW optimizer
- Gradient checkpointing for memory savings
- Output: JSON with intent + sub_intent + rewritten_query
"""

import json
import os
import time
import gc
import numpy as np

import torch
from torch.utils.data import DataLoader, Dataset as TorchDataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
DATA_DIR = os.path.join(PROJECT_DIR, "data", "intent")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "sft-checkpoint")

LEARNING_RATE = 2e-5
NUM_EPOCHS = 5
BATCH_SIZE = 4
GRAD_ACCUM = 4
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
MAX_SEQ_LEN = 256
SEED = 42
LOG_EVERY = 10
EVAL_EVERY = 30
WARMUP_RATIO = 0.1


class IntentSFTDataset(TorchDataset):
    """Pre-tokenized SFT dataset for intent classification + query rewriting."""

    def __init__(self, data, tokenizer, max_length):
        self.encoded = []
        for item in data:
            text = (
                f"### Instruction:\n{item['instruction']}\n\n"
                f"### Input:\n{item['input']}\n\n"
                f"### Response:\n{item['output']}"
            )
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
    print("SFT Fine-tuning: Qwen2.5-0.5B Intent + Query Rewrite")
    print("Training on CPU (Mac 48GB, 0.5B model fits easily)")
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
    # Data
    # ============================================================
    print("\n--- Preparing Data ---")
    np.random.seed(SEED)

    train_path = os.path.join(DATA_DIR, "train.json")
    eval_path = os.path.join(DATA_DIR, "eval.json")

    with open(train_path, 'r') as f:
        train_data = json.load(f)
    with open(eval_path, 'r') as f:
        eval_data = json.load(f)

    print(f"Train: {len(train_data)}, Eval: {len(eval_data)}")

    train_ds = IntentSFTDataset(train_data, tokenizer, MAX_SEQ_LEN)
    val_ds = IntentSFTDataset(eval_data, tokenizer, MAX_SEQ_LEN)
    del train_data, eval_data
    gc.collect()

    # ============================================================
    # Model (fp16 + LoRA on CPU)
    # ============================================================
    print("\n--- Loading Model (fp16 + LoRA on CPU) ---")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        torch_dtype=torch.float32,  # CPU training needs float32
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    # LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    gc.collect()

    # ============================================================
    # Optimizer + Scheduler
    # ============================================================
    print("\n--- Setting up Training ---")
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=LEARNING_RATE, weight_decay=0.01)

    total_steps = (len(train_ds) // (BATCH_SIZE * GRAD_ACCUM)) * NUM_EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)
    print(f"Total steps: {total_steps}, Warmup: {warmup_steps}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=1, num_workers=0)

    # ============================================================
    # Training Loop
    # ============================================================
    print("\n--- Training ---")
    model.train()

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
                    elapsed = time.time() - start_time
                    print(f"  Step {global_step}/{total_steps} | Loss: {avg:.4f} | LR: {lr:.2e} | Time: {elapsed:.0f}s")
                    running_loss = 0.0
                    log_count = 0

                if global_step % EVAL_EVERY == 0:
                    model.eval()
                    eval_loss = 0
                    n = 0
                    with torch.no_grad():
                        for vb in val_loader:
                            vo = model(
                                input_ids=vb["input_ids"],
                                attention_mask=vb["attention_mask"],
                                labels=vb["labels"]
                            )
                            eval_loss += vo.loss.item()
                            n += 1
                            del vo
                            if n >= 50:
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
            vo = model(
                input_ids=vb["input_ids"],
                attention_mask=vb["attention_mask"],
                labels=vb["labels"]
            )
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
        "quantization": "none (fp32)",
        "model": "Qwen2.5-0.5B",
        "task": "Intent classification + query rewriting",
        "optimizer": "AdamW",
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
        "loss_curve_sample": all_losses[::max(1, len(all_losses) // 20)],
    }
    metrics_path = os.path.join(OUTPUT_DIR, "training_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_DIR}")
    print(f"Metrics saved to {metrics_path}")

    return OUTPUT_DIR


if __name__ == "__main__":
    main()
