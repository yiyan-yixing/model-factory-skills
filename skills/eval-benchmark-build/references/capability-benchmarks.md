# 公开能力 Benchmark 清单

> 不用从零造评测。**先用公开 benchmark 打底，再叠加你的垂直 benchmark。**
> 注意：公开 benchmark 有**数据污染**风险（泄露进训练集），分数要打折扣看。

## 通用知识

| Benchmark | 测什么 |
|-----------|--------|
| MMLU | 多学科多选知识（经典基线） |
| MMLU-Pro | MMLU 升级版，更难 |
| ARC | 科学推理多选 |
| HellaSwag | 常识推理 |
| TruthfulQA | 抗误区/抗幻觉 |
| GPQA | 研究生级难题（防污染用） |

## 数学 / 推理

| Benchmark | 测什么 |
|-----------|--------|
| GSM8K | 小学应用题（基础数学） |
| MATH | 竞赛数学（难） |
| AIME / AMC | 高难竞赛（顶配模型才上） |

## 代码

| Benchmark | 测什么 |
|-----------|--------|
| HumanEval / HumanEval+ | Python 函数生成（执行评测） |
| MBPP | 基础编程任务 |
| LiveCodeBench | **按时间分窗**，防数据污染（推荐） |
| BigCodeBench | 复杂代码任务 |

## 中文

| Benchmark | 测什么 |
|-----------|--------|
| C-Eval | 中文多学科 |
| CMMLU | 中文多选知识 |
| GAOKAO | 中文高考题 |

## 指令跟随

| Benchmark | 测什么 |
|-----------|--------|
| IFEval | 可验证的指令约束遵循 |
| FollowBench | 多级指令跟随难度 |

## Agent / 工具调用

| Benchmark | 测什么 |
|-----------|--------|
| BFCL（Berkeley Function Calling Leaderboard） | 函数/工具调用 |
| GAIA | 通用 Agent 助手（多步推理） |
| τ-bench | 多轮工具调用 Agent |

## 长上下文

| Benchmark | 测什么 |
|-----------|--------|
| RULER | 长上下文综合（可调长度） |
| LongBench | 长文本任务 |
| NIAH（Needle in a Haystack） | 长文里找信息（经典） |

## 怎么用这些 benchmark（方法论）

1. **按能力目标挑**：你的模型要强什么 → 选对应 benchmark（别全跑，浪费）
2. **关注数据污染**：优先用**按时间分窗**的（LiveCodeBench）或**私有/新生成**的，防泄露虚高
3. **对照基线**：必须和基座/竞品同条件跑，绝对分没意义
4. **公开 benchmark 是起点**：真正决定产品成败的是你的**垂直 benchmark + 真实流量抽检**
5. **定期更新**：benchmark 会过时/被污染，定期换新的

## 重要警示：数据污染

> 公开 benchmark 数据**可能已被训练数据抓取** → 模型"见过题" → 分数虚高。
> 应对：
> - 用时间分窗 benchmark（LiveCodeBench 等）
> - 自建**私有评测集**（不公开、不进训练）
> - 对异常高分保持怀疑，交叉验证

## 参考来源

- 各 benchmark 原始论文/官方站点
- HELM / Open LLM Leaderboard（聚合评测框架）
- benchmark 会迭代，以最新版本为准
