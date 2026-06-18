# 7B 代码模型 · vLLM IDE 补全 · 延迟优化方案

> 目标：把 P95 900ms 压到 IDE 补全可接受区间（理想 ≤300ms，可接受 ≤500ms），同时不丢代码生成能力。
> 约束：补全场景 = 延迟极敏感 + 代码任务属于量化"易受损项"——这两点决定了下面的优先级排序。

---

## 0. 先 profile，别瞎调（30 分钟内必做）

按 `engines-and-serving.md` 的反模式：**优化前先 profile，瓶颈在显存、算力还是 KV cache，对策不同。**

补全场景的典型延迟构成：

| 阶段 | 瓶颈类型 | 说明 |
|------|----------|------|
| 网络/排队 | 调度 | IDE 到服务的 RTT、vLLM 队列等待 |
| Prefill | 算力密集 | 当前文件上下文（可能几 K token）一次性算 attention |
| Decode | **显存带宽密集** | 逐 token 生成，7B 在 A10/A100 上每 token 主要卡带宽 |
| 首包返回 | TTFT | 补全尤其看 TTFT，不是只看 P95 端到端 |

**先抓两个数：**
1. `TTFT`（time to first token）和 `ITL`（inter-token latency）分别多少——900ms 是端到端，是卡在首包还是 decode 速率？这俩对策完全不同。
2. 真实负载下的并发 QPS——补全是高并发突发（多开发者同时敲键盘），不是单请求。只测单请求延迟会**严重误判**。

> `engines-and-serving.md` 陷阱表："只测单请求延迟 → 实际是并发场景，要测吞吐"。补全就是典型并发场景。

---

## 1. 引擎层：vLLM 留着，但要调对（Step 1 + engines-and-serving）

vLLM 选型没错（通用首选），问题是默认配置不适合补全。按 `engines-and-serving.md` checklist 逐项过：

### 1.1 continuous batching —— 确认真开了
默认开，但要确认你的部署版本没有覆盖成 `--disable-batch` 或等价项。**不开 = 吞吐差 10x**，多个开发者并发时延迟直接爆炸。这是 ROI 最高的一个开关。

### 1.2 chunked prefill —— 补全场景必开（关键）
补全的 prompt 是"当前文件 + 光标前上下文"，长 prompt 的 prefill 会把后面所有短请求（其它开发者的一次性补全）饿死，直接抬高整体 P95。

> `engines-and-serving.md` 陷阱表："长 prompt 把短请求饿死 → 用 chunked prefill"。

vLLM 参数：`--enable-chunked-prefill`。配套调 `--max-num-batched-tokens`（典型 2048~4096，按显存试）。**这一项大概率是 900ms 的主因之一**。

### 1.3 prefix caching —— 强烈建议开
IDE 补全有大量重复前缀：
- 同一个文件连续补全，system prompt + 文件头部完全复用
- FIM（fill-in-the-middle）模板固定
- 语言/项目级的重复 preamble

> `engines-and-serving.md`：prefix caching 对"固定 system prompt 场景大幅降本"，SGLang/vLLM 都支持。

vLLM 参数：`--enable-prefix-caching`。对补全的 TTFT 下降非常直接——文件头部的 KV cache 不用重算。

### 1.4 KV cache 大小 —— 按显存给足
> `cost-model.md` 杠杆第 2 条 + `engines-and-serving.md` 陷阱："KV cache 太小 → 并发上不去，加显存给 KV"。

7B FP16 权重约 14GB。A10（24GB）装得下但要给 KV 留够；A100（40/80GB）充裕。把 `--gpu-memory-utilization` 调到 0.9 左右（留余量防 OOM），让 vLLM 把剩余显存尽量分给 KV cache，提并发。

### 1.5 max_num_seqs —— 按真实并发调
补全是突发并发。默认值（256）可能偏大导致排队，或偏小导致拒绝。**用真实开发者并发负载压测**，找到延迟不崩的甜点。

### 1.6 Speculative Decoding —— 延迟敏感场景上（重点）
> `engines-and-serving.md`：speculative decoding "适合对延迟敏感的场景"，"小模型/草稿模型先猜，大模型批量验证"。

补全 = 逐 token 输出 + 延迟极敏感 = speculative decoding 的理想场景。方案：
- 用一个 0.5B~1.5B 的小代码模型（或自己拿通用小模型微调）做 draft
- vLLM 支持 `--speculative-model` + `--num-speculative-tokens`（建议 3~5）
- 对纯吞吐可能持平或微降，但**单请求延迟能降 1.5x~2x**，补全要的就是这个

代价：多一个 draft 模型的显存 + 工程复杂度。延迟达标后再考虑。

### 1.7（可选）TensorRT-LLM —— 延迟极致再上
> SKILL.md Step 1："延迟极致场景再上 TensorRT-LLM"。如果上面全做完还达不到目标，且你们有 H 系列、愿意深度调优，再考虑迁移。优先级低于先把 vLLM 调对。

---

## 2. 量化层：代码任务要小心，分级量化（Step 2 + quantization）

**这是保代码能力的核心战场。** 按 `quantization.md` 的关键认知——量化损失不均匀，**代码属于"易受损项"**：

> quantization.md 易损表："代码（细节易错）"在易受损列。
> "任务对精度极敏感（数学/代码/长文）？→ 慎用 4bit，至少 FP8 或 INT8，且必测。"

所以决策：**不要一上来就 INT4。** 分级走：

### 2.1 首选 FP8（如果有 H100/A100-late）
> quantization.md："FP8 精度损失很小，~50% 显存节省，适合质量敏感场景"。
> "到 2025-2026 主流：FP8（H100）或 AWQ/GPTQ INT4 是两大主力方向"。

FP8 几乎无损，又能省一半显存多塞并发，是代码场景的最佳起点。H100 直接用；A100 不原生支持 FP8 则退回下一档。

### 2.2 次选 INT8（W8A16）
> quantization.md："W8A16（权重 8bit 激活 16bit）更稳"，"激活量化比权重量化更敏感"。

A 系列硬件上，W8A16 是稳妥选择：权重 8bit 省 ~50% 显存，激活保持 FP16，代码细节能力损失小。**避免 W8A8**（激活也量化），代码生成更容易出错。

### 2.3 INT4（AWQ/GPTQ）—— 只在前两档不够、且评测能扛时
> quantization.md："AWQ 识别'重要'权重保高精度，通常比朴素 INT4 好"。

如果显存极度紧张（比如要塞进更小的卡降本），才考虑 AWQ INT4。**且必须用 IDE 补全的真实分布数据做校准**，不是随便抓的通用语料：

> quantization.md："校准数据用贴近真实分布的数据（不是随便抓的）"。

用你们微调时的代码语料、FIM 样本做校准集。

### 2.4 量化前后必测（关键，保代码能力的护城河）
> quantization.md："量化必须在你要部署的任务上测，不能只看通用 benchmark"。

通用 HumanEval 不够，要测**补全场景特化**：

| 维度 | 具体测法 |
|------|----------|
| 代码生成 | HumanEval / MBPP / 你们内部代码任务集，对照 FP16 基线 |
| 补全质量 | FIM（fill-in-the-middle）准确率——补全特有，不是 generate 指标 |
| 易损项重点 | 边界条件、缩进/括号、跨行补全——这些 INT4 最容易出错 |
| 人工抽检 | "量化有时变啰嗦或重复"——补全场景啰嗦=废，必人工看 |

**红线**：如果 INT4 让 HumanEval pass@1 掉超过 ~2-3 个百分点，或 FIM 准确率明显下降，**退回 INT8/FP8**。代码补全对正确性零容忍。

---

## 3. 成本核算（Step 4 + cost-model）

压延迟往往伴随成本变化，按 `cost-model.md` 公式算清楚：

```
单 token 成本 = GPU 时薪 / (每小时产出 token 数)
每小时产出 = 吞吐(tokens/s/卡) × 卡数 × 3600
```

### 3.1 关键：别用厂商理论吞吐
> cost-model.md："别用厂商理论吞吐，实测通常打折扣"。
> "推理成本 ≤ 商业定价的 40%（毛利保护线）"。

### 3.2 显存带宽是瓶颈，不是算力
> cost-model.md："大模型推理（尤其 decode）瓶颈常在显存带宽，不是算力"。

7B decode 阶段主要卡带宽 → 这就是为什么量化能同时降延迟和降成本（权重搬动量减半）。

### 3.3 选卡
- A10（24GB）：能跑 7B FP16 + 一定 KV，性价比好，是补全的主力候选
- A100（40/80GB）：KV 充裕、并发高，流量大时更划算
- H100：如果走 FP8 路线，H 系列原生支持，吞吐/质量双优

按 P50/P80 容量规划，峰值靠自动扩缩容，**别按峰值常开**（补全有明显的工作时段尖峰）。

### 3.4 ROI 排序（先做哪个）
> cost-model.md 杠杆按 ROI 排序：
1. continuous batching（确认开）— ROI 最高
2. chunked prefill + prefix caching — 补全场景几乎免费
3. 量化 FP8/INT8 — 降延迟+降成本双杀
4. speculative decoding — 延迟达标的最后一块拼图

---

## 4. 对照 benchmark + 可回滚部署（Step 5）

### 4.1 对照表（量化/优化前后）

| 配置 | TTFT P95 | ITL | 端到端 P95 | 吞吐 | 单 token 成本 | HumanEval pass@1 | FIM 准确率 |
|------|----------|-----|-----------|------|---------------|------------------|-----------|
| FP16 默认配置（现状） | ? | ? | **900ms** | ? | ? | 基准 | 基准 |
| FP16 + chunked prefill + prefix cache | ? | ? | ? | ? | ? | =基准 | =基准 |
| + FP8/INT8 量化 | ? | ? | ? | ? | ? | ? | ? |
| + speculative decoding | ? | ? | **目标 ≤300-500ms** | ? | ? | ? | ? |
| (若需要) AWQ INT4 | ? | ? | ? | ? | ? | **重点盯** | **重点盯** |

**每个配置都要填实测数，不能靠感觉。**

### 4.2 可回滚（硬约束）
> SKILL.md 反模式："优化方案不可回滚，量化出问题没法切回"。

- **保留 FP16 全精度 checkpoint，别删**
- 服务层做配置切换：量化版本和 FP16 版本作为可切换的 serving 后端
- 量化上线后挂监控，代码补全质量指标（FIM 准确率、用户 accept rate）一旦下降 → 一键切回 FP16
- 交给 @backend 封装 API（多版本路由），@infra 部署延迟/成本/质量三套监控告警

---

## 5. 执行顺序（45 分钟时间盒内可先验证可行性）

1. **[10min]** profile：拆 TTFT vs ITL，拉真实并发负载，确认瓶颈
2. **[10min]** vLLM 调参：chunked prefill + prefix caching + KV cache 给足——**大概率单这一步就能砍掉一大块延迟**
3. **[10min]** 量化候选：FP8（H 系列）或 W8A16 INT8，跑补全特化评测
4. **[5min]** 成本核算：实测吞吐，对照 40% 毛利线
5. **[10min]** 若仍未达标：上 speculative decoding（draft 小模型）
6. **[持续]** 部署 + 可回滚 + 三套监控

---

## 关键判断（为什么这套方案适合补全场景）

1. **延迟 vs 精度的张力点在量化**：补全延迟极敏感（推你激进量化），但代码又是最怕量化的任务（拉你保守）。解法是**引擎层先把延迟压下来**（chunked prefill/prefix cache/continuous batching 几乎无损），**量化只做到 FP8/INT8 这个低损档**，不为压延迟强行 INT4。
2. **prefix caching 是补全的天然红利**：同文件连续补全、固定 FIM 模板 = 大量重复前缀，这是 vLLM prefix cache 最赚的场景。
3. **speculative decoding 是补全的杀手锏**：逐 token + 延迟敏感 = 草稿模型收益最大化。
4. **评测必须补全特化**：HumanEval 不够，FIM 准确率 + 易损项人工抽检才是代码能力的真护城河。
