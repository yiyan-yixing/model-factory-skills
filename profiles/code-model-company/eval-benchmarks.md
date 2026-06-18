# 代码评测基准

> 代码大模型的**优势是可客观评测**——代码能跑，对就是对。用好执行式评测 + 防污染，是代码大模型评测的核心。
> 通用评测方法论见 `skills/eval-benchmark-build/references/`，本页只讲代码特有。

## 代码 benchmark 清单

### 基础生成（执行式，pass@k）

| Benchmark | 说明 |
|-----------|------|
| **HumanEval** | Python 函数生成，经典基线（⚠️ 易污染） |
| **HumanEval+** | HumanEval 增强测试用例版，更严 |
| **MBPP** | 基础编程任务 |

### 防污染（推荐主力）

| Benchmark | 说明 |
|-----------|------|
| **LiveCodeBench** | **按时间分窗**，新题持续加入，防训练数据泄露 ← 主力推荐 |
| **BigCodeBench** | 复杂代码任务，多工具/多步 |

### 多语言

| Benchmark | 说明 |
|-----------|------|
| **MultiPL-E** | HumanEval/MBPP 多语言翻译版 |

### 补全 / FIM（Fill-in-the-Middle）

- IDE 补全场景特有：给定前后文，补中间
- 评测补全准确率 + 延迟（IDE 对延迟极敏感）

### 代码 Agent（高阶差异化）

| Benchmark | 说明 |
|-----------|------|
| **SWE-bench / SWE-bench Lite** | 真实 GitHub issue 修复（端到端 Agent 能力） |
| **SWE-bench Verified** | 人工校验版，更可靠 |

### 仓库级 / 长上下文

- 跨文件理解、整个 repo 上下文的代码任务
- 长上下文能力（NIAH/RULER 的代码版）

## 防污染（代码场景特有重点）

代码 benchmark 污染**极常见**（HumanEval 在 GitHub 上到处都是，容易进训练集）：

| 策略 | 说明 |
|------|------|
| **时间分窗** | 用 LiveCodeBench，只用模型训练截止后的新题 |
| **训练集剔除** | 从训练数据去 HumanEval/MBPP（含近似去重） |
| **私有评测集** | 企业内部真实代码任务，不公开 |
| **定期换题** | 公开 benchmark 会过时，定期更新 |

> 代码大模型"HumanEval 90分"几乎无意义（太容易污染）。**LiveCodeBench + 私有集**才有参考价值。

## 评测方式

- **执行式**（pass@k）：跑测试用例，通过率。客观、可重复。
- **pass@1** 最常用（单次生成通过率），pass@k（k 次采样至少 1 次通过）衡量上限
- **多语言**：不只测 Python，按目标用户技术栈测
- **代码 Agent**：端到端任务（如 SWE-bench），不只看代码对不对，看能否自主完成多步任务

## 代码场景的评测维度组合

| 维度 | 用什么 |
|------|--------|
| 基础生成 | LiveCodeBench pass@1 |
| 多语言 | MultiPL-E |
| 补全（IDE） | FIM 评测 + 延迟 |
| Agent（差异化） | SWE-bench |
| 企业私域 | 私有代码评测集 |

## 与其他角色衔接

- @evaluation 主导代码评测基准构建
- @ml-trainer 交付模型 → 过 @evaluation 的代码评测闸门
- @ml-serving 补全延迟单独测（IDE 体验关键）
- 企业私有评测集由 @data-strategy + 企业授权代码构建

## 参考来源

- HumanEval / HumanEval+ / MBPP / LiveCodeBench / BigCodeBench / MultiPL-E / SWE-bench 原论文
- 各代码大模型技术报告的评测章节
- benchmark 持续迭代，防污染策略以最新实践为准
