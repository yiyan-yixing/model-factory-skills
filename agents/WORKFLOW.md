# 模型工厂 Agent 协作流程

> 15 个角色，1 条「数据 → 模型 → 服务 → 商业」闭环 DAG，用最少人数跑通模型能力变现。
> 支持：条件分支、质疑协议、共享记忆、DAG 编排。

---

## 核心闭环 DAG

不是线性流水线，而是支持条件分支的有向无环图。四个环节逐级推进，评测是关键闸门：

```
@po 定义模型产品需求
  ├── @ai-pm 设计 Prompt / Agent 交互
  ├── @data-strategy 制定数据标准与评估指标 ← 条件：涉及新模型能力
  │
  └── @data-engineer 采集清洗数据
        └── @ml-trainer 预训练 / 持续训练
              ├── @ml-alignment 微调对齐（SFT / RLHF）
              │
              └── @evaluation 评测（自动基准 + 人工抽检）
                    ├── @ml-serving 推理优化部署 ← 条件：评测达标
                    └── @ml-trainer 继续训练 ← 条件：评测不达标（回流数据，加训）
                          │
                          └── @backend 封装为 API 服务
                                └── @mlops 流水线自动化（数据→训练→评测→上线）
                                      └── @infra CI/CD 部署 + 监控
                                            │
                                            └── @growth 推用户 + @devrel 开发者接入
                                                  └── @evaluation AB 测试 + 灰度回滚
                                                        └── @po 决策迭代
                                                              ├── 继续 → 下一迭代
                                                              ├── 调整 → 改进后下一迭代
                                                              └── 砍掉 → @ceo 切方向 → 回到 @po 重新定义
```

### 质疑节点（按 challenge-protocol.md）

```
@po 出 PRD ──→ @data-strategy 质疑数据可得性 ──→ 通过/修改/打回
            ──→ @evaluation 质疑评估指标可量化 ──→ 通过/修改/打回

@data-strategy 出数据标准 ──→ @ml-trainer 质疑数据量/质量够不够训练 ──→ 通过/修改/打回

@ml-trainer 出模型 ──→ @evaluation 质疑评测是否充分 ──→ 通过/修改/打回
                   ──→ @ml-serving 质疑推理可行性/成本 ──→ 通过/修改/打回

@ceo 做重大决策（选基座/算力投入）──→ @evaluation 质疑数据与评测支撑 ──→ 通过/修改/打回
```

---

## 角色职责速查

| 角色 | 调用 | 做什么 | 不做什么 |
|------|------|--------|----------|
| **CEO** | `@ceo` | 定方向、选基座、算力投入、融资 | 不陷入训练调参细节 |
| **PO** | `@po` | 定模型能力、排优先级、写 PRD | 不自己当标注员/用户 |
| **AI PM** | `@ai-pm` | Prompt/Agent 设计、体验优化 | 不追求完美 prompt 拖慢上线 |
| **数据工程师** | `@data-engineer` | 采集、清洗、ETL、数据版本 | 不拍脑袋定数据标准 |
| **数据策略** | `@data-strategy` | 定数据来源、标注规范、评估指标 | 不堆数据不清洗就喂模型 |
| **ML·训练** | `@ml-trainer` | 预训练、实验、Scaling | 不跳过评测直接上 |
| **ML·对齐** | `@ml-alignment` | SFT/RLHF、安全对齐 | 不为指标牺牲安全 |
| **ML·推理** | `@ml-serving` | 推理优化、量化、部署 | 不为压延迟砍精度无依据 |
| **Evaluation** | `@evaluation` | 自动评测、AB、回滚、报告 | 不证明模型没问题，只证明问题在哪 |
| **Backend** | `@backend` | API、鉴权、数据库、日志 | 不自建不需要的基础设施 |
| **Infra** | `@infra` | CI/CD、部署、监控、容器 | 不手动重复部署 |
| **MLOps** | `@mlops` | 端到端流水线、实验追踪 | 不让人工搬运数据/模型 |
| **Growth** | `@growth` | 增长、用户反馈、转化 | 不刷量不追虚荣指标 |
| **DevRel** | `@devrel` | 文档、SDK、社区、生态 | 不写没人看的文档 |
| **运营** | `@ops` | 内容、用户运营 | 不追热点偏离定位 |

---

## 快速出模型能力流程（1 周）

> 大模型公司铁律：没有可调用的模型能力，就没有对话。

```
Day 1-2: @po 定场景 + @data-strategy 定数据来源 + 确认可行性
         输入：市场假设 + 算力预算
         输出：1 页 PRD + 数据策略 + 技术方案（自训/微调/基座）

Day 3-4: @ml-trainer 训练/微调 + @ml-alignment 对齐 + @evaluation 跑评测
         输入：数据集 + 技术方案 + 评测基准
         输出：达标模型版本 + 评测报告（通过质疑闸门）

Day 5:   @ml-serving 推理优化 + @backend 封 API + @infra 部署
         输入：达标模型
         输出：可调用 API + Playground + 健康检查

Day 6-7: @devrel 出文档/示例 + @growth 推 10 个种子用户 + @data-engineer 开始采集日志
         输入：可调用 API
         输出：接入文档 + 10 份反馈 + 调用量/效果数据
```

### 交接标准

| 交接 | 从 → 到 | 交接物 | 验收条件 |
|------|---------|--------|----------|
| PO → Data-Strategy | 需求 → 数据标准 | PRD + 模型能力定义 | 数据策略确认数据可获取 |
| Data-Strategy → Data-Engineer | 标准 → 数据 | 数据规范 + 来源清单 | 数据工程师确认能采到 |
| Data-Engineer → ML-Trainer | 数据 → 训练 | 清洗后数据集 + 版本 | 数据通过质量校验 |
| ML-Trainer → ML-Alignment | 基座 → 对齐 | 预训练/基座模型 + 日志 | 模型能跑通基础能力 |
| ML-Alignment → Evaluation | 模型 → 评测 | 微调后模型 + 变更说明 | 评测给出 Go/No-Go |
| Evaluation → ML-Serving | 评测通过 → 上线 | Go 判定 + 评测报告 | 评测说 Go 才能推理优化上线 |
| Evaluation → ML-Trainer | 评测不达标 → 重训 | No-Go + 缺陷分析 | 标注哪些能力不达标，回流数据 |
| ML-Serving → Backend | 推理就绪 → API | 推理服务 + benchmark | API 能稳定调用 |
| Backend → MLOps | 服务 → 流水线 | API + 部署配置 | MLOps 确认可自动化 |
| MLOps → Infra | 流水线 → 部署 | CI/CD 配置 + 监控 | Infra 确认部署通道畅通 |
| Infra → Growth | 上线 → 推广 | 在线 URL + 监控 | 服务可用率达标 |
| Growth → Evaluation | 用户来了 → 效果 | 调用量 + 用户反馈 | AB 实验数据开始流入 |
| Evaluation → PO | 效果 → 决策 | 模型效果报告 | 报告有"所以呢"结论 |
| Evaluation → CEO | 效果 → 校准 | 关键指标红/黄/绿 | CEO 根据数据做战略判断 |

---

## 两周一迭代节奏

```
周一（20min）         周三（10min）         周五（30min）
┌──────────┐        ┌──────────┐        ┌──────────────┐
│ 规划本期  │──────→│ 中期检查  │──────→│ 评测+复盘    │
│ @po 主导  │       │ @po 主导  │       │@eval+@po 主导│
│ @data-str│       │ @ml 反馈  │       │ @ceo 校准    │
│ @ml 可行  │       │          │       │              │
└──────────┘        └──────────┘        └──────────────┘
```

### 周一规划

- @po 从 OKR 提取本期模型能力目标
- @data-strategy 确认数据就绪
- @ml-trainer + @ml-alignment 确认训练可行性 + 算力预算
- @mlops 确认流水线通道畅通
- @evaluation 确认评测基准就绪
- 质疑：@data-strategy 对 PRD 做数据可得性评审

### 周三检查

- @po 检查训练/评测进度
- @ml-* 反馈训练障碍（数据不够/算力不足/效果卡住）
- 偏航 → 当天调整，不等到周五

### 周五复盘

- @evaluation 出模型效果报告（评测分数 + AB 数据）
- @po 判断模型能力假设是否成立
- @ml-* 评估技术债
- @ceo 做战略校准（如需要）
- 定下期方向
- 写入 `.claude/blackboard/current-sprint.md`

---

## 角色协作矩阵

| | PO | Data-Str | Data-Eng | ML-Train | ML-Align | Eval | ML-Serve | Backend | MLOps | Infra | Growth | DevRel | Ops | CEO |
|--|----|----------|----------|----------|----------|------|----------|---------|-------|-------|--------|--------|-----|-----|
| **PO** | — | 给PRD | — | 给能力定义 | — | 给评估标准 | — | — | — | — | 给推广目标 | 给用户画像 | — | 汇报进度 |
| **Data-Str** | 给数据结论 | — | 给规范 | 给数据质量 | — | — | — | — | — | — | — | — | — | — |
| **Data-Eng** | — | 执行采集 | — | 给数据集 | — | — | — | — | — | — | — | — | — | — |
| **ML-Train** | 确认可行 | — | 要数据 | — | 给基座模型 | — | — | — | — | — | — | — | — | — |
| **ML-Align** | — | — | — | 拿基座 | — | — | — | — | — | — | — | — | — | — |
| **Eval** | 给评测结论 | — | — | 给No-Go | 给No-Go | — | 给Go判定 | — | — | — | — | — | — | 给指标报告 |
| **ML-Serve** | — | — | — | — | 拿模型 | — | — | 给推理服务 | — | — | — | — | — | — |
| **Backend** | — | — | — | — | — | — | 拿推理 | — | — | — | — | — | — | — |
| **MLOps** | — | — | — | — | — | — | — | 拿API | — | — | — | — | — | — |
| **Infra** | — | — | — | — | — | — | — | 部署服务 | — | — | 给在线URL | — | — | 给成本 |
| **Growth** | 给用户反馈 | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **DevRel** | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **Ops** | 给内容反馈 | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **CEO** | 给方向 | — | — | 给算力预算 | — | 给决策 | — | — | — | — | — | — | — | — |

---

## 记忆读写规则

| Agent | 可写 | 可读 |
|-------|------|------|
| @ceo | blackboard/decisions-log.md, blackboard/open-questions.md | 所有 |
| @po | blackboard/current-sprint.md | 所有 |
| @data-strategy | memory/core/project-context.md（数据部分）, blackboard/ | 所有 |
| @data-engineer | — | memory/core/, archival/ |
| @ml-trainer | memory/core/architecture.md（训练部分） | memory/core/, archival/ |
| @ml-alignment | — | memory/core/ |
| @ml-serving | memory/core/architecture.md（推理部分） | memory/core/ |
| @evaluation | blackboard/challenges.md, blackboard/current-sprint.md（评测部分） | 所有 |
| @backend | memory/core/architecture.md（服务部分） | memory/core/ |
| @infra | memory/core/tech-stack.md（部署部分） | memory/core/ |
| @mlops | memory/core/architecture.md（流水线部分） | memory/core/ |
| @growth | blackboard/current-sprint.md（增长部分） | memory/core/, archival/user-research/ |
| @devrel | — | memory/core/ |
| @ops | — | memory/core/ |
| @architect(若复用) | memory/core/architecture.md, memory/core/tech-stack.md, archival/decisions/ | 所有 |

---

## 紧急流程

### 线上模型事故（输出有害/能力回退/服务宕机）

```
@evaluation/监控 发现事故 → @ml-serving 立即灰度回滚上一版本 → @infra 确认回滚生效
                          → @ml-alignment + @ml-trainer 定位根因（数据污染/对齐退化）
全程 < 1 小时止血，根因修复进下个迭代
```

### 模型能力不达标

```
@evaluation 报告评测 No-Go → @data-strategy 补数据 → @ml-trainer 加训/换方案
                            → @po 判断是数据问题还是方向问题 → 若方向错 → @ceo 切方向
不靠"再调调 prompt"硬撑，数据不够就补数据
```

### 能力机会窗口（外部出现新基座/新范式）

```
外部出现更强基座 → @ceo 判断是否值得切 → @ml-trainer 评估迁移成本 → @evaluation 评估效果增益
                → 如果 1 周能切换并出可用能力 → 立刻启动快速出模型能力流程
```
