# 模型工厂 Agent 协作流程

> 15 个角色，1 条「数据 → 模型 → 服务 → 商业」闭环 DAG，用最少人数跑通模型能力变现。
> 支持：条件分支、质疑协议、共享记忆、DAG 编排、反馈闭环。
> **v2 更新：级联协议 + 反馈闭环协议——关键交接点自动走查，防止方向跑偏。**

---

## 核心闭环 DAG

不是线性流水线，而是支持条件分支的有向无环图。四个环节逐级推进，评测是关键闸门：

```
@ceo 定方向 + 选基座
  │
  └── @po 定义模型产品需求
        │
        ├── ⚡ CEO 走查 PRD ← 反馈闭环①（≤2轮）
        │     │
        │     ├── 通过 → @po 继续派发下游
        │     └── 打回 → @po 修改 PRD
        │           └── 2轮打回 → 上报 CEO
        │
        ├── @ai-pm 设计 Prompt / Agent 交互
        ├── @data-strategy 制定数据标准与评估指标 ← 条件：涉及新模型能力
        │
        └── @data-engineer 采集清洗数据
              └── @ml-trainer 预训练 / 持续训练
                    ├── @ml-alignment 微调对齐（SFT / RLHF）
                    │
                    └── @evaluation 评测（自动基准 + 人工抽检）← 反馈闭环②
                          ├── Go → @ml-serving 推理优化部署 ← 条件：评测达标
                          └── No-Go → @ml-trainer 继续训练（回流数据，加训，≤2轮）
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

---

## 级联协议（Cascade Protocol）

Agent 完成核心工作后，自动检测下游是否存在，自动派发下游 Agent。用户只需和入口角色（@ceo / @po）沟通，整条链自动走完。

### 级联路由表

| 当前 Agent | 完成条件 | 下游 Agent | 交接物 | 条件 |
|-----------|---------|-----------|--------|------|
| @ceo | 方向已定 | @po | 方向决策 + 基座策略 | 交付型任务 |
| @po | PRD+评测目标写入 blackboard | @ceo | PRD 路径 | 级联交付型，CEO 走查 PRD |
| @ceo | PRD 走查通过 | @po（继续级联） | 走查通过 | PO 继续派发下游 |
| @ceo | PRD 走查打回 | @po | 打回原因+修改要求 | 修改后重新走查（≤2轮） |
| @po | CEO 走查通过 | @data-strategy | PRD+评测目标 | 涉及新模型能力/新数据源 |
| @po | CEO 走查通过 | @ai-pm | PRD+评测目标 | 涉及 Prompt/Agent 交互 |
| @po | CEO 走查通过 | @ml-trainer | PRD+评测目标 | 微调/对齐类（不需新数据） |
| @data-strategy | 数据标准+指标写入 blackboard | @data-engineer | 数据规范+来源清单 | 数据策略确认 |
| @data-engineer | 清洗数据集写入 blackboard | @ml-trainer | 清洗后数据集+版本 | 数据通过质量校验 |
| @ml-trainer | 预训练/基座模型写入 blackboard | @ml-alignment | 模型+训练日志 | 模型能跑通基础能力 |
| @ml-alignment | 微调后模型写入 blackboard | @evaluation | 模型+变更说明 | 微调完成 |
| @evaluation | Go 判定 | @ml-serving | Go+评测报告 | 评测说 Go |
| @evaluation | No-Go | @ml-trainer | No-Go+缺陷分析 | 回流重训（≤2轮） |
| @ml-serving | 推理服务就绪 | @backend | 推理服务+benchmark | API 可稳定调用 |
| @backend | API 封装完成 | @mlops | API+部署配置 | MLOps 确认可自动化 |
| @mlops | 流水线自动化完成 | @infra | CI/CD 配置+监控 | Infra 确认通道畅通 |
| @infra | 部署完成 | @growth | 在线 URL+监控 | 服务可用率达标 |
| @growth | 用户数据开始流入 | @evaluation | 调用量+用户反馈 | AB 实验数据 |
| @evaluation | AB 效果报告完成 | @po | 效果报告 | 有"所以呢"结论 |

### 级联触发判断

| 任务意图 | 级联？ |
|---------|--------|
| 来自上游 Agent 的级联任务 | ✅ 级联 |
| 包含"走完流程""全流程""出模型能力""一键交付"意图 | ✅ 级联 |
| 单一动作（"训个模型""写个 API"） | ❌ 不级联 |
| 用户说"只做这一步" | ❌ 不级联 |

### 级联-闭环交互

```
交付型任务 → @ceo → @po 出 PRD → CEO 走查 PRD ──→ 通过 → @data-strategy/@ai-pm/@ml-trainer
                                         │
                                         └── 打回 → @po 修改
                                               └── 2轮打回 → 上报 CEO

@ml-trainer → @ml-alignment → @evaluation ──→ Go → @ml-serving → @backend → @mlops → @infra → @growth → @evaluation(AB) → @po
                                           └── No-Go → @ml-trainer（≤2轮）
```

### 人工确认点

| 节点 | 触发条件 | 谁确认 | 为什么 |
|------|---------|--------|--------|
| CEO PRD 走查 | PO 出 PRD 后 | @ceo | 方向错 = 全白干 |
| 评测 No-Go 第 3 轮 | ML 连续 3 轮不达标 | 用户 | 需判断是数据/方案/方向问题 |
| 风控红线 | 涉及安全/合规 | 用户 | 模型安全不可自动放行 |

---

## 反馈闭环协议（Feedback Loop Protocol）

在级联的关键交接点加入双向反馈循环，防止方向跑偏和需求漂移。走查（walkthrough）≠ 质疑（challenge），走查是快速确认"做得对不对"，质疑是深度拷问"做得好不好"。

### 核心规则

1. **走查门控** — PRD 必须经 CEO 走查通过，才能级联到下游
2. **最多 2 轮回退** — 超过 2 轮上报用户
3. **走查记录** — 每次走查写入 `blackboard/walkthrough-{timestamp}.md`
4. **走查不替代质疑** — 质疑协议照常运行，走查是额外的方向保险
5. **闭环优先级** — ① PRD 走查 > ② 评测闸门

### 两条闭环

| 闭环 | 触发 | 走查者 | 被走查者 | 走查内容 | 最大轮数 |
|------|------|--------|----------|----------|----------|
| ① PRD 走查 | PO 出 PRD | @ceo | @po | 方向对不对？基座选对没？评测标准可量化？ | 2 |
| ② 评测闸门 | ML 出模型 | @evaluation | @ml-trainer/@ml-alignment | Go/No-Go（已有） | 2（已有） |

### 走查记录格式

```markdown
# 走查记录 walkthrough-{timestamp}
走查类型：PRD 走查 / 评测闸门
走查者：[角色名]
被走查者：[角色名]
轮次：[1/2]

## 走查结论
通过 / 打回

## 走查要点
1. [要点1]：✅/❌ [说明]
2. [要点2]：✅/❌ [说明]
...

## 修改要求（打回时填写）
- [具体修改要求1]
- [具体修改要求2]
```

### PRD 走查要点（CEO 走查 PO）

1. **方向一致性** — PRD 是否符合公司战略方向和当前 OKR？
2. **基座选型** — 选自训/微调/基座是否合理？算力预算是否匹配？
3. **评测标准** — 评测指标是否可量化？有没有"所以呢"结论？
4. **可执行性** — PRD 是否在现有资源下可实现？

### 走查结果路由

| 结果 | 动作 |
|------|------|
| 通过 | 写走查记录，PO 继续级联下游 |
| 打回（轮次 < 2） | 写走查记录 + 修改要求，@po 修改后重新走查 |
| 打回（第 2 轮） | BLOCKED，上报用户 |

### 终端报告格式

```
🏭 模型工厂流水线完成

📋 PRD：[需求摘要]
👑 CEO 走查：[N] 轮（通过/打回）
🧪 模型评测：Go / No-Go（[N] 轮）
🚀 推理部署：[状态]
📊 AB 效果：[结论]
🔄 PO 决策：继续/调整/砍掉

📊 闭环记录：
  PRD 走查：[N] 轮
  评测闸门：[N] 轮（Go/No-Go）
```
