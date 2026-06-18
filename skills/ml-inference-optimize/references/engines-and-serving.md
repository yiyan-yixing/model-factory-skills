# 推理引擎与 Serving 调优

> 选对引擎 + 调对参数，同样的模型吞吐能差几倍。这一页讲引擎怎么选、关键技术怎么用。

## 主流推理引擎对比

| 引擎 | 强项 | 适合 |
|------|------|------|
| **vLLM** | PagedAttention、高吞吐、生态广 | 通用首选，吞吐优先 |
| **SGLang** | 复杂编排、结构化输出、prefix cache 强 | Agent/多轮/结构化任务 |
| **TensorRT-LLM** | 极致延迟、Nvidia 深度优化 | 延迟极敏感、H 系列 |
| **TGI**（HuggingFace） | 易用、HF 生态 | 快速起步 |
| **llama.cpp / GGUF** | CPU/边缘、低资源 | 本地、嵌入式、私有化 |

> 到 2025-2026 主流：**vLLM（通用吞吐）+ SGLang（结构化/Agent）+ TensorRT-LLM（极致延迟）**。

## 决定吞吐/延迟的关键技术

### Continuous Batching（连续批处理）— 吞吐核心

- 不同请求动态组批，不等一批凑齐
- vLLM/SGLang/TGI 默认开；自研引擎**一定要有**，否则吞吐差一个量级

### PagedAttention / KV Cache 管理 — 显存核心

- KV cache 分页管理（像操作系统虚拟内存），碎片大幅减少
- 直接决定能并发多少请求、多大上下文

### Prefix Caching — 重复前缀加速

- 相同 system prompt / few-shot 前缀的 KV cache 复用
- 多轮对话、固定 system prompt 场景大幅降本
- SGLang/vLLM 都支持，**Agent 场景必开**

### Speculative Decoding（投机解码）— 延迟优化

- 小模型/草稿模型先猜，大模型批量验证
- 显著降延迟，吞吐看场景
- 适合**对延迟敏感**的场景（实时对话）

### Chunked Prefill — 长上下文优化

- 把长 prompt 的 prefill 切块，和 decode 交错，防长请求饿死短请求

## 选引擎决策

```
要极致吞吐、通用场景？
└─ vLLM

Agent / 多轮 / 结构化输出（JSON）/ 重前缀复用？
└─ SGLang

延迟极敏感、有 Nvidia H 系列、愿意调优？
└─ TensorRT-LLM

要快速跑起来、不在意极致优化？
└─ TGI 或 vLLM 默认配置

CPU/边缘/私有化小机器？
└─ llama.cpp
```

## 调优 checklist

- [ ] continuous batching 开了
- [ ] KV cache 大小调过（显存允许下尽量大，提并发）
- [ ] prefix caching 开了（如有重复前缀）
- [ ] max batch size / max num seqs 按显存调过
- [ ] 量化和引擎匹配（引擎支持的量化格式）
- [ ] 测了真实负载下的吞吐/延迟（不是空跑）

## 常见性能陷阱

| 陷阱 | 对策 |
|------|------|
| 没开 continuous batching | 吞吐差 10x，立刻开 |
| KV cache 太小 | 并发上不去，加显存给 KV |
| 长 prompt 把短请求饿死 | 用 chunked prefill |
| 固定 system prompt 每次重算 | 开 prefix caching |
| 量化格式引擎不支持 | 换支持的量化方案或引擎 |
| 只测单请求延迟 | 实际是并发场景，要测吞吐 |

> **优化前先 profile**——瓶颈在显存、算力、还是 KV cache？不同瓶颈对策不同。瞎调参数不如先量。

## 参考来源

- vLLM（PagedAttention, Kwon et al. 2023）
- SGLang（系列论文/文档）
- TensorRT-LLM / TGI 官方文档
- 关键技术名/行为为公开已知，具体参数以各引擎最新文档为准
