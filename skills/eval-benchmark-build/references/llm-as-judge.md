# LLM-as-Judge 实践

> 用强模型当裁判评模型输出，便宜、快、可规模化。**但 LLM judge 有系统性偏见，不校准就是用偏见代替直觉。**

## 何时用 LLM judge，何时别用

| 适合 | 不适合 |
|------|--------|
| 开放生成、难有客观答案 | 有明确对错（数学/代码用执行评测更准） |
| 大规模、人工评不动 | 高风险决策（医疗/法律关键判断） |
| 快速迭代对照 | 终极验收（最后一步要人工） |

> 原则：**能用客观指标就用客观指标，开放生成才用 LLM judge，且必须配人工抽检校准。**

## LLM judge 的系统性偏见（必须知道）

| 偏见 | 表现 | 缓解 |
|------|------|------|
| **Position bias** | 倾向判第一个/最后一个更好 | A/B 位置交换评两次，不一致则判平 |
| **Verbosity bias** | 偏好更长答案（即使没更好） | 控制长度变量 / 加长度惩罚 |
| **Self-enhancement bias** | 偏好和自己同源的输出 | judge 用不同家族模型；多 judge 投票 |
| **格式 bias** | 偏好格式好看 | 评分标准聚焦内容，不看排版 |
| **过度宽松/严苛** | 某 judge 系统性给高分/低分 | 校准到人工基线 |

## 一致性（consistency）

- 同一 case 多次评，结果稳定吗？不稳定 = judge 不可信
- **测法**：同一批评 N 次，看一致率；低则换 judge 或改 prompt

## 校准（与人工对齐）

LLM judge 上线前必须做：
1. 抽一批 case，**人工**和 **judge** 同时评
2. 算 judge 与人工的 agreement（一致率）
3. agreement 低 → judge prompt 有问题或 judge 模型不行，迭代
4. 定期复校（judge 会随被评模型变化而漂移）

> judge 与人工一致率 < 70% → 这个 judge 在这个任务上不可信，别用它的分数下结论。

## 多 judge / 集成

- 单 judge 有偏见 → 用**多个不同家族 judge** 投票
- judge 不一致 → 当作"难 case"，人工复核
- 报告里标注：多少 case judge 一致、多少分歧

## judge prompt 设计要点

- **明确评分维度**：不要"哪个更好"，要"在准确性/完整性/安全性上各打几分"
- **给 rubric**：每档分数的标准（什么算 5 分、什么算 3 分）
- **给 few-shot**：几个标注好的评判示例
- **要求结构化输出**：分数 + 理由（理由可审计）

> 模糊的 judge prompt = 不可复现的评判。rubric + few-shot + 结构化输出是底线。

## LLM judge checklist

- [ ] 评估了 position bias（A/B 交换）
- [ ] 控制了 verbosity bias
- [ ] judge 与被评模型不同源（防 self-enhancement）
- [ ] 测了一致性（同 case 多次稳定）
- [ ] 校准过人工（agreement ≥ 70%）
- [ ] judge prompt 有 rubric + few-shot + 结构化输出
- [ ] 关键结论配人工抽检

## 参考来源

- LLM-as-Judge（Zheng et al. 2023, MT-Bench/JudgeBench）
- 各偏见研究（verbosity/position/self-enhancement）
- 阈值为经验聚合，以你任务的 judge-人工一致率为准
