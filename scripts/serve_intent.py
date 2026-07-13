#!/usr/bin/env python3
"""
Intent Recognition + Query Rewriting API Server.

Usage:
  python3 scripts/serve_intent.py                     # Default (merged model, port 8100)
  python3 scripts/serve_intent.py --port 9000          # Custom port
  python3 scripts/serve_intent.py --device mps         # Use MPS acceleration
  python3 scripts/serve_intent.py --lora               # Load base + LoRA (slower startup)

API Endpoints:
  POST /intent         — Single query intent recognition
  POST /intent/batch   — Batch query intent recognition
  GET  /health         — Health check
"""

import argparse
import json
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import torch
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from transformers import AutoModelForCausalLM, AutoTokenizer

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MERGED = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "merged")
DEFAULT_BASE = os.path.join(PROJECT_DIR, "models", "Qwen2.5-0.5B-base")
DEFAULT_ADAPTER = os.path.join(PROJECT_DIR, "models", "intent-0.5b-v1", "sft-checkpoint")

INSTRUCTION = "分析用户输入的意图，输出意图分类和改写后的查询。"
MAX_NEW_TOKENS = 128
MAX_INPUT_LENGTH = 256

# ============================================================
# Pydantic models
# ============================================================
class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="User input query")

class BatchIntentRequest(BaseModel):
    queries: List[str] = Field(..., min_length=1, max_length=64, description="List of queries")

class IntentResponse(BaseModel):
    query: str
    intent: Optional[str] = None
    sub_intent: Optional[str] = None
    rewritten_query: Optional[str] = None
    raw_output: Optional[str] = None
    parse_success: bool
    latency_ms: float

class BatchIntentResponse(BaseModel):
    results: List[IntentResponse]
    total_latency_ms: float

class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
    uptime_seconds: float


# ============================================================
# Core logic (reused from inference_intent.py)
# ============================================================
def parse_output(text: str) -> Optional[dict]:
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

    # Try to find JSON object with intent key
    json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return result
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if "intent" in result:
                return result
        except json.JSONDecodeError:
            pass

    return None


def predict(model, tokenizer, query: str, device: str) -> dict:
    """Run intent prediction on a single query. Returns (parsed, raw_text, latency_ms)."""
    prompt = (
        f"### Instruction:\n{INSTRUCTION}\n\n"
        f"### Input:\n{query}\n\n"
        f"### Response:\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_LENGTH)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.pad_token_id,
        )
    latency_ms = (time.time() - start) * 1000

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    parsed = parse_output(generated_text)
    return parsed, generated_text, latency_ms


# ============================================================
# Model loader
# ============================================================
class ModelManager:
    """Manages model lifecycle: load, predict, health."""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.start_time = None
        self.model_name = ""

    def load(self, args):
        """Load model based on CLI arguments."""
        self.device = args.device
        self.start_time = time.time()

        # Determine device (prefer MPS on Apple Silicon, fallback to CPU)
        if self.device == "mps":
            if not torch.backends.mps.is_available():
                print("⚠️  MPS not available, falling back to CPU")
                self.device = "cpu"

        # Auto-detect: if merged model exists, use it; otherwise use base + LoRA
        model_path = args.model_path
        use_lora = args.lora

        if not use_lora and os.path.isdir(DEFAULT_MERGED) and model_path == DEFAULT_MERGED:
            # Use merged model (no peft dependency)
            print(f"Loading merged model from {model_path}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model_name = "intent-0.5b-v1 (merged)"
        elif use_lora or not os.path.isdir(DEFAULT_MERGED):
            # Use base + LoRA
            from peft import PeftModel
            print(f"Loading base model from {DEFAULT_BASE}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                DEFAULT_BASE,
                trust_remote_code=True,
                torch_dtype=torch.float16,
            )
            print(f"Loading LoRA adapter from {DEFAULT_ADAPTER}...")
            self.model = PeftModel.from_pretrained(self.model, DEFAULT_ADAPTER)
            self.tokenizer = AutoTokenizer.from_pretrained(DEFAULT_ADAPTER, trust_remote_code=True)
            self.model_name = "intent-0.5b-v1 (base+LoRA)"
        else:
            # Custom model path
            print(f"Loading model from {model_path}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model_name = f"custom ({os.path.basename(model_path)})"

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval()

        # Move to device
        if self.device == "mps":
            self.model = self.model.to("mps")

        print(f"✅ Model loaded on {self.device}")
        print(f"   Model: {self.model_name}")

    def predict_intent(self, query: str):
        """Predict intent for a single query."""
        return predict(self.model, self.tokenizer, query, self.device)


# Global model manager
mgr = ModelManager()


# ============================================================
# FastAPI app with lifespan
# ============================================================
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    args = application.state.args
    print(f"\n🚀 Starting Intent Recognition API")
    print(f"   Device: {args.device}")
    print(f"   Model:  {'base+LoRA' if args.lora else args.model_path}")
    mgr.load(args)
    print(f"   Ready to serve!\n")
    yield
    # Shutdown: nothing special needed
    print("Shutting down...")


app = FastAPI(
    title="Intent Recognition API",
    description="意图识别 + Query 改写服务，基于 Qwen2.5-0.5B 微调模型",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/intent", response_model=IntentResponse)
async def intent_recognition(req: IntentRequest):
    """Classify intent and rewrite a single query."""
    if mgr.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    parsed, raw, latency_ms = mgr.predict_intent(req.query)

    if parsed:
        return IntentResponse(
            query=req.query,
            intent=parsed.get("intent"),
            sub_intent=parsed.get("sub_intent"),
            rewritten_query=parsed.get("rewritten_query"),
            raw_output=raw[:300],
            parse_success=True,
            latency_ms=round(latency_ms, 1),
        )
    else:
        return IntentResponse(
            query=req.query,
            raw_output=raw[:300],
            parse_success=False,
            latency_ms=round(latency_ms, 1),
        )


@app.post("/intent/batch", response_model=BatchIntentResponse)
async def intent_recognition_batch(req: BatchIntentRequest):
    """Classify intent for a batch of queries."""
    if mgr.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    results = []
    for query in req.queries:
        parsed, raw, latency_ms = mgr.predict_intent(query)
        if parsed:
            results.append(IntentResponse(
                query=query,
                intent=parsed.get("intent"),
                sub_intent=parsed.get("sub_intent"),
                rewritten_query=parsed.get("rewritten_query"),
                raw_output=raw[:300],
                parse_success=True,
                latency_ms=round(latency_ms, 1),
            ))
        else:
            results.append(IntentResponse(
                query=query,
                raw_output=raw[:300],
                parse_success=False,
                latency_ms=round(latency_ms, 1),
            ))
    total_ms = (time.time() - start) * 1000

    return BatchIntentResponse(results=results, total_latency_ms=round(total_ms, 1))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - mgr.start_time if mgr.start_time else 0
    return HealthResponse(
        status="ok" if mgr.model is not None else "loading",
        model=mgr.model_name,
        device=mgr.device or "unknown",
        uptime_seconds=round(uptime, 1),
    )


@app.get("/", response_class=HTMLResponse)
async def test_page():
    """Serve the interactive test page."""
    html_path = Path(__file__).parent / "test-page.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Test page not found</h1><p>Place test-page.html in scripts/</p>", status_code=404)


def main():
    parser = argparse.ArgumentParser(description="Intent Recognition API Server")
    parser.add_argument("--port", type=int, default=8100, help="Server port (default: 8100)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--device", default="cpu", choices=["cpu", "mps"], help="Inference device")
    parser.add_argument("--model-path", default=DEFAULT_MERGED, help="Path to model (default: merged model)")
    parser.add_argument("--lora", action="store_true", help="Force base+LoRA mode instead of merged model")
    args = parser.parse_args()

    # Store args for lifespan
    app.state.args = args

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
