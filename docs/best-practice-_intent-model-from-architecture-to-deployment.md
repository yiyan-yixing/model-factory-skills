# 一人公司造模型：从组织架构到模型部署的完整实践

> 以 model-factory-skills 为例，展示「一人公司」如何用 Claude Code Agent 体系 + LoRA 微调，在 Mac 上 1 天内跑通意图识别模型的全链路。
> 覆盖：架构设计 → 需求定义 → 数据工程 → 训练算法 → 评测闸门 → 推理部署 → 应用集成，每一步都与「两环一核」组织架构对齐。

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

### 架构如何映射到实战

本文后续每一节都会标注对应的架构阶段。一人公司做模型的每一步，都不是"想做什么做什么"，而是有明确的角色归属和交接标准：

```
需求定义 → @po (创造环·阶段1)
数据工程 → @data-strategy + @data-engineer (创造环·阶段2)
训练算法 → @ml-trainer + @ml-alignment (创造环·阶段2)
评测闸门 → @evaluation (闸门·独立)
推理部署 → @ml-serving + @backend + @infra (推广环·阶段3)
应用集成 → @growth + @devrel (推广环·阶段4)
```

---

## 三、需求定义（🎨 创造环 · 阶段 1 · @po + @ai-pm）

### 3.1 问题定义

**场景**：AI 助手需要对用户输入做意图识别 + query 改写，以便精准路由到不同的下游执行器。

两个核心需求：
1. **识别准确性** — 兼顾主流分类体系
2. **query 改写** — 意图识别后对 query 改写，提升后续执行效果

### 3.2 意图分类体系设计

**设计原则**：
- **粗粒度用于路由** — 6 类足够覆盖 AI 助手主流场景，类别间互斥性好
- **细粒度用于执行** — 每个粗意图下 4-5 个子意图，对应不同的下游处理逻辑
- **改写用于增强** — 模糊输入补充隐含信息，保留原始意图不变

**两级分类体系**（6 coarse + 25 fine）：

| 粗粒度意图 | 说明 | 细粒度子意图 |
|-----------|------|------------|
| `chat` | 闲聊/问候/情感 | emotion, greeting, persona, small_talk |
| `search` | 知识查询/事实检索 | comparison, factual, how_to, opinion |
| `generation` | 图片/视频/音频生成 | audio_gen, image_gen, text_gen, video_gen |
| `code` | 编程/调试/技术 | debug, explain, refactor, write |
| `math` | 计算/推理/公式 | computation, equation, proof, statistics |
| `tool` | 工具/API 操作 | calendar, email, file_op, system, translate |

**为什么是 6 类而不是更多**：意图分类的首要目标是路由，不是穷举。6 类覆盖了 AI 助手 95%+ 的用户输入场景，类别间互斥性高（`code` vs `math` 的边界是"是否需要编程"，`search` vs `chat` 的边界是"是否需要事实性回答"）。更多类别会降低互斥性，增加标注难度和模型错误率。

### 3.3 模型输出格式设计

意图识别 + query 改写一体化，模型输出 JSON：

```json
{
  "intent": "generation",
  "sub_intent": "image_gen",
  "rewritten_query": "请生成一张好看的图片，风格简约，色彩明亮"
}
```

**为什么不拆成两个模型**：
1. 级联错误——意图分类错 → 改写也错；一体化模型可以联合优化
2. 推理开销——一个模型一次前向，比两个模型两次前向快 1 倍
3. 数据效率——改写训练信号可以反哺意图分类的判别能力

**改写规则**：
- 补充模糊表达的隐含信息（"好看的" → 具体描述）
- 明确意图边界（"帮我弄一下那个" → 具体操作）
- 保留原始意图不变（改写是增强不是替换）
- 不编造不存在的信息（不知道用户想要什么风格就不编）

### 3.4 交接物

@po 产出以下内容，通过 `schema.json` 标准化：

```json
{
  "version": "1.0",
  "coarse_intents": ["chat", "search", "generation", "code", "math", "tool"],
  "sub_intents": {
    "chat": ["emotion", "greeting", "persona", "small_talk"],
    "search": ["comparison", "factual", "how_to", "opinion"],
    "generation": ["audio_gen", "image_gen", "text_gen", "video_gen"],
    "code": ["debug", "explain", "refactor", "write"],
    "math": ["computation", "equation", "proof", "statistics"],
    "tool": ["calendar", "email", "file_op", "system", "translate"]
  },
  "output_format": {
    "intent": "coarse intent (string)",
    "sub_intent": "fine-grained intent (string)",
    "rewritten_query": "expanded and clarified query (string)"
  }
}
```

**验收条件**：@data-strategy 确认分类体系可标注、@evaluation 确认评测指标可量化。

---

## 四、数据工程（🎨 创造环 · 阶段 2 · @data-strategy + @data-engineer）

### 4.1 数据设计方法论

数据是一人公司造模型的**第一瓶颈**——没有标注团队，没有数据平台，必须用自动化方式生成高质量数据。

**设计原则**：
1. **Schema 先行** — 先定义分类体系（`schema.json`），数据生成才有锚点
2. **覆盖度优先** — 每个子意图至少 8-10 条基础样本
3. **多样性倍增** — 用前缀/后缀/改写自动扩充样本量
4. **歧义样本单独构造** — 类别边界上的易混淆样本必须手动添加
5. **三轮增补策略** — 初始生成 → 评测发现弱点 → 针对性增补 → 再评测

### 4.2 数据生成实现

使用 `scripts/generate_intent_data.py`，核心数据结构：

```python
# 每条样本：(用户输入, 子意图, 改写后query)
SAMPLES = {
    "chat": [
        ("你好", "greeting", "你好，我想和你打个招呼"),
        ("今天天气怎么样", "small_talk", "我想聊聊天，今天天气怎么样"),
        ("我今天心情不好", "emotion", "我心情低落，想找人倾诉和聊天"),
        ("你叫什么名字", "persona", "我想了解你的名称和身份信息"),
    ],
    "generation": [
        ("画一只猫", "image_gen", "请生成一张猫的图片，可爱风格，高清画质"),
        ("做个短视频", "video_gen", "请帮我制作一段15秒的短视频，内容为城市延时摄影"),
        ("生成一段背景音乐", "audio_gen", "请生成一段轻柔的背景音乐，钢琴为主，3分钟时长"),
        ("帮我写首诗", "text_gen", "请创作一首关于春天的现代诗，4-8行，意境优美"),
    ],
    # ... 其他意图
}
```

**自动增强策略**：

```python
# 前缀变体：模拟真实用户的不同开场方式
PREFIXES = ["帮我", "能不能", "我想", "麻烦", "请问", "能不能帮我"]

# 后缀变体：模拟口语化语气
SUFFIXES = ["吧", "呢", "啊", "一下", "可以吗", "嘛"]

def augment_query(query):
    """对短 query 添加前缀/后缀变体，扩充数据多样性"""
    variants = set()
    variants.add(query)
    if len(query) <= 12:
        for p in random.sample(PREFIXES, min(2, len(PREFIXES))):
            variants.add(p + query)
        for s in random.sample(SUFFIXES, min(2, len(SUFFIXES))):
            variants.add(query + s)
    return variants
```

**数据集拆分**：

```python
# 每个意图类别的拆分比例
eval_size = int(target * 0.15)    # 15% 验证集
test_size = int(target * 0.15)    # 15% 测试集
train_size = target - eval_size - test_size  # 70% 训练集
```

### 4.3 三轮数据增补

数据工程不是一次性工作。在「两环一核」中，@data-engineer 的产出要经过 @evaluation 的闸门检验，No-Go 回流时需要针对性补数据：

**Round 1**（初始 756 条）：

```
评测结果: coarse 78.4%, fine 30.9%
问题诊断: tool 类只有 70 条样本，远少于其他类别；fine 粒度数据不足
增补动作: +79 条 tool/search/歧义样本
```

**Round 2**（835 条）：

```
评测结果: coarse 91.4%, fine 81.5%
问题诊断: sub-intent 混淆严重——"翻译"被分到 code 而非 tool
增补动作: +46 条 sub-intent 歧义消歧样本
```

**Round 3**（881 条）：

```
评测结果: coarse 89.5%, fine 82.1%
问题诊断: tool 类 F1 仍只有 0.583，数据量仍然不够
当前状态: No-Go，需要继续增补 tool 类样本
```

**最终数据集**：

| 集合 | 样本数 | 说明 |
|------|--------|------|
| 训练集 | 881 | 包含增强变体 |
| 验证集 | 162 | 用于训练时早停 |
| 测试集 | 162 | 用于最终评测 |
| Schema | 6 coarse / 25 fine | 分类体系定义 |

### 4.4 SFT 数据格式

每条训练数据遵循 Alpaca 格式：

```json
{
  "instruction": "分析用户输入的意图，输出意图分类和改写后的查询。",
  "input": "画个好看的",
  "output": "{\"intent\": \"generation\", \"sub_intent\": \"image_gen\", \"rewritten_query\": \"请生成一张好看的图片，风格简约，色彩明亮\"}"
}
```

**设计决策**：
- `output` 是 JSON 字符串，不是自然语言——这迫使模型学会结构化输出
- `instruction` 固定不变——让模型聚焦于 input→output 的映射
- 改写结果放在 output 中与意图联合训练——一体化学习

---

## 五、训练算法（🎨 创造环 · 阶段 2 · @ml-trainer + @ml-alignment）

### 5.1 模型选型

| 参数 | 选择 | 理由 |
|------|------|------|
| 基座模型 | Qwen2.5-0.5B-base | 0.5B 参数量，48GB 内存轻松容纳；中文能力强 |
| 微调方法 | LoRA SFT | 只训练 2.1M 参数（0.44%），效率高，不易过拟合 |
| LoRA rank | 16, alpha=32 | alpha/rank=2，注意力层全覆盖（q/k/v/o_proj） |
| 训练精度 | fp32 (CPU) | Apple Silicon 上 BitsAndBytes 不可用，MPS + PEFT 有兼容问题 |
| 序列长度 | 256 | 意图分类 + 改写不需要长上下文 |

**为什么不选更大的模型**：
- 意图分类是**窄任务**——输入短、输出结构化、类别有限
- 0.5B + LoRA 的有效参数量约 2.1M，足以拟合 881 条训练数据的模式
- 更大的模型（1.5B、7B）在这个任务上不会有质的飞跃，但训练和推理成本翻倍

**为什么选 LoRA 而不是全参数微调**：
- 全参数微调 0.5B 模型需要更新 496M 参数，在 CPU 上不现实
- LoRA 只训练 2.1M 参数（0.44%），CPU 上 69 分钟即可完成
- LoRA 的 adapter 只有 8.3MB，便于版本管理和部署

### 5.2 训练超参数

```python
LEARNING_RATE = 2e-5     # LoRA 微调的典型学习率
NUM_EPOCHS = 5           # 小数据集需要多跑几轮
BATCH_SIZE = 4           # CPU 显存有限，小 batch
GRAD_ACCUM = 4           # 等效 batch_size = 16
LORA_RANK = 16           # LoRA 低秩分解的秩
LORA_ALPHA = 32          # LoRA 缩放因子，alpha/rank=2
LORA_DROPOUT = 0.05      # LoRA dropout 防过拟合
MAX_SEQ_LEN = 256        # 序列最大长度
WARMUP_RATIO = 0.1       # 前 10% 步骤线性升温
```

**超参数选择逻辑**：
- `LR=2e-5`：LoRA 微调的标准学习率，太大会导致训练不稳定
- `EPOCHS=5`：数据量小（881 条），需要多轮学习；但也不能太多，5 轮后 eval loss 开始 plateau
- `BATCH_SIZE=4, GRAD_ACCUM=4`：等效 batch=16，在 CPU 上是内存和收敛速度的平衡点
- `LORA_RANK=16`：注意力层全覆盖 + rank=16 是 0.5B 模型的甜蜜点；rank 太低（4/8）容量不够，太高（64/128）容易过拟合
- `ALPHA=32`（alpha/rank=2）：这是 LoRA 论文推荐的缩放比例

### 5.3 训练脚本核心实现

`scripts/train_intent.py` 的核心设计：

**数据集类**——预分词，训练时零拷贝：

```python
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
            labels[labels == tokenizer.pad_token_id] = -100  # pad token 不计入 loss
            self.encoded.append({"input_ids": ids, "attention_mask": mask, "labels": labels})
```

**关键决策**：
- 预分词：初始化时一次性分词完毕，训练时直接取 tensor，避免重复分词开销
- `labels = ids.clone()` + pad 设为 -100：标准的 causal LM 训练方式，模型学习预测每个 token
- 全序列做 labels（包括 Instruction 和 Input 部分）：简化实现，pad 部分已经被 -100 mask 掉了

**LoRA 配置**：

```python
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=LORA_RANK,                    # 秩 = 16
    lora_alpha=LORA_ALPHA,          # 缩放 = 32
    lora_dropout=LORA_DROPOUT,      # dropout = 0.05
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # 全注意力层
    bias="none",                    # 不训练 bias
)
model = get_peft_model(model, lora_config)
# 输出: trainable params: 2,162,688 || all params: 496,195,456 || trainable%: 0.4359
```

**训练循环**——手动实现，不依赖 Trainer：

```python
# 手动训练循环的优势：完全控制每一步，方便调试和定制
for epoch in range(NUM_EPOCHS):
    for batch_idx, batch in enumerate(train_loader):
        # 线性 warmup
        if global_step < warmup_steps:
            lr_scale = (global_step + 1) / warmup_steps
            for pg in optimizer.param_groups:
                pg['lr'] = LEARNING_RATE * lr_scale

        outputs = model(input_ids=batch["input_ids"],
                        attention_mask=batch["attention_mask"],
                        labels=batch["labels"])
        loss = outputs.loss / GRAD_ACCUM
        loss.backward()

        # 梯度累积
        if (batch_idx + 1) % GRAD_ACCUM == 0:
            torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)  # 梯度裁剪
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)  # 释放梯度内存
            global_step += 1
```

**为什么不用 HuggingFace Trainer**：
1. CPU 训练 + 手动循环更容易调试（MPS/BitsAndBytes 的坑需要精确控制每一步）
2. 不需要 Trainer 的分布式、混合精度等高级特性
3. 手动循环的代码更透明，出问题能快速定位

### 5.4 训练过程

```
5 epochs, LR=2e-5, batch=4, grad_accum=4
设备: CPU (Mac M4 Max 48GB)
时长: 69.4 分钟

Epoch 1: loss 2.54 → 1.14  (模型从随机输出开始，学会基本格式)
Epoch 2: loss 1.14 → 0.82  (学会大部分粗意图分类)
Epoch 3: loss 0.82 → 0.72  (细粒度分类开始收敛)
Epoch 4: loss 0.72 → 0.66  (改写质量提升)
Epoch 5: loss 0.66          (best eval loss: 0.638)

Loss 曲线采样: 3.11 → 2.47 → 2.10 → 1.09 → 0.78 → 0.72 → 0.66 → 0.59
```

**训练产出**：

```
models/intent-0.5b-v1/sft-checkpoint/
├── adapter_config.json          # LoRA 配置
├── adapter_model.safetensors    # LoRA 权重 (8.3MB)
├── tokenizer.json               # 分词器
├── tokenizer_config.json
├── chat_template.jinja
├── training_metrics.json        # 训练元数据
└── README.md
```

### 5.5 Apple Silicon 踩坑实录

| 坑 | 症状 | 解法 |
|----|------|------|
| BitsAndBytes 不可用 | `ImportError: Using bitsandbytes 4-bit quantization requires bitsandbytes` | 放弃 4-bit 量化，用 fp32 + LoRA。48GB 内存足够 |
| MPS + PEFT + gradient_checkpointing 冲突 | `RuntimeError: Placeholder storage has not been allocated on MPS device!` | 训练用 CPU，推理可以用 MPS |
| mlx-lm 与 transformers 5.x 不兼容 | `AttributeError: 'str' object has no attribute '__module__'` | 放弃 mlx-lm，用纯 transformers+PEFT |
| device_map="auto" 在 MPS 上行为不稳定 | MPS 设备上的 placeholder 错误 | 显式指定 device，不依赖自动映射 |
| 数据量不足导致低准确率 | 首轮 coarse 78.4%, fine 30.9% | 针对性增补 tool/search/歧义样本（3 轮迭代） |

**核心教训**：在 Apple Silicon 上，**先跑通再优化**。CPU fp32 训练虽然慢（69 min），但 100% 可靠。MPS 和 BitsAndBytes 的坑踩不完，先把模型训出来，再考虑加速。

---

## 六、评测闸门（🚦 闸门 · @evaluation 独立）

### 6.1 评测设计原则

评测是「两环一核」中**唯一有发布否决权**的角色。设计原则：

1. **对抗视角** — 评测的职责是找问题，不是证明没问题
2. **量化门控** — Go/No-Go 由数字决定，不由人决定
3. **分层诊断** — 总体准确率会掩盖局部问题，必须看每类 F1
4. **结构独立** — @evaluation 不归创造环管辖，不受"模型训了这么久不能不上线"的压力

### 6.2 评测指标设计

| 指标 | 计算方式 | 阈值 | 为什么 |
|------|---------|------|--------|
| 粗粒度准确率 | 6 类意图分类正确率 | ≥ 90% | 路由错误是致命的，粗意图错 = 用户被送到错误流程 |
| 细粒度准确率 | 25 类子意图分类正确率 | ≥ 85% | 执行精度要求，子意图错 = 执行结果偏差 |
| JSON 解析率 | 模型输出可解析为合法 JSON 的比例 | ≥ 90% | 解析失败 = 系统异常，不可接受 |
| 每类 F1 | 每个粗意图的 precision/recall/F1 | 诊断用 | 发现薄弱类别，指导数据增补 |

**为什么粗意图阈值比细意图高**：
- 粗意图错 = 路由到完全错误的下游（比如把"画个猫"路由到搜索引擎）
- 细意图错 = 路由到正确的类别但子分类偏了（比如把"代码调试"分成"代码解释"）
- 前者对用户体验的影响远大于后者

### 6.3 评测脚本核心实现

`scripts/eval_intent.py` 的关键逻辑：

**JSON 解析——三级容错**：

```python
def parse_output(text):
    """Parse model output to extract intent JSON."""
    # 1. 先提取 ### Response: 之后的部分
    if "### Response:" in text:
        text = text.split("### Response:")[-1].strip()

    # 2. 尝试直接 JSON 解析
    try:
        result = json.loads(text)
        if "intent" in result:
            return result
    except json.JSONDecodeError:
        pass

    # 3. 用正则提取包含 "intent" 键的 JSON 对象
    json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return result
        except json.JSONDecodeError:
            pass

    return None
```

**为什么需要三级容错**：
- 模型有时会在 JSON 前后加自然语言（"根据分析，结果是 {..."）
- 模型有时会生成多个 JSON 对象（只取第一个含 intent 的）
- 解析率 99.4% 证明三级容错是必要的

**Go/No-Go 判定**：

```python
go = coarse_acc >= 0.90 and fine_acc >= 0.85 and parse_rate >= 0.90
if go:
    print(f"✅ GO")
else:
    reasons = []
    if coarse_acc < 0.90:
        reasons.append(f"Coarse acc {coarse_acc:.2%} < 90%")
    if fine_acc < 0.85:
        reasons.append(f"Fine acc {fine_acc:.2%} < 85%")
    if parse_rate < 0.90:
        reasons.append(f"Parse rate {parse_rate:.2%} < 90%")
    print(f"❌ NO-GO — {'; '.join(reasons)}")
```

### 6.4 评测结果与诊断

| 指标 | 值 | 阈值 | 状态 |
|------|-----|------|------|
| 粗粒度准确率 | 89.5% | ≥ 90% | ⚠️ 差 0.5% |
| 细粒度准确率 | 82.1% | ≥ 85% | ⚠️ 差 2.9% |
| JSON 解析率 | 99.4% | ≥ 90% | ✅ 通过 |
| **整体判定** | **No-Go** | | 需要继续迭代 |

**系统性错误诊断**：

| 错误类型 | 示例 | 原因 | 修复方向 |
|---------|------|------|---------|
| `tool/translate` → `code/translate` | "翻译一下这段话" | 训练数据中 code 类含有大量 "翻译" 措辞，模型学到了错误关联 | 增补 tool/translate 的歧义消歧样本 |
| `tool/file_op` → `tool/file_manager` | "帮我整理一下文件" | 模型输出了 schema 外的子意图 `file_manager` | 在训练数据中强化 schema 约束 |
| 粗意图边界模糊 | code vs math | "算一下" 既可能是 math/computation 也可能是 code/write | 增补边界歧义样本 |

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

### 6.5 No-Go 回流机制

在「两环一核」中，@evaluation 的 No-Go 不是终点，而是**定向反馈**：

```
No-Go → @data-engineer 补数据（针对性增补弱点类别）
      → @ml-trainer 再训练（使用增补后的数据集）
      → @evaluation 再评测
      → 最多 2 轮回退，超过 2 轮上报 CEO/用户
```

3 轮迭代的缺陷分析：

| 轮次 | 主要问题 | 增补动作 | 效果 |
|------|---------|---------|------|
| Round 1 | tool 类只有 70 条样本 | +79 条 tool/search/歧义 | coarse 78.4% → 91.4% |
| Round 2 | sub-intent 混淆 | +46 条歧义消歧样本 | fine 30.9% → 81.5% |
| Round 3 | tool F1 仍低 (0.583) | 需要继续增补 | fine 81.5% → 82.1% |

---

## 七、推理部署（🚀 推广环 · 阶段 3 · @ml-serving + @backend + @infra）

即使评测是 No-Go，部署链路也要提前跑通——这是「两环一核」的设计哲学：**创造环和推广环可以并行准备**。下次模型通过评测闸门，可以立即上线。

### 7.1 Step 1：合并 LoRA → 独立模型

**为什么需要合并**：
- LoRA 适配器（8.3MB）需要基座模型（942MB）+ peft 库才能运行
- 合并后变成独立模型，**去掉 peft 运行时依赖**，加载更快、部署更简单
- 合并操作是不可逆的（权重已融合），但 LoRA 原始 checkpoint 仍然保留

**合并脚本** `scripts/merge_lora.py`：

```python
# 1. 加载基座模型
model = AutoModelForCausalLM.from_pretrained(
    args.base, trust_remote_code=True, torch_dtype=torch.float16,
)

# 2. 加载 LoRA 适配器
model = PeftModel.from_pretrained(model, args.adapter)

# 3. 合并权重（将 LoRA 矩阵折叠回原始权重）
model = model.merge_and_unload()

# 4. 保存为独立模型
model.save_pretrained(args.output, safe_serialization=True)
tokenizer.save_pretrained(args.output)
```

```bash
# 运行
python3 scripts/merge_lora.py
# 输入: base (942MB) + adapter (8.3MB)
# 输出: merged/ (942MB, 独立模型，无需 peft)
# 耗时: 1.4 秒
```

**合并前后对比**：

| 维度 | 合并前 (base + LoRA) | 合并后 (merged) |
|------|---------------------|-----------------|
| 加载依赖 | transformers + peft | 仅 transformers |
| 加载步骤 | 加载 base → 加载 adapter → 组合 | 一步加载 |
| 模型大小 | 942MB + 8.3MB | 942MB（权重已融合） |
| 推理精度 | 相同 | 相同（数学等价） |
| 适用场景 | 开发/实验 | 生产部署 |

### 7.2 Step 2：FastAPI 推理服务

`scripts/serve_intent.py` 的架构设计：

```
┌─────────────────────────────────────────────┐
│  FastAPI + Uvicorn (port 8100)              │
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐ │
│  │ /health │  │ /intent  │  │/intent/batch│ │
│  └─────────┘  └──────────┘  └────────────┘ │
│       │            │              │         │
│       └────────────┼──────────────┘         │
│                    │                        │
│            ┌───────┴───────┐                │
│            │ ModelManager  │                │
│            │ (常驻内存)     │                │
│            │               │                │
│            │ merged model  │                │
│            │ + tokenizer   │                │
│            └───────────────┘                │
└─────────────────────────────────────────────┘
```

**API 端点设计**：

```bash
# 1. 健康检查
GET /health
→ {"status": "ok", "model": "intent-0.5b-v1 (merged)", "device": "cpu", "uptime_seconds": 1.3}

# 2. 单条推理
POST /intent
Body: {"query": "帮我画个猫"}
→ {"query": "帮我画个猫",
   "intent": "generation",
   "sub_intent": "image_gen",
   "rewritten_query": "请生成一张猫的卡通画，画风可爱",
   "parse_success": true,
   "latency_ms": 1235.3}

# 3. 批量推理
POST /intent/batch
Body: {"queries": ["你好", "画个好看的", "帮我写个快排"]}
→ {"results": [...], "total_latency_ms": 5208}
```

**Pydantic 请求/响应模型**——自动校验 + 自动文档：

```python
class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)

class IntentResponse(BaseModel):
    query: str
    intent: Optional[str] = None
    sub_intent: Optional[str] = None
    rewritten_query: Optional[str] = None
    raw_output: Optional[str] = None
    parse_success: bool
    latency_ms: float
```

**模型生命周期管理**——用 FastAPI lifespan 替代已弃用的 on_event：

```python
@asynccontextmanager
async def lifespan(application: FastAPI):
    """启动时加载模型，关闭时释放"""
    args = application.state.args
    mgr.load(args)         # 加载模型到内存
    yield
    print("Shutting down...")  # 清理

app = FastAPI(lifespan=lifespan)
```

**双模式加载**——支持合并模型和 base+LoRA 两种模式：

```python
class ModelManager:
    def load(self, args):
        if not args.lora and os.path.isdir(DEFAULT_MERGED):
            # 模式 1: 加载合并后的独立模型（推荐，无需 peft）
            self.model = AutoModelForCausalLM.from_pretrained(args.model_path, ...)
        elif args.lora or not os.path.isdir(DEFAULT_MERGED):
            # 模式 2: 加载 base + LoRA（开发/调试用）
            from peft import PeftModel
            self.model = AutoModelForCausalLM.from_pretrained(DEFAULT_BASE, ...)
            self.model = PeftModel.from_pretrained(self.model, DEFAULT_ADAPTER)
```

**启动与使用**：

```bash
# 启动服务
python3 scripts/serve_intent.py --port 8100         # 默认: 合并模型, CPU
python3 scripts/serve_intent.py --device mps        # MPS 加速 (推理正常, ~50-200ms)
python3 scripts/serve_intent.py --lora              # 用 base+LoRA 模式

# 或用 uvicorn 直接启动
uvicorn serve_intent:app --host 0.0.0.0 --port 8100
```

**API 设计原则**：
- 模型常驻内存，避免冷启动（首次加载 ~3s，后续推理 ~1s/query on CPU）
- 返回 `latency_ms` 字段，便于监控和 SLA 管理
- `parse_success` 字段区分成功/失败，下游可以做降级处理
- Pydantic 做请求/响应校验，FastAPI 自动生成 OpenAPI 文档

### 7.3 Step 3：Docker 容器化

`Dockerfile.serve` 的设计要点：

```dockerfile
FROM python:3.11-slim

# 只安装运行时依赖（不含训练库）
RUN pip install --no-cache-dir \
    torch==2.7.0 \
    transformers>=5.0.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.30.0 \
    pydantic>=2.0.0 \
    safetensors>=0.4.0 \
    accelerate>=1.0.0

# 只打包 merged 模型 + serving 代码
COPY scripts/serve_intent.py /app/serve_intent.py
COPY models/intent-0.5b-v1/merged/ /app/models/intent-0.5b-v1/merged/

# 内置健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl http://localhost:8100/health || exit 1

CMD ["python3", "/app/serve_intent.py", "--port", "8100", "--device", "cpu"]
```

```bash
# 构建
docker build -f Dockerfile.serve -t intent-api:latest .

# 运行
docker run -p 8100:8100 intent-api:latest

# 验证
curl http://localhost:8100/health
```

预计镜像大小 ~1.5GB（python:3.11-slim + torch CPU + 模型权重）。

**容器化关键决策**：
- 不安装 peft——合并模型不需要
- 不包含训练脚本和数据——镜像只做推理
- 使用 CPU torch——Docker 通常运行在 Linux 服务器上，如果有 GPU 可以换 torch 的 CUDA 版本
- 内置 HEALTHCHECK——容器编排系统（K8s/ECS）可以自动检测服务健康

### 7.4 推理性能

| 设备 | 单条延迟 | 批量 (5 条) | 说明 |
|------|---------|------------|------|
| CPU (M4 Max) | ~1000-1300ms | ~5200ms | fp16, 0.5B 模型 |
| MPS (M4 Max) | ~50-200ms (预估) | ~300-800ms (预估) | 推理时 MPS 正常，只有训练有兼容问题 |
| Docker (Linux CPU) | ~800-1200ms (预估) | ~4000-6000ms (预估) | 取决于服务器配置 |

---

## 八、应用集成（🚀 推广环 · 阶段 4 · @growth + @devrel）

### 8.1 意图识别在 AI 助手中的位置

意图识别模型不是独立产品，而是 AI 助手的**路由层**：

```
用户输入
  │
  ├── 意图识别模型 (本模型)
  │     → intent + sub_intent + rewritten_query
  │
  └── 路由分发
        ├── chat/* → 对话引擎
        ├── search/* → RAG/搜索引擎
        ├── generation/* → 图片/视频/音频生成引擎
        ├── code/* → 代码引擎 (Claude Code / Copilot)
        ├── math/* → 数学推理引擎
        └── tool/* → 工具调用引擎 (Function Calling)
```

**改写后的 query 如何提升下游效果**：

| 场景 | 原始 query | 改写后 query | 下游效果提升 |
|------|-----------|-------------|------------|
| 模糊输入 | "画个好看的" | "请生成一张好看的图片，风格简约，色彩明亮" | 图片生成模型收到更具体的指令，出图质量更高 |
| 含指代 | "帮我弄一下那个" | "请帮我整理指定目录下的文件" | 工具调用引擎收到明确的操作指令 |
| 口语化 | "代码跑不通" | "请检查代码运行状态，分析错误原因并提供修复方案" | 代码引擎收到结构化的调试请求 |

### 8.2 集成方式

```python
import httpx

INTENT_API = "http://localhost:8100"

async def route_query(user_input: str):
    """意图识别 + 路由分发"""
    # 1. 调用意图识别 API
    resp = await httpx.post(f"{INTENT_API}/intent", json={"query": user_input})
    result = resp.json()

    if not result["parse_success"]:
        return {"error": "意图识别失败", "raw": result["raw_output"]}

    intent = result["intent"]
    sub_intent = result["sub_intent"]
    rewritten = result["rewritten_query"]

    # 2. 根据意图路由到下游执行器
    if intent == "chat":
        return await call_chat_engine(rewritten)
    elif intent == "search":
        return await call_search_engine(rewritten)
    elif intent == "generation":
        return await call_generation_engine(sub_intent, rewritten)
    elif intent == "code":
        return await call_code_engine(sub_intent, rewritten)
    elif intent == "math":
        return await call_math_engine(rewritten)
    elif intent == "tool":
        return await call_tool_engine(sub_intent, rewritten)
```

### 8.3 降级策略

意图识别可能失败（parse_success=false）或延迟过高，需要降级：

```python
# 1. 解析失败 → 用规则引擎兜底
if not result["parse_success"]:
    intent = rule_based_classify(user_input)  # 关键词匹配兜底
    rewritten = user_input  # 不改写，直接用原始 query

# 2. 延迟过高 → 异步调用 + 超时降级
try:
    resp = await httpx.post(f"{INTENT_API}/intent",
                           json={"query": user_input},
                           timeout=2.0)  # 2 秒超时
except httpx.TimeoutException:
    intent = rule_based_classify(user_input)
    rewritten = user_input
```

---

## 九、流程全景：DAG 闭环

把上面的实践映射回两环一核的 DAG，整条链路是这样的：

```
@ceo 定方向（意图识别 + query 改写）
  └── @po 出 PRD（6 类粗意图 + 25 类细意图 + 改写规则 + schema.json）
        ├── @data-strategy 定数据标准（schema + 样本分布 + 增强策略）
        │     └── @data-engineer 生成/清洗数据（881 train + 162 eval + 162 test）
        │           └── @ml-trainer 训练（Qwen2.5-0.5B + LoRA, 69 min on CPU）
        │                 └── @evaluation 评测 → No-Go（coarse 89.5% < 90%）
        │                       ├── No-Go 回流 → 补数据再训（已做 3 轮）
        │                       └── 推广环并行准备 ↓
        │
        └── @ml-serving 合并 LoRA → 独立模型 (1.4s)
              └── @backend 封 FastAPI（/intent, /intent/batch, /health）
                    └── @infra Docker 容器化 + 健康检查
                          └── @devrel 集成文档 + 示例代码
```

**关键观察**：

1. **评测闸门阻断了上线**——这是正确的行为。模型在 `tool/translate` 和 `tool/file_op` 上有系统性错误，不应该带着已知缺陷上线。
2. **推广环提前跑通了部署链路**——即使模型还没 Go，部署基础设施已就绪。下次模型通过评测，可以立即上线。
3. **3 轮 No-Go 都有明确的缺陷分析**——评测不只是打分，而是指出"哪里错了、怎么修"。第 1 轮 tool 数据不足，第 2 轮 sub-intent 歧义，第 3 轮 tool F1 仍低——每次都有针对性解法。
4. **创造环和推广环并行**——这是「两环一核」的核心优势：不等评测 Go 才开始做部署。

---

## 十、最佳实践总结

### 10.1 架构设计

| 实践 | 说明 |
|------|------|
| **按价值流分阶段，不按部门划分** | 一人公司的瓶颈是认知切换，不是组织协调 |
| **评测独立为闸门** | 结构独立 > 文化独立，否则生产压力必然侵蚀评测 |
| **MLOps 横向支撑** | 不属于任何阶段，为全链路提供自动化 |
| **最多 2 轮回退** | 超过 2 轮上报用户/CEO，避免无限循环 |
| **不提前建能力中心** | 流水线没跑通就建中台是过度设计（阿里教训） |
| **创造环和推广环并行** | 评测 No-Go 不阻塞部署链路建设 |

### 10.2 数据工程

| 实践 | 说明 |
|------|------|
| **Schema 先行** | 先定义分类体系，数据生成才有锚点 |
| **覆盖度 > 数量** | 每个子意图至少 8-10 条基础样本，比一个子意图堆 100 条有效 |
| **自动增强** | 前缀/后缀变体是零成本的多样性提升 |
| **歧义样本手动构造** | 类别边界上的易混淆样本无法自动生成，必须人工构造 |
| **三轮增补策略** | 初始生成 → 评测发现弱点 → 针对性增补 → 再评测，比一次性堆量高效 |

### 10.3 模型训练

| 实践 | 说明 |
|------|------|
| **0.5B 模型够用就别上大模型** | 意图分类是窄任务，0.5B + LoRA 足够 |
| **先跑通再优化** | CPU fp32 训练虽然慢（69 min），但可靠；MPS/BitsAndBytes 的坑踩不完 |
| **数据质量 > 数据量** | 3 轮针对性增补比盲目堆量有效 |
| **双任务一体化** | 意图分类 + query 改写在同一个模型里完成，避免级联错误 |
| **LoRA rank=16, alpha=32** | 注意力层全覆盖，0.44% 参数量，在 0.5B 模型上是甜蜜点 |
| **手动训练循环** | CPU + LoRA 场景下比 HuggingFace Trainer 更易调试 |

### 10.4 评测与部署

| 实践 | 说明 |
|------|------|
| **Go/No-Go 门控** | 评测不过就是 No-Go，不要"先上线再观察" |
| **评测要对抗视角** | 找问题 > 证明没问题；每类 F1 比总体准确率更有诊断价值 |
| **三级容错解析** | 模型输出不总是完美 JSON，需要 direct parse → regex → broad regex |
| **合并 LoRA 再部署** | 去掉 peft 运行时依赖，模型加载更快 |
| **部署链路提前跑通** | 推广环和创造环并行，不等评测 Go 才开始做部署 |
| **API 返回延迟指标** | `latency_ms` 字段为后续 SLA 和监控打基础 |
| **Docker 只打包推理** | 不含训练脚本和数据，镜像更小更安全 |

### 10.5 Apple Silicon 特别注意

| 坑 | 解法 |
|----|------|
| BitsAndBytes 不支持 Apple Silicon | 用 fp32 + LoRA，48GB 内存足够 |
| MPS + PEFT + gradient_checkpointting 不兼容 | 训练用 CPU，推理可以试 MPS |
| mlx-lm 与 transformers 5.x 不兼容 | 放弃 mlx-lm，用纯 transformers |
| device_map="auto" 在 MPS 上行为不稳定 | 显式指定 device，不依赖自动映射 |
| 数据量不足导致低准确率 | 针对性增补弱点类别，比堆总量有效 |

---

## 十一、文件清单

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
│   ├── generate_intent_data.py  # 数据生成脚本（含增强策略）
│   ├── train_intent.py          # LoRA SFT 训练脚本（手动循环）
│   ├── eval_intent.py           # 评测 + Go/No-Go 判定
│   ├── inference_intent.py      # CLI 交互式推理
│   ├── merge_lora.py            # LoRA 合并 → 独立模型
│   └── serve_intent.py          # FastAPI 推理服务（含双模式加载）
├── models/intent-0.5b-v1/
│   ├── sft-checkpoint/          # LoRA 适配器 (8.3MB)
│   │   ├── adapter_config.json  # LoRA 配置
│   │   ├── adapter_model.safetensors  # LoRA 权重
│   │   └── training_metrics.json      # 训练元数据
│   ├── merged/                  # 合并后独立模型 (942MB)
│   │   ├── model.safetensors    # 融合后的完整权重
│   │   ├── config.json
│   │   └── tokenizer.json
│   ├── eval_results.json        # 评测结果
│   └── examples.json            # 推理示例
├── Dockerfile.serve             # Docker 部署文件
└── install.sh                   # 一键安装到目标项目
```

---

## 十二、下一步

1. **补数据再训** — 针对 tool/translate 和 tool/file_op 的系统性错误，增补 50-100 条样本
2. **通过评测闸门** — 目标 coarse ≥ 92%, fine ≥ 87%（留 buffer）
3. **MPS 推理优化** — 推理阶段用 MPS 加速，目标延迟 < 200ms
4. **集成到 AI 助手** — 意图识别作为路由层，上游接收用户 query，下游分发到各执行器
5. **线上 AB 测试** — @evaluation 设计 AB 实验，验证改写后的 query 是否真的提升了下游执行效果
6. **模型版本管理** — @mlops 建立模型注册机制，支持灰度发布和回滚

---

*本文基于 model-factory-skills 的真实开发过程撰写，所有数据和代码均可在仓库中复现。*
