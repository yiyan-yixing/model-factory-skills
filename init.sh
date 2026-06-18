#!/bin/bash
# 模型工厂初始化脚本
# 安装框架后，一键初始化你的模型公司信息
# 用法: bash .claude/init.sh
# 非交互模式: COMPANY_NAME="XX" MODEL_DIRECTION="XX" bash .claude/init.sh

set -e

# ─── 配置项（支持环境变量预填，交互模式可修改） ───

: "${COMPANY_NAME:=}"
: "${MODEL_DIRECTION:=}"
: "${TARGET_USER:=}"
: "${HYPOTHESIS:=}"
: "${ADVANTAGE:=}"
: "${PRODUCT_POSITIONING:=}"
: "${TRAINING_FRAMEWORK:=}"
: "${COMPUTE:=}"
: "${INFERENCE_ENGINE:=}"
: "${DEPLOY:=}"

echo ""
echo "🏭 模型工厂 · 初始化"
echo "===================="
echo ""
echo "以下信息将写入 Agent 记忆系统，所有角色都会读取。"
echo "按回车跳过则使用默认模板值。"
echo ""

# ─── 交互式收集 ───

if [ -z "$COMPANY_NAME" ]; then
  read -rp "📌 公司名称: " COMPANY_NAME
fi
if [ -z "$MODEL_DIRECTION" ]; then
  read -rp "🧭 模型方向 (如: 垂直法律大模型 / 代码模型 / 智能客服): " MODEL_DIRECTION
fi
if [ -z "$TARGET_USER" ]; then
  read -rp "👤 目标用户 (如: 中小企业法务 / 开发者): " TARGET_USER
fi
if [ -z "$HYPOTHESIS" ]; then
  read -rp "💡 核心假设 (如: 市场需要垂直法律合同分析能力，有人愿付费调用): " HYPOTHESIS
fi
if [ -z "$ADVANTAGE" ]; then
  read -rp "⚔️  差异化壁垒 (如: 垂直数据壁垒 + 工程效率): " ADVANTAGE
fi
if [ -z "$PRODUCT_POSITIONING" ]; then
  read -rp "🎯 产品定位 (一句话): " PRODUCT_POSITIONING
fi

echo ""
echo "⚡ 技术栈偏好 (回车跳过 = 创业期选型原则)"
if [ -z "$TRAINING_FRAMEWORK" ]; then
  read -rp "   训练框架 (如: PyTorch+DeepSpeed): " TRAINING_FRAMEWORK
fi
if [ -z "$COMPUTE" ]; then
  read -rp "   算力 (如: 云 GPU A100 按需): " COMPUTE
fi
if [ -z "$INFERENCE_ENGINE" ]; then
  read -rp "   推理引擎 (如: vLLM): " INFERENCE_ENGINE
fi
if [ -z "$DEPLOY" ]; then
  read -rp "   部署平台 (如: Docker+云托管): " DEPLOY
fi

# ─── 默认值处理 ───

COMPANY_NAME="${COMPANY_NAME:-我的模型公司}"
MODEL_DIRECTION="${MODEL_DIRECTION:-垂直大模型能力}"
TARGET_USER="${TARGET_USER:-待定（需通过可调用能力验证）}"
HYPOTHESIS="${HYPOTHESIS:-市场需要 ${MODEL_DIRECTION} 能力，有人愿意为调用付费}"
ADVANTAGE="${ADVANTAGE:-垂直数据壁垒 + 工程效率}"
PRODUCT_POSITIONING="${PRODUCT_POSITIONING:-在 ${MODEL_DIRECTION} 场景做出可调用、可付费的模型能力}"

# ─── 写入记忆系统 ───

CLAUDE_DIR=".claude"

echo ""
echo "📝 [1/4] 写入项目上下文..."

cat > "${CLAUDE_DIR}/memory/core/project-context.md" << EOF
# 项目上下文

> 此文件由所有 Agent 共享。描述公司/产品的基本信息，每个 Agent 都应该知道。

## 公司

- **名称**：${COMPANY_NAME}
- **阶段**：0→1 创立期
- **模式**：大模型公司（用最少人数跑通 数据→模型→服务→商业 闭环）
- **方向**：${MODEL_DIRECTION}

## 产品

- **定位**：${PRODUCT_POSITIONING}
- **目标用户**：${TARGET_USER}
- **核心假设**：${HYPOTHESIS}
- **差异化**：${ADVANTAGE}

## 季度 OKR

- **O**：用可调用的模型能力赢得信任，获得第一批付费调用方
- **KR1**：构建垂直训练数据集，质量达标（W4）
- **KR2**：模型在垂直评测基准达标，可调用（W8）
- **KR3**：API 上线，日调用达标（W10）
- **KR4**：付费调用方 3 个（W12）

## 明确不做

- ❌ 通用大模型对标 GPT（打不过大厂）
- ❌ 自建超大规模 GPU 集群（烧不起）
- ❌ 堆人力标注（强自动化优先）
- ❌ AI 套壳（必须有数据/模型壁垒）

## 当前瓶颈

- 验证 Problem-Solution Fit
- 数据从哪来（垂直数据壁垒是核心）
- 算力成本可控

## 团队角色（标准配置 15 人）

| 团队 | 角色 | 调用 | 核心使命 |
|------|------|------|----------|
| 管理层 | CEO/Founder | @ceo | 方向、算力决策、商业闭环 |
| 产品 | Product Owner | @po | 做用户真正需要的模型能力 |
| 产品 | AI 产品经理 | @ai-pm | Prompt/Agent 设计、体验优化 |
| 数据 | 数据工程师 | @data-engineer | 采集、清洗、数据版本 |
| 数据 | 数据策略 | @data-strategy | 数据来源、标准、评估指标 |
| 模型 | ML·训练 | @ml-trainer | 预训练、实验、Scaling |
| 模型 | ML·对齐 | @ml-alignment | SFT/RLHF、安全对齐 |
| 模型 | ML·推理 | @ml-serving | 推理优化、量化、部署 |
| 模型 | Evaluation | @evaluation | 评测、AB、回滚、报告 |
| 平台 | Backend/平台 | @backend | API、鉴权、数据库、日志 |
| 平台 | Infra/DevOps | @infra | 部署、CI/CD、监控、容器 |
| 平台 | MLOps | @mlops | 端到端流水线、实验追踪 |
| 商业 | Growth | @growth | 增长、用户反馈、转化 |
| 商业 | DevRel | @devrel | 文档、SDK、社区、生态 |
| 商业 | 运营 | @ops | 内容、用户运营 |
EOF
echo "   ✅ project-context.md"

# ─── 写入技术栈 ───

echo "⚙️  [2/4] 写入技术栈..."

TECH_ROWS=""
if [ -n "$TRAINING_FRAMEWORK" ]; then
  TECH_ROWS="${TECH_ROWS}
| 训练框架 | ${TRAINING_FRAMEWORK} | — | 开源优先、可复现 | — |"
fi
if [ -n "$COMPUTE" ]; then
  TECH_ROWS="${TECH_ROWS}
| 算力 | ${COMPUTE} | — | 成本可控、按需 | — |"
fi
if [ -n "$INFERENCE_ENGINE" ]; then
  TECH_ROWS="${TECH_ROWS}
| 推理引擎 | ${INFERENCE_ENGINE} | — | 高吞吐、可量化 | — |"
fi
if [ -n "$DEPLOY" ]; then
  TECH_ROWS="${TECH_ROWS}
| 部署 | ${DEPLOY} | — | 一键部署 ≤ 15min | — |"
fi

if [ -z "$TECH_ROWS" ]; then
  TECH_ROWS="
| 待定 | — | — | 创业初期，尚未选型 | — |"
fi

cat > "${CLAUDE_DIR}/memory/core/tech-stack.md" << EOF
# 技术栈

> 此文件由所有 Agent 共享。每次技术选型变更时更新。

## 当前技术栈

| 层级 | 技术 | 版本 | 选型理由 | 选型日期 |
|------|------|------|----------|----------|${TECH_ROWS}

## 选型原则

- **开源优先**：能用开源框架/基座就不从零造
- **算力成本可控**：推理成本 ≤ 商业定价 40%
- **托管优先**：能用云托管/Serverless 就不自建集群
- **速度优先**：数据→模型→上线 < 1 周
- **可复现**：数据版本 + 超参 + 种子全记录

## 选型决策记录

| 编号 | 决策 | 理由 | 日期 | 当前状态 |
|------|------|------|------|----------|
| — | — | — | — | — |
EOF
echo "   ✅ tech-stack.md"

# ─── 重置架构 ───

echo "🏗️  [3/4] 重置架构决策..."

cat > "${CLAUDE_DIR}/memory/core/architecture.md" << EOF
# 架构决策记录

> 此文件由所有 Agent 共享。每次重大架构/技术选型决策时更新。

## 当前架构

- **阶段**：0→1 创业期
- **模式**：待定（自训基座 / 开源基座微调 / 调用 API）
- **核心约束**：15 人团队，算力成本可控，跑通 数据→模型→服务→商业 闭环

## 模型工厂四层架构

\`\`\`
数据层 ──→ 模型层 ──→ 服务层 ──→ 商业层
采集/清洗    预训练/对齐   API/推理     增长/计费
\`\`\`

## ADR（Architecture Decision Records）

格式：ADR-<编号> | <标题> | <状态>

### ADR 模板

\`\`\`
## ADR-<N>: <标题>

### 状态
提议 / 已采纳 / 已废弃 / 已替代

### 背景
为什么要做这个决策？

### 决策
我们选择了什么？

### 理由
为什么这么选？考虑了哪些替代方案？

### 后果
这个决策带来的好处和代价？
\`\`\`

### 已记录的 ADR

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| — | — | — | — |
EOF
echo "   ✅ architecture.md"

# ─── 重置白板 ───

echo "📋 [4/4] 重置共享白板..."

cat > "${CLAUDE_DIR}/blackboard/current-sprint.md" << 'EOF'
# 当前迭代

> 协调者 Agent 维护此文件。所有 Agent 可读取当前迭代状态。

## 迭代信息

| 项目 | 值 |
|------|----|
| 迭代号 | Sprint-0 |
| 起止日期 | — |
| 季度 OKR | O: 用可调用的模型能力赢得信任，获得第一批付费调用方 |

## 本期目标

```
本期目标：[每期开始由 @po 填写，对齐 OKR]
成功标准：[可评测的模型能力达标指标]
算力预算：[本期可用 GPU 时]
```

## 任务分配

| 任务 | 负责角色 | 状态 | 交付物 |
|------|----------|------|--------|
| — | — | — | — |

## 进度

| 日期 | 更新内容 | 更新者 |
|------|----------|--------|
| — | 初始化 | @ceo |
EOF

cat > "${CLAUDE_DIR}/blackboard/open-questions.md" << 'EOF'
# 待解决问题

> 任何 Agent 都可以写入新问题，协调者负责分配和推进。

## 问题格式

```
Q<编号> | <提出者> | <日期> | <问题描述> | <严重度：阻断/重要/一般> | <状态：待处理/进行中/已解决>
```

## 问题列表

| 编号 | 提出者 | 日期 | 问题 | 严重度 | 状态 |
|------|--------|------|------|--------|------|

> 新问题追加到表末尾，不要删除已解决问题——它们是决策历史的一部分。
EOF

cat > "${CLAUDE_DIR}/blackboard/challenges.md" << 'EOF'
# 质疑记录

> 按 challenge-protocol.md 执行的质疑记录。协调者维护。

## 格式

```
C<编号> | <质疑者> | <被质疑者> | <日期> | <质疑内容> | <严重度> | <结果：通过/修改/打回>
```

## 记录

| 编号 | 质疑者 | 被质疑者 | 日期 | 质疑内容 | 严重度 | 结果 |
|------|--------|----------|------|----------|--------|------|
EOF

cat > "${CLAUDE_DIR}/blackboard/decisions-log.md" << 'EOF'
# 决策日志

> 记录每个重大决策，便于追溯。

## 格式

```
D<编号> | <决策者> | <日期> | <决策内容> | <依据> | <影响范围>
```

## 决策记录

| 编号 | 决策者 | 日期 | 决策 | 依据 | 影响范围 |
|------|--------|------|------|------|----------|
EOF

echo "   ✅ current-sprint.md / open-questions.md / challenges.md / decisions-log.md"

# ─── 清空归档 ───

echo ""
echo "📦 清空归档记忆（保留模板结构）..."

cat > "${CLAUDE_DIR}/memory/archival/decisions/decisions.md" << 'EOF'
# 决策归档

> 已完成或已废弃的决策存档于此。

## 归档记录

| 编号 | 标题 | 原状态 | 归档原因 | 归档日期 |
|------|------|--------|----------|----------|
EOF

cat > "${CLAUDE_DIR}/memory/archival/lessons/lessons.md" << 'EOF'
# 经验教训

> 每次迭代复盘后的经验教训存档于此。格式：L<编号> | <教训> | <场景> | <如何避免/复用>

## 教训记录

| 编号 | 教训 | 场景 | 如何避免/复用 |
|------|------|------|---------------|
EOF

cat > "${CLAUDE_DIR}/memory/archival/user-research/research.md" << 'EOF'
# 用户调研归档

> 调用方访谈、问卷、调用日志等调研数据存档于此。

## 调研记录

| 编号 | 方法 | 日期 | 样本数 | 关键发现 | 行动 |
|------|------|------|--------|----------|------|
EOF

echo "   ✅ archival/decisions / lessons / user-research"

# ─── 完成 ───

echo ""
echo "🎉 初始化完成！"
echo ""
echo "你的模型公司信息："
echo "  📌 公司: ${COMPANY_NAME}"
echo "  🧭 方向: ${MODEL_DIRECTION}"
echo "  🎯 定位: ${PRODUCT_POSITIONING}"
echo "  👤 用户: ${TARGET_USER}"
echo ""
echo "下一步："
echo "  1. 启动 Claude Code"
echo "  2. 输入 @ceo 定垂直场景和模型路线"
echo "  3. 输入 @po 定义第一个模型能力需求"
echo "  4. 输入 @data-strategy 规划数据来源"
echo ""
echo "随时可以修改 .claude/memory/core/ 下的文件更新公司信息。"
