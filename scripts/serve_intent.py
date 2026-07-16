#!/usr/bin/env python3
"""
意图识别 + Query 改写 API 服务

自包含部署版本 — 所有路径基于脚本所在目录解析。
放到 /home/work/baidu/new-yiyan/intent/ 下即可运行，无需额外配置。

目录结构:
  intent/
  ├── serve_intent.py              ← 本文件
  ├── test-page.html               ← 测试页面
  ├── start.sh                     ← 启动脚本
  ├── requirements-serve.txt       ← Python 依赖
  ├── models/intent-0.5b-v1/merged/  ← 合并后模型
  └── data/intent/schema.json        ← 意图分类体系

Usage:
  bash start.sh                                  # 默认启动
  python3 serve_intent.py --port 9000             # 自定义端口
  python3 serve_intent.py --device cuda           # GPU 推理

API:
  POST /intent         单条意图识别
  POST /intent/batch   批量意图识别
  GET  /health         健康检查
  GET  /               测试页面
  GET  /schema         意图分类体系
"""

import argparse
import json
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import torch
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from transformers import AutoModelForCausalLM, AutoTokenizer

# ============================================================
# Configuration — 所有路径基于脚本所在目录
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MERGED = str(BASE_DIR / "models" / "intent-0.5b-v1" / "merged")
DEFAULT_BASE = str(BASE_DIR / "models" / "Qwen2.5-0.5B-base")
DEFAULT_ADAPTER = str(BASE_DIR / "models" / "intent-0.5b-v1" / "sft-checkpoint")
SCHEMA_PATH = BASE_DIR / "data" / "intent" / "schema.json"
EXAMPLES_PATH = BASE_DIR / "models" / "intent-0.5b-v1" / "examples.json"
EVAL_PATH = BASE_DIR / "models" / "intent-0.5b-v1" / "eval_results.json"

INSTRUCTION = "分析用户输入的意图，输出意图分类和改写后的查询。"
MAX_NEW_TOKENS = 128
MAX_INPUT_LENGTH = 256


# ============================================================
# Pydantic models
# ============================================================
class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512, description="用户输入")

class BatchIntentRequest(BaseModel):
    queries: List[str] = Field(..., min_length=1, max_length=64, description="用户输入列表")

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

class SchemaResponse(BaseModel):
    schema: Dict
    version: str


# ============================================================
# Core logic
# ============================================================
def parse_output(text: str) -> Optional[dict]:
    """解析模型输出，提取意图 JSON"""
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
    """单条推理"""
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
# Model Manager
# ============================================================
class ModelManager:
    """管理模型生命周期"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.start_time = None
        self.model_name = ""

    def load(self, args):
        self.device = args.device
        self.start_time = time.time()

        if self.device == "cuda":
            if not torch.cuda.is_available():
                print("⚠️  CUDA 不可用，回退到 CPU")
                self.device = "cpu"
        elif self.device == "mps":
            if not torch.backends.mps.is_available():
                print("⚠️  MPS 不可用，回退到 CPU")
                self.device = "cpu"

        model_path = args.model_path
        use_lora = args.lora

        if not use_lora and os.path.isdir(DEFAULT_MERGED) and model_path == DEFAULT_MERGED:
            print(f"📦 加载合并模型: {model_path}")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path, trust_remote_code=True, torch_dtype=torch.float16,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model_name = "intent-0.5b-v1 (merged)"
        elif use_lora or not os.path.isdir(DEFAULT_MERGED):
            from peft import PeftModel
            print(f"📦 加载基座模型: {DEFAULT_BASE}")
            self.model = AutoModelForCausalLM.from_pretrained(
                DEFAULT_BASE, trust_remote_code=True, torch_dtype=torch.float16,
            )
            print(f"📦 加载 LoRA 适配器: {DEFAULT_ADAPTER}")
            self.model = PeftModel.from_pretrained(self.model, DEFAULT_ADAPTER)
            self.tokenizer = AutoTokenizer.from_pretrained(DEFAULT_ADAPTER, trust_remote_code=True)
            self.model_name = "intent-0.5b-v1 (base+LoRA)"
        else:
            print(f"📦 加载自定义模型: {model_path}")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path, trust_remote_code=True, torch_dtype=torch.float16,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model_name = f"custom ({os.path.basename(model_path)})"

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval()

        if self.device == "cuda":
            self.model = self.model.to("cuda")
        elif self.device == "mps":
            self.model = self.model.to("mps")

        print(f"✅ 模型加载完成: {self.model_name} on {self.device}")

    def predict_intent(self, query: str):
        return predict(self.model, self.tokenizer, query, self.device)


mgr = ModelManager()


# ============================================================
# FastAPI App
# ============================================================
@asynccontextmanager
async def lifespan(application: FastAPI):
    args = application.state.args
    print(f"\n🚀 启动意图识别服务")
    print(f"   设备: {args.device}")
    print(f"   模型: {'base+LoRA' if args.lora else args.model_path}")
    print(f"   目录: {BASE_DIR}")
    mgr.load(args)
    print(f"   服务地址: http://{args.host}:{args.port}")
    print(f"   测试页面: http://{args.host}:{args.port}/")
    print(f"   API 文档: http://{args.host}:{args.port}/docs\n")
    yield
    print("服务关闭...")


app = FastAPI(
    title="意图识别 API",
    description="意图识别 + Query 改写服务，基于 Qwen2.5-0.5B 微调模型。"
                "支持 6 大意图分类 (chat/search/generation/code/math/tool) + 25 子意图。",
    version="1.0.0",
    lifespan=lifespan,
)


# ────────────────────────────────────────────────────────────
# API: 意图识别
# ────────────────────────────────────────────────────────────

@app.post("/intent", response_model=IntentResponse, summary="单条意图识别")
async def intent_recognition(req: IntentRequest):
    """
    对单条用户输入进行意图识别和 Query 改写。

    返回：粗意图 (intent)、细意图 (sub_intent)、改写查询 (rewritten_query)
    """
    if mgr.model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

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


@app.post("/intent/batch", response_model=BatchIntentResponse, summary="批量意图识别")
async def intent_recognition_batch(req: BatchIntentRequest):
    """对多条用户输入批量进行意图识别。"""
    if mgr.model is None:
        raise HTTPException(status_code=503, detail="模型未加载")

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


# ────────────────────────────────────────────────────────────
# API: 服务信息 & 集成支持
# ────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """服务健康检查，供负载均衡 / K8s 探针使用。"""
    uptime = time.time() - mgr.start_time if mgr.start_time else 0
    return HealthResponse(
        status="ok" if mgr.model is not None else "loading",
        model=mgr.model_name,
        device=mgr.device or "unknown",
        uptime_seconds=round(uptime, 1),
    )


@app.get("/schema", summary="意图分类体系")
async def get_schema():
    """
    返回意图分类体系的完整定义，供其他服务了解可用的意图类别。

    6 大粗意图 + 25 个细粒度子意图。
    """
    if SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        return {"schema": schema, "version": "1.0.0"}
    return {"schema": {}, "version": "1.0.0", "note": "schema.json not found"}


@app.get("/examples", summary="推理示例")
async def get_examples():
    """返回批量推理示例，供其他服务参考输入输出格式。"""
    if EXAMPLES_PATH.exists():
        examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
        return {"examples": examples, "count": len(examples)}
    return {"examples": [], "count": 0}


@app.get("/eval", summary="模型评估指标")
async def get_eval():
    """返回模型评估指标，供其他服务判断模型质量。"""
    if EVAL_PATH.exists():
        return json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    return {"note": "eval_results.json not found"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def test_page():
    """交互式测试页面。"""
    html_path = BASE_DIR / "test-page.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse(
        "<h1>测试页面未找到</h1><p>请将 test-page.html 放在 serve_intent.py 同目录</p>",
        status_code=404,
    )


# ────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="意图识别 API 服务")
    parser.add_argument("--port", type=int, default=8100, help="服务端口 (默认: 8100)")
    parser.add_argument("--host", default="0.0.0.0", help="服务地址 (默认: 0.0.0.0)")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "mps"], help="推理设备")
    parser.add_argument("--model-path", default=DEFAULT_MERGED, help="模型路径 (默认: merged 模型)")
    parser.add_argument("--lora", action="store_true", help="使用 base+LoRA 模式")
    args = parser.parse_args()

    app.state.args = args

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
