# Changelog

所有重要变更均记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

## [0.2.0] - 2026-06-17

### Added

- **4 个核心技能的深度参考层（references/）** — 把核心技术技能从"框架清单"升级为"方法论知识库"，遵循渐进披露（SKILL.md 入口 + references 按需加载）
  - `ml-pretraining-experiment`：超参范围+调度、Scaling Law(Chinchilla)+数据配比、训练失败诊断手册
  - `ml-alignment-rlhf`：对齐方法对比(SFT/DPO/KTO/ORPO/PPO/GRPO)+决策树、偏好数据构建+污染、安全对齐+红队+公开安全benchmark
  - `ml-inference-optimize`：量化方案对比(FP8/INT8/INT4/AWQ/GPTQ)、推理引擎对比(vLLM/SGLang/TRT-LLM)+serving调优、推理成本核算+GPU选型
  - `eval-benchmark-build`：评测指标+局限、LLM-as-Judge偏见与校准、公开能力benchmark清单(防数据污染)
- 4 个 SKILL.md 新增「深度参考（按需阅读）」指针章节

### Changed

- 内容深度与分层渐进披露显著提升；具体方法论、真实方法/benchmark 名称、失败诊断、经验值（均标注需校准）进入 references 层

---

## [0.1.0] - 2026-06-17

### Added

- **模型工厂 Agent 体系初版** — 专为「用最少人数跑通 数据 → 模型 → 服务 → 商业闭环」的大模型公司设计
- **15 个角色 Agent**（标准配置 15 人）：CEO、Product Owner、AI 产品经理、数据工程师、数据策略、ML·训练、ML·对齐、ML·推理、Evaluation、Backend/Platform、Infra/DevOps、MLOps、Growth、DevRel、运营
- **16 个核心技能**：覆盖数据流水线、预训练、对齐(RLHF)、推理优化、自动评测、AB回滚、模型API、MLOps流水线、开发者文档等
- **闭环协作流程** `agents/WORKFLOW.md` — 数据→模型→服务→商业 的条件分支 DAG + 交接标准
- **质疑协议** `agents/challenge-protocol.md` — 数据可得性 / 评测充分性 / 推理成本 三大对抗审查维度
- **三层记忆系统** `memory/` — core（常驻）/ archival（长期）/ recall（历史）
- **共享白板** `blackboard/` — current-sprint、open-questions、challenges、decisions-log
- **CLAUDE.md 记忆入口** — @import core 三文件
- **一键安装脚本** `install.sh` + **交互式初始化** `init.sh`
- **README.md** — 角色一览、闭环流程、安装说明

### 设计原则

- 与「一人公司」通用软件仓库（`skills/`）完全同构，格式 100% 对齐
- 内容全部改写为大模型公司语境：闭环、角色、KPI、技术栈
- 少层级 / 强自动化 / 工程优先 / 产品闭环，长期保持 20 人以内核心组织
