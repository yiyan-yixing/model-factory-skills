# 一人公司造模型：从组织架构到模型部署的完整实践

> 以 model-factory-skills 为例，展示「一人公司」如何用 Claude Code Agent 体系 + LoRA 微调，在 Mac 上 1 天内跑通意图识别模型的全链路。

---

## 一、为什么需要一套「模型工厂」Agent 体系

大模型时代，一个人也能做模型公司——前提是有一套可复用的协作框架。传统模型公司需要产品经理、数据工程师、训练工程师、评测工程师、部署工程师……一人公司没有这么多人，但可以用 **Agent 角色化** 解决：同一个人在不同阶段切换不同思维域，由 Agent 体系保证流程不丢步。

model-factory-skills 就是这套框架：**15 个角色、16 个技能、1 条闭环 DAG**，覆盖从产品定义到商业闭环的全链路。

---

## 二、组织架构：两环一核

一人公司不需要部门，需要**思维域**。我们的架构不是按部门划分，而是按价值流阶段组织：

```
CEO
 │
 ├── 🎨 创造环（Make It）
 │    ├── 阶段 1 · 产品定义：@po @ai-pm
 │    │     产出：PRD + 评测目标 + Prompt/Agent 设计
 │    │
 │    └── 阶段 2 · 模型研发：@data-strategy @data-engineer @ml-trainer @ml-alignment
 │          产出：达标模型（可评测状态）
 │
 ├── 🚦 闸门（Gate It）：@evaluation（独立）
 │     产出：Go/No-Go 判定 + 评测报告
 │     权力：发布否决权，不归创造环管辖
 │
 ├── 🚀 推广环（Ship It）
 │    ├── 阶段 3 · 工程交付：@ml-serving @backend @infra
 │    │     产出：可调用 API + 部署 + 监控
 │    │
 │    └── 阶段 4 · 商业闭环：@growth @devrel @ops
 │          产出：调用量 + 用户反馈 + 商业转化
 │
 └── 🔧 横向支撑：@mlops
       职责：跨阶段流水线自动化、实验追踪、模型注册
```

### 为什么是「两环一核」而不是「三层」

最初我考虑过三层架构：CEO → 虚拟部门 → 基础部门。但 @ceo 评估后指出：

| 变更 | 三层架构 | 两环一核 | 理由 |
|------|---------|---------|------|
| 组织逻辑 | 按部门划分 | 按价值流阶段 | 一人公司不需要部门，需要思维域 |
| 评测归属 | 在某个部门 | **独立闸门** | 评测必须独立于被评测者（OpenAI 教训：评测团队被生产压力侵蚀） |
| MLOps | 在工程部 | **横向支撑** | MLOps 跨全链路，不属于任何阶段 |
| 跨部门交接 | 4 次 | **0 次** | 阶段流转是自然工作流，不是跨部门 |
| 思维切换 | 4 种部门身份 | **2 种思维模式** | 大幅降低认知负荷 |

**核心洞察**：评测独立不能靠文化，必须靠结构。@evaluation 有发布否决权，这是从 Anthropic 的实践和 OpenAI 的教训中学到的核心原则。

---

## 三、实战：1 天跑通意图识别模型

架构设计好了，能跑通吗？下面用一个真实案例验证——在 Mac M4 Max 48GB 上，1 天内完成意图识别模型的训练和部署。

### 3.1 需求定义（🎨 创造环 · 阶段 1）

**场景**：AI 助手需要对用户输入做意图识别 + query 改写，以便精准路由到不同的下游执行器。

两个核心需求：
1. **识别准确性** — 兼顾主流分类体系
2. **query 改写** — 意图识别后对 query 改写，提升后续执行效果

**意图分类体系**：采用两级分类（coarse → fine），6 个粗粒度 + 25 个细粒度：

| 粗粒度意图 | 说明 | 细粒度子意图 |
|-----------|------|------------|
| `chat` | 闲聊/问候/情感 | emotion, greeting, persona, small_talk |
| `search` | 知识查询/事实检索 | comparison, factual, how_to, opinion |
| `generation` | 图片/视频/音频生成 | audio_gen, image_gen, text_gen, video_gen |
| `code` | 编程/调试/技术 | debug, explain, refactor, write |
| `math` | 计算/推理/公式 | computation, equation, proof, statistics |
| `tool` | 工具/API 操作 | calendar, email, file_op, system, translate |

**模型输出格式**（意图 + 改写一体化）：

```
输入: "画个好看的"
输出: {
  "intent": "generation",
  "sub_intent": "image_gen",
  "rewritten_query": "请生成一张好看的图片，风格简约，色彩明亮"
}
```

### 3.2 数据与训练（🎨 创造环 · 阶段 2）

#### 模型选择：Qwen2.5-0.5B + LoRA

| 参数 | 选择 | 理由 |
|------|------|------|
| 基座模型 | Qwen2.5-0.5B-base | 0.5B 参数量，48GB 内存轻松容纳 |
| 微调方法 | LoRA SFT | 只训练 2.1M 参数（0.44%），效率高 |
| LoRA rank | 16, alpha=32 | 注意力层全覆盖（q/k/v/o_proj） |
| 训练精度 | fp32 (CPU) | Apple Silicon 上 BitsAndBytes 不可用，MPS + PEFT 有兼容问题 |
| 序列长度 | 256 | 意图分类 + 改写不需要长上下文 |

#### 数据工程

数据集通过脚本 `generate_intent_data.py` 生成，覆盖多种表达方式：

- **直接表达**：「帮我写个快排」「什么是量子计算」
- **间接表达**：「代码跑不通怎么办」「今天心情不好」
- **模糊表达**：「画个好看的」「帮我P一下这张图」
- **含前缀变体**：「帮我…」「能不能…」「我想…」
- **含后缀变体**：「…吧」「…呢」「…啊」

经过 3 轮数据增补（初始 756 → 增补 tool/search → 增补 sub-intent 歧义），最终数据集：

| 集合 | 样本数 |
|------|--------|
| 训练集 | 881 |
| 验证集 | 162 |
| 测试集 | 162 |
| Schema | 6 coarse / 25 fine |

#### 训练过程

```
5 epochs, LR=2e-5, batch=4, grad_accum=4
设备: CPU (Mac M4 Max 48GB)
时长: 69.4 分钟

Epoch 1: loss 2.54 → 1.14
Epoch 2: loss 1.14 → 0.82
Epoch 3: loss 0.82 → 0.72
Epoch 4: loss 0.72 → 0.66
Epoch 5: loss 0.66 (best eval loss: 0.638)
```

**关键经验**：Apple Silicon 训练踩过的坑：

| 坑 | 症状 | 解法 |
|----|------|------|
| BitsAndBytes 不可用 | `ImportError` on Apple Silicon | 放弃 4-bit 量化，用 fp32 + LoRA |
| MPS + PEFT 冲突 | `Placeholder storage has not been allocated on MPS device!` | 训练用 CPU，推理用 MPS/CPU 都行 |
| mlx-lm 版本不兼容 | `AttributeError: 'str' object has no attribute '__module__'` | 放弃 mlx-lm，用纯 transformers+PEFT |
| 数据量不足 | 首轮 coarse 78.4% | 针对性增补 tool/search/歧义样本 |

### 3.3 评测闸门（🚦 闸门）

评测脚本 `eval_intent.py` 自动计算粗/细粒度准确率和每类 F1，并给出 Go/No-Go 判定：

**Go/No-Go 标准**：
- 粗粒度准确率 ≥ 90%
- 细粒度准确率 ≥ 85%
- JSON 解析率 ≥ 90%

**当前结果**：

| 指标 | 值 | 阈值 | 状态 |
|------|-----|------|------|
| 粗粒度准确率 | 89.5% | ≥ 90% | ⚠️ 差 0.5% |
| 细粒度准确率 | 82.1% | ≥ 85% | ⚠️ 差 2.9% |
| JSON 解析率 | 99.4% | ≥ 90% | ✅ 通过 |
| **整体判定** | **No-Go** | | 需要继续迭代 |

**@evaluation 的对抗视角**：尽管结果接近目标，但评测的角色不是"证明模型没问题"，而是"找出模型的问题"。当前 No-Go 是正确的——模型在 `tool/translate`（被误分类为 `code/translate`）和 `tool/file_op`（模型输出了 schema 外的 `file_manager`）上存在系统性错误，需要针对性补数据再训。

**推理效果示例**（14/15 分类正确）：

```
📥 你好              → chat/greeting        | 你好，我想和你打个招呼
📥 画个好看的         → generation/image_gen  | 请生成一张好看的图片，风格简约，色彩明亮
📥 帮我写个快排       → code/write           | 请用Python实现快速排序算法
📥 什么是量子计算     → search/factual       | 请解释量子计算的基本原理和应用
📥 1+1等于几         → math/computation     | 请计算1+1的值
📥 设个闹钟明天7点    → tool/calendar        | 请设置明天7点的闹钟
📥 代码跑不通怎么办   → code/debug           | 请检查代码运行状态，分析错误原因
📥 解方程x²-5x+6=0  → math/equation        | 请解一元二次方程x²-5x+6=0
📥 做个短视频         → generation/video_gen | 请生成短视频，时长10分钟，风格轻松幽默
```

### 3.4 部署上线（🚀 推广环 · 阶段 3）

即使评测是 No-Go，部署链路也要提前跑通——这是「两环一核」的设计哲学：创造环和推广环可以并行准备。

#### Step 1：合并 LoRA → 独立模型

LoRA 适配器（8.3MB）需要基座模型（942MB）才能运行。通过 `merge_lora.py` 将两者合并：

```bash
python3 scripts/merge_lora.py
# 输入: base (942MB) + adapter (8.3MB)
# 输出: merged/ (942MB, 独立模型，无需 peft)
# 耗时: 1.4 秒
```

合并后模型可直接用 `AutoModelForCausalLM.from_pretrained()` 加载，**去掉了 peft 运行时依赖**，加载更快、部署更简单。

#### Step 2：FastAPI 推理服务

`serve_intent.py` 提供三个 API 端点：

```bash
# 启动服务
python3 scripts/serve_intent.py --port 8100

# 健康检查
curl http://localhost:8100/health
# → {"status": "ok", "model": "intent-0.5b-v1 (merged)", "device": "cpu", "uptime_seconds": 1.3}

# 单条推理
curl -X POST http://localhost:8100/intent \
  -H "Content-Type: application/json" \
  -d '{"query": "帮我画个猫"}'
# → {"intent": "generation", "sub_intent": "image_gen",
#    "rewritten_query": "请生成一张猫的卡通画，画风可爱",
#    "parse_success": true, "latency_ms": 1235.3}

# 批量推理
curl -X POST http://localhost:8100/intent/batch \
  -H "Content-Type: application/json" \
  -d '{"queries": ["你好", "画个好看的", "帮我写个快排"]}'
# → {"results": [...], "total_latency_ms": 5208}
```

**API 设计原则**：
- 模型常驻内存，避免冷启动（首次加载 ~3s，后续推理 ~1s/query on CPU）
- 返回 `latency_ms` 字段，便于监控和 SLA 管理
- 支持 `--device mps` 切换到 Apple Silicon GPU 推理（延迟可降至 ~50-200ms）
- Pydantic 做请求/响应校验，FastAPI 自动生成 OpenAPI 文档

#### Step 3：Docker 容器化

```bash
# 构建（只打包 merged 模型 + serving 代码，不含训练脚本）
docker build -f Dockerfile.serve -t intent-api:latest .

# 运行
docker run -p 8100:8100 intent-api:latest

# 镜像内置健康检查
HEALTHCHECK --interval=30s CMD curl http://localhost:8100/health
```

预计镜像大小 ~1.5GB（python:3.11-slim + torch CPU + 模型权重）。

---

## 四、流程全景：DAG 闭环

把上面的实践映射回两环一核的 DAG，整条链路是这样的：

```
@ceo 定方向（意图识别 + query 改写）
  └── @po 出 PRD（6 类粗意图 + 25 类细意图 + 改写规则）
        ├── @data-strategy 定数据标准（schema.json + 样本分布）
        │     └── @data-engineer 生成/清洗数据（881 train + 162 eval + 162 test）
        │           └── @ml-trainer 训练（Qwen2.5-0.5B + LoRA, 69 min on CPU）
        │                 └── @evaluation 评测 → No-Go（coarse 89.5% < 90%）
        │                       ├── No-Go 回流 → 补数据再训（已做 3 轮）
        │                       └── 推广环并行准备 ↓
        │
        └── @ml-serving 合并 LoRA → 独立模型
              └── @backend 封 FastAPI（/intent, /intent/batch, /health）
                    └── @infra Docker 容器化
```

**关键观察**：

1. **评测闸门阻断了上线**——这是正确的行为。模型在 `tool/translate` 和 `tool/file_op` 上有系统性错误，不应该带着已知缺陷上线。
2. **推广环提前跑通了部署链路**——即使模型还没 Go，部署基础设施已就绪。下次模型通过评测，可以立即上线。
3. **3 轮 No-Go 都有明确的缺陷分析**——评测不只是打分，而是指出"哪里错了、怎么修"。第 1 轮 tool 数据不足，第 2 轮 sub-intent 歧义，第 3 轮 tool F1 仍低——每次都有针对性解法。

---

## 五、最佳实践总结

### 5.1 架构设计

| 实践 | 说明 |
|------|------|
| **按价值流分阶段，不按部门划分** | 一人公司的瓶颈是认知切换，不是组织协调 |
| **评测独立为闸门** | 结构独立 > 文化独立，否则生产压力必然侵蚀评测 |
| **MLOps 横向支撑** | 不属于任何阶段，为全链路提供自动化 |
| **最多 2 轮回退** | 超过 2 轮上报用户/CEO，避免无限循环 |
| **不提前建能力中心** | 流水线没跑通就建中台是过度设计（阿里教训） |

### 5.2 模型训练

| 实践 | 说明 |
|------|------|
| **0.5B 模型够用就别上大模型** | 意图分类是窄任务，0.5B + LoRA 足够 |
| **先跑通再优化** | CPU fp32 训练虽然慢（69 min），但可靠；MPS/BitsAndBytes 的坑踩不完 |
| **数据质量 > 数据量** | 3 轮针对性增补（tool 歧义、sub-intent 混淆）比盲目堆量有效 |
| **双任务一体化** | 意图分类 + query 改写在同一个模型里完成，避免级联错误 |
| **先出数据再训模型** | `schema.json` 先定义清楚分类体系，数据生成才有锚点 |

### 5.3 评测与部署

| 实践 | 说明 |
|------|------|
| **Go/No-Go 门控** | 评测不过就是 No-Go，不要"先上线再观察" |
| **评测要对抗视角** | 找问题 > 证明没问题；每类 F1 比总体准确率更有诊断价值 |
| **合并 LoRA 再部署** | 去掉 peft 运行时依赖，模型加载更快 |
| **部署链路提前跑通** | 推广环和创造环并行，不等评测 Go 才开始做部署 |
| **API 返回延迟指标** | `latency_ms` 字段为后续 SLA 和监控打基础 |

### 5.4 Apple Silicon 特别注意

| 坑 | 解法 |
|----|------|
| BitsAndBytes 不支持 Apple Silicon | 用 fp32 + LoRA，48GB 内存足够 |
| MPS + PEFT + gradient_checkpointing 不兼容 | 训练用 CPU，推理可以试 MPS |
| mlx-lm 与 transformers 5.x 不兼容 | 放弃 mlx-lm，用纯 transformers |
| device_map="auto" 在 MPS 上行为不稳定 | 显式指定 device，不依赖自动映射 |

---

## 六、文件清单

整条链路产生的文件：

```
model-factory-skills/
├── agents/
│   ├── WORKFLOW.md              # 两环一核架构文档
│   ├── ceo.md                   # 15 个角色 Agent 定义
│   ├── evaluation.md            # 评测闸门（独立）
│   └── ...
├── data/intent/
│   ├── train.json               # 881 条训练数据
│   ├── eval.json                # 162 条验证数据
│   ├── test.json                # 162 条测试数据
│   └── schema.json              # 意图分类体系定义
├── scripts/
│   ├── generate_intent_data.py  # 数据生成脚本
│   ├── train_intent.py          # LoRA SFT 训练脚本
│   ├── eval_intent.py           # 评测 + Go/No-Go
│   ├── inference_intent.py      # CLI 交互式推理
│   ├── merge_lora.py            # LoRA 合并 → 独立模型
│   └── serve_intent.py          # FastAPI 推理服务
├── models/intent-0.5b-v1/
│   ├── sft-checkpoint/          # LoRA 适配器 (8.3MB)
│   │   ├── adapter_config.json
│   │   ├── adapter_model.safetensors
│   │   └── training_metrics.json
│   ├── merged/                  # 合并后独立模型 (942MB)
│   │   ├── model.safetensors
│   │   └── ...
│   ├── eval_results.json        # 评测结果
│   └── examples.json            # 推理示例
├── Dockerfile.serve             # Docker 部署文件
└── install.sh                   # 一键安装到目标项目
```

---

## 七、下一步

1. **补数据再训** — 针对 tool/translate 和 tool/file_op 的系统性错误，增补 50-100 条样本
2. **通过评测闸门** — 目标 coarse ≥ 92%, fine ≥ 87%（留 buffer）
3. **MPS 推理优化** — 推理阶段用 MPS 加速，目标延迟 < 200ms
4. **集成到 AI 助手** — 意图识别作为路由层，上游接收用户 query，下游分发到各执行器
5. **线上 AB 测试** — @evaluation 设计 AB 实验，验证改写后的 query 是否真的提升了下游执行效果

---

*本文基于 model-factory-skills 的真实开发过程撰写，所有数据和代码均可在仓库中复现。*
