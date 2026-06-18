# model-factory-skills

> Claude Code 技能集合 — 大模型公司 15 角色 Agent + 16 个核心技能 + 三层记忆 + 协作白板 + 质疑协议。
> 专为「用最少人数跑通 **数据 → 模型 → 服务 → 商业** 闭环」的 AI 公司打造。标准 `.claude/` 格式。

## 30 秒上手

```bash
# 1. 创建新项目
mkdir my-model-company && cd my-model-company

# 2. 一键安装 + 自动初始化（回答几个问题，模型工厂就是你的了）
bash /workspace/model-factory-skills/install.sh

# 3. 启动 Claude Code，你的大模型公司已就绪
claude
@ceo 帮我定垂直场景和模型路线
@data-strategy 我们的数据从哪来
```

> 🎯 安装完成后，你将拥有：15 个 Agent 角色、16 个技能、三层记忆系统、共享白板、质疑协议 — 一家完整的大模型公司框架。

### 用户旅程

```
┌──────────────────────────────────────────────────────────────────┐
│  mkdir my-model-co && cd my-model-co                             │
│                                                                  │
│  ┌───────────┐    ┌──────────────┐    ┌────────────────────────┐ │
│  │  安装框架  │──→│  初始化公司   │──→│     开工！             │ │
│  │ install.sh│    │  init.sh     │    │  @po 定模型产品需求    │ │
│  │           │    │              │    │  @data-strategy 定数据 │ │
│  │ 拿到空壳  │    │  填入模型方向 │    │  @ml-trainer 训练      │ │
│  │ 15角色    │    │  目标用户     │    │  @evaluation 评测      │ │
│  │ 16技能    │    │  算力 技术栈  │    │  @backend 出 API       │ │
│  │ 记忆系统  │    │              │    │  @growth 变现          │ │
│  └───────────┘    └──────────────┘    └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 核心闭环

模型工厂只做一件事：把数据变成能赚钱的模型能力。

```
数据 ──→ 模型 ──→ 服务 ──→ 商业
 │         │        │         │
 ▲         ▲        ▲         ▲
@data    @ml      @backend   @growth
@eval    @mlops   @infra     @devrel
```

- **数据**：@data-strategy 定标准 → @data-engineer 采集清洗
- **模型**：@ml-trainer 训练 → @ml-alignment 对齐 → @evaluation 评测 → @ml-serving 推理优化
- **服务**：@backend 封装 API → @mlops 流水线 → @infra 部署监控
- **商业**：@growth 推用户 → @devrel 开发者接入 → @evaluation AB 回滚 → @po 决策迭代

---

## 仓库目录结构（源码）

```
model-factory-skills/              # 仓库根目录
├── skills/                        #   16 个技能（标准 SKILL.md 格式）
│   ├── ceo-model-strategy/        #     CEO 模型战略决策
│   ├── data-pipeline-build/       #     数据采集清洗流水线
│   ├── ml-pretraining-experiment/ #     预训练实验
│   ├── ml-alignment-rlhf/         #     SFT/RLHF 对齐
│   ├── eval-benchmark-build/      #     自动评测基准
│   ├── mlops-pipeline/            #     端到端模型流水线
│   └── ...                        #     共 16 个技能
│
├── agents/                        #   15 个角色子代理（通过 @角色名 调用）
│   ├── ceo.md                     #     CEO / Founder（兼 COO）
│   ├── po.md                      #     Product Owner
│   ├── data-strategy.md           #     数据策略
│   ├── ml-trainer.md              #     ML·训练
│   ├── evaluation.md              #     评测
│   ├── mlops.md                   #     MLOps
│   └── ...                        #     共 15 角色
│   ├── WORKFLOW.md                #     数据→模型→服务→商业 闭环 DAG
│   └── challenge-protocol.md      #     质疑协议
│
├── memory/                        #   三层记忆系统
│   ├── core/                      #     常驻记忆（每 session 加载）
│   ├── archival/                  #     长期记忆（按需读取）
│   └── recall/                    #     历史会话（按需检索）
│
├── blackboard/                    #   Agent 共享白板
├── evals/                         #   效果评估体系（占位）
├── profiles/                      #   垂直落地配置包（code-model-company 等）
├── CLAUDE.md.template             #   记忆入口模板
├── install.sh                     #   一键安装脚本
└── init.sh                        #   交互式初始化脚本
```

### 安装后的用户项目结构

```
your-project/
└── .claude/                    # Claude Code 自动发现
    ├── skills/                 #   16 个 Skills
    ├── agents/                 #   15 个 Agent + WORKFLOW + 质疑协议
    ├── memory/                 #   三层记忆系统
    ├── blackboard/             #   共享白板
    ├── evals/
    ├── CLAUDE.md               #   记忆入口 (@import core)
    └── init.sh                 #   初始化脚本
```

---

## 角色子代理（15 个 · 标准配置）

通过 `@角色名` 调用，每个角色拥有完整的职责、KPI、决策权限和可用技能。

```
                          ┌──────────────────────┐
                          │      CEO · 1         │
                          │  方向·融资·算力决策   │
                          └──────────┬───────────┘
           ┌──────────────┬──────────┼──────────┬──────────────┐
           ▼              ▼          ▼          ▼              ▼
      ┌─────────┐   ┌─────────┐ ┌─────────┐ ┌─────────┐  ┌─────────┐
      │ 产品 ×2  │   │ 数据 ×2 │ │ 模型 ×4 │ │ 平台 ×3 │  │ 商业 ×3 │
      │ @po     │   │@data-eng│ │@ml-train│ │@backend │  │@growth  │
      │ @ai-pm  │   │@data-str│ │@ml-align│ │@infra   │  │@devrel  │
      │         │   │         │ │@ml-serve│ │@mlops   │  │@ops     │
      │         │   │         │ │@eval    │ │         │  │         │
      └─────────┘   └─────────┘ └─────────┘ └─────────┘  └─────────┘
```

| 角色 | 调用 | 核心使命 | 可用技能 |
|------|------|----------|----------|
| **CEO/Founder** | `@ceo` | 方向、融资、算力资源决策，确保公司活下去 | 模型战略决策 |
| **Product Owner** | `@po` | 用户是谁、做什么模型能力、什么先上线 | 模型产品 PRD |
| **AI 产品经理** | `@ai-pm` | Prompt/Agent 设计、体验优化 | Prompt/Agent 设计 |
| **数据工程师** | `@data-engineer` | 采集、清洗、ETL、数据版本 | 数据流水线搭建 |
| **数据策略** | `@data-strategy` | 采什么、怎么标、怎么生、评估指标 | 数据标准与评估 |
| **ML·训练** | `@ml-trainer` | 预训练、训练实验、Scaling | 预训练实验 |
| **ML·对齐** | `@ml-alignment` | SFT/RLHF、对齐、安全 | SFT/RLHF 对齐 |
| **ML·推理** | `@ml-serving` | 推理优化、量化、部署 | 推理优化 |
| **Evaluation** | `@evaluation` | 自动评测、AB、回滚、模型报告 | 评测基准 + AB回滚 |
| **Backend/平台** | `@backend` | API、鉴权、数据库、日志 | 模型 API 设计 |
| **Infra/DevOps** | `@infra` | 部署、CI/CD、监控、容器 | 部署 CI/CD |
| **MLOps** | `@mlops` | 端到端模型流水线、实验追踪 | MLOps 流水线 |
| **Growth** | `@growth` | 增长、用户反馈、商业转化 | 增长实验 |
| **DevRel** | `@devrel` | 文档、SDK、社区、开发者生态 | 开发者文档/SDK |
| **运营** | `@ops` | 内容、用户运营 | 内容运营日历 |

> **COO**（组织架构里 CEO 可兼任）职责并入 @ceo，不单列 Agent。

### 闭环流程（详见 `agents/WORKFLOW.md`）

```
@po 定需求 → @data-strategy 定标准 → @data-engineer 采数据
  → @ml-trainer 训练 → @ml-alignment 对齐 → @evaluation 评测
    → @ml-serving 推理优化 → @backend 出 API → @mlops 流水线 → @infra 部署
      → @growth 推用户 + @devrel 接入 → @evaluation AB 回滚 → @po 决策迭代
                                                                    ↓
                          @ceo 战略校准 ← @evaluation 效果报告 ←─────┘
```

---

## 技能一览（16 个）

| 环节 | 技能 | 触发时机 | 时间盒 |
|------|------|----------|--------|
| **管理层** | `ceo-model-strategy` | 定方向/选基座/算力投入时 | 30min |
| **产品** | `model-product-prd` | 开发模型能力前 | 45min |
| | `prompt-agent-design` | 设计 Prompt/Agent 时 | 30min |
| **数据** | `data-pipeline-build` | 搭建数据采集时 | 60min |
| | `data-strategy-spec` | 定数据标准时 | 30min |
| **模型** | `ml-pretraining-experiment` | 启动训练实验时 | — |
| | `ml-alignment-rlhf` | 微调对齐阶段 | — |
| | `ml-inference-optimize` | 上线前推理优化 | 45min |
| | `eval-benchmark-build` | 构建评测基准时 | 60min |
| | `eval-ab-rollout` | 模型上线灰度时 | 30min |
| **服务** | `model-api-design` | 设计模型 API 时 | 45min |
| | `infra-cicd-deploy` | 部署模型服务时 | 60min |
| | `mlops-pipeline` | 搭建模型流水线时 | 90min |
| **商业** | `growth-experiment` | 做增长实验时 | 30min |
| | `devrel-docs-sdk` | 出开发者文档/SDK 时 | — |
| | `ops-content-calendar` | 规划内容运营时 | 30min |

---

## 快速出模型能力流程（1 周）

> 大模型公司铁律：没有可调用的模型能力，就没有对话。

```
Day 1-2: @po 定场景 + @data-strategy 定数据来源 + @architect(若复用基座) 确认可行性
         输出：模型能力 PRD + 数据策略 + 技术方案

Day 3-4: @ml-trainer 训练/微调 + @ml-alignment 对齐 + @evaluation 跑评测
         输出：达标模型版本 + 评测报告

Day 5:   @ml-serving 推理优化 + @backend 封 API + @infra 部署
         输出：可调用的 API + Playground

Day 6-7: @devrel 出文档/示例 + @growth 推 10 个种子用户 + @data 开始采集
         输出：接入文档 + 10 份反馈 + 调用量数据
```

---

## 使用方法

### 技能（skills/）

技能通过 Claude Code **自动触发** — 当对话匹配到技能的 `description` 或 `when_to_use` 时自动加载。也可直接提及技能名显式触发：

```
帮我搭一套数据采集流水线
设计一个评测基准
我们的模型怎么做推理优化
```

### 角色子代理（agents/）

通过 `@角色名` 调用，以该角色的视角、权限和 KPI 执行：

```
@ceo 我们要不要自训基座还是用开源
@po 这个模型能力该做成 API 还是 Playground
@data-strategy 训练数据从哪来，怎么标注
@ml-trainer 设计一个预训练实验方案
@evaluation 给这个模型版本出评测报告
@ml-serving 推理延迟太高怎么优化
@backend 设计模型推理 API
@mlops 把数据→训练→评测→上线串成流水线
@growth 设计一个增长实验
@devrel 出一份开发者接入文档
```

---

## 组织演化（自动化后）

```
初期：人执行      →  中期：人监督      →  成熟：AI执行 / 人决策
```

长期保持 **20 人以内核心组织**。本仓库的 15 角色 Agent，正是这条演化路径的起点——先用 Agent 把每个角色的 SOP 固化，再逐步把"人执行"变成"AI 执行、人决策"。

---

## 垂直落地 Profile

通用框架 + 垂直落地配置包。`profiles/` 下提供针对特定场景的具体化参考（场景上下文、数据策略、评测基准、路线图）：

- `profiles/code-model-company/` — **代码大模型公司**：代码数据策略（开源协议/凭证合规）、代码评测（LiveCodeBench/SWE-bench 防污染）、0→1 路线图

做法律/医疗/金融大模型可仿照此结构做自己的 profile。详见各 profile 的 README。

## 三层记忆系统

| 层级 | 路径 | 加载方式 | 内容 |
|------|------|----------|------|
| **Core（常驻）** | `.claude/memory/core/` | CLAUDE.md @import，每 session 自动加载 | 技术栈、架构决策、项目上下文 |
| **Archival（长期）** | `.claude/memory/archival/` | Agent 需要时用 Read 读取 | 决策归档、经验教训、用户调研 |
| **Recall（历史）** | `.claude/memory/recall/` | 会话摘要 | 历史对话、自动学习 |

## 共享白板

| 文件 | 用途 | 维护者 |
|------|------|--------|
| `.claude/blackboard/current-sprint.md` | 当前迭代目标、任务分配、进度 | @po |
| `.claude/blackboard/open-questions.md` | 待解决问题 | 任何 Agent |
| `.claude/blackboard/challenges.md` | 质疑记录 | 协调者 |
| `.claude/blackboard/decisions-log.md` | 决策日志索引 | @ceo |

## 质疑协议

- @po 出 PRD → @data-strategy 质疑「数据可得性」+ @evaluation 质疑「评估指标可量化」
- @ml-trainer 出模型 → @evaluation 质疑「评测是否充分」+ @ml-serving 质疑「推理可行性/成本」
- @ceo 做重大决策 → @evaluation 质疑「数据与评测支撑」

详见 `agents/challenge-protocol.md`。

---

## 设计原则

- **同构对齐**：与「一人公司」通用软件仓库完全同构，格式 100% 一致
- **闭环驱动**：数据→模型→服务→商业，每个环节都有角色负责，无缝交接
- **少层级**：15 人扁平组织，CEO 直管 5 个职能团队
- **强自动化**：MLOps 把数据→训练→评测→上线串成一条流水线，减少人工搬运
- **工程优先**：算力成本、推理延迟、迭代速度是硬约束，不是"感觉"
- **可量化**：每个角色的 KPI 都是具体数字（评测分数、延迟、调用量、成本）
- **防自欺**：质疑协议让 Agent 互相挑战；评测先行，不靠"我觉得模型不错"

## License

CC BY-SA 4.0 — 欢迎借鉴，请注明出处
