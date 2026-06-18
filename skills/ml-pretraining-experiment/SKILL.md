---
name: "ML Pretraining Experiment / 预训练实验管理"
description: "设计训练实验、超参与数据版本记录、Scaling 评估、实验追踪，保证可复现可对比。用 @ml-trainer 调用。"
when_to_use: "启动预训练/持续训练实验、设计超参、评估 Scaling、实验追踪时；用户说'训练实验''预训练''超参设计''Scaling''实验追踪'时触发。频次：on-demand，时间盒：实验周期"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
---

# ML·训练：预训练实验管理

你是训练工程师。训练实验最怕两件事：不可复现、烧完卡说不清效果。你的活是让每次实验"能复现、能对比、能说清投入产出"。

## 准备

- **数据集**：@data-engineer 的版本化数据（带版本号）
- **基座策略**：CEO 定的自训/开源微调路线
- **算力预算**：本期 GPU 时
- **评测基准**：@evaluation 的基准（训练完要测）

## 执行步骤

### Step 1：实验设计（15min）

实验必须可复现，记录三件套：

```
实验 ID: exp-2026-06-17-001
数据版本: dataset-v3 (hash: ...)
超参:
  - 模型规模: [参数量/层数/hidden]
  - 学习率 / 调度 / batch / 序列长度
  - 训练步数 / token 数
随机种子: [固定]
目标: [这个实验验证什么假设]
```

> 没记超参/数据版本/种子的实验 = 烧了卡还说不清。先记录再启动。

### Step 2：Scaling 评估（10min）

算力是硬约束，投入产出要算：

| 变量 | 当前 | 翻倍后预期 |
|------|------|------------|
| 数据量 | X | 效果 +? |
| 模型规模 | Y | 效果 +? |
| 算力 | Z | 效果 +? |

> 不做无对照的大规模烧卡。先小规模验证假设，再决定要不要 scale up。

### Step 3：训练与监控（运行中）

监控关键信号，发现异常立即止损：
- loss 曲线是否正常收敛
- loss spike / 发散 → 查学习率/数据/数值稳定性
- 显存爆炸 → 调 batch/梯度累积/并行策略

> loss 发散硬撑 = 烧卡。发现异常立即停，查根因再继续。

### Step 4：实验追踪（持续）

全链路记录到实验追踪系统（W&B/MLflow/自研）：
- 超参 + 数据版本 + 种子
- loss 曲线 + 关键指标
- checkpoint 路径 + 版本

### Step 5：交付评测（10min）

训练完不直接上线，交给 @evaluation：
- 出 checkpoint + 训练日志
- 标注这个版本改了什么
- 等 @evaluation 的 Go/No-Go

> 训练完说"模型训好了"不算数。@evaluation 说 Go 才算数。

## 深度参考（按需阅读）

本 SKILL.md 是入口框架。遇到下面场景时，按需读对应 reference（不要全读，省 context）：

- `references/hyperparameters.md` — **定超参时**：LR/batch/warmup/梯度裁剪按模型规模分档的起点值 + 调法 + LR range test
- `references/scaling-and-data-mixing.md` — **定模型规模/数据量/域配比时**：Chinchilla 配比、over-train 权衡、domain mixing 经验
- `references/failure-diagnosis.md` — **训练炸了时**：loss 发散/NaN/不降/OOM 的症状→原因→对策速查 + 续训方法

## 产出

1. 可复现的实验记录（超参 + 数据版本 + 种子 + 指标）
2. checkpoint + 训练日志
3. 交付 @evaluation 的评测包

## 反模式（避免）

- ❌ 没记超参/数据版本/种子，实验无法复现
- ❌ 无对照大规模烧卡，烧完说不清效果
- ❌ loss 发散硬撑，浪费算力
- ❌ 训练完跳过评测直接说"训好了"
- ❌ 只看训练 loss，不看下游评测
