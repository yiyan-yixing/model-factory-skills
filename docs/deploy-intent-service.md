# 意图识别服务部署指南

> 目标路径：`/home/work/baidu/new-yiyan/intent/`

## 部署包

部署包：`intent.tar.gz`（~741MB）

## 传输到目标服务器

从本地无法直接 SCP 到内网（iCode 是受限 shell），需通过内网可达的方式传输：

```bash
# 方式 1：VPN 直连
scp intent.tar.gz <user>@<target-host>:/tmp/

# 方式 2：跳板机中转
scp intent.tar.gz <user>@<jump-host>:/tmp/
ssh <jump-host> "scp /tmp/intent.tar.gz <target-host>:/tmp/"

# 方式 3：对象存储
boscmd put intent.tar.gz bos://bucket/intent.tar.gz
```

## 部署（3 步）

```bash
# 1. 解压到目标目录
mkdir -p /home/work/baidu/new-yiyan
tar -xzf intent.tar.gz -C /home/work/baidu/new-yiyan/

# 2. 安装依赖
cd /home/work/baidu/new-yiyan/intent
pip install -r requirements-serve.txt

# 3. 启动
bash start.sh
```

## 验证

```bash
curl http://localhost:8100/health
curl -X POST http://localhost:8100/intent -H "Content-Type: application/json" -d '{"query": "帮我画个猫"}'
```

## API 端点（供其他服务集成）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/intent` | 单条意图识别 |
| POST | `/intent/batch` | 批量意图识别 |
| GET | `/health` | 健康检查 |
| GET | `/schema` | 意图分类体系定义 |
| GET | `/examples` | 推理示例数据 |
| GET | `/eval` | 模型评估指标 |
| GET | `/` | 交互式测试页面 |

## 其他服务集成示例

```python
import requests

INTENT_API = "http://localhost:8100"  # 或 http://intent-service:8100

# 意图识别
resp = requests.post(f"{INTENT_API}/intent", json={"query": "帮我写个排序算法"}, timeout=5)
result = resp.json()
# result = {"intent": "code", "sub_intent": "code_gen", "rewritten_query": "...", ...}

# 获取分类体系
schema = requests.get(f"{INTENT_API}/schema").json()

# 健康检查
health = requests.get(f"{INTENT_API}/health").json()
```

建议配置：
- 超时：单条 5s，批量 30s
- 重试：2 次，指数退避
- 健康检查：GET /health，间隔 30s
- 资源：CPU ~500MB 内存，GPU ~1.5GB 显存

## 目录结构

```
/home/work/baidu/new-yiyan/intent/
├── serve_intent.py                          # FastAPI 服务（路径自包含）
├── test-page.html                           # 测试页面
├── start.sh                                 # 启动/停止/状态脚本
├── requirements-serve.txt                   # Python 依赖
├── README.md                                # 使用说明
├── models/intent-0.5b-v1/merged/            # 合并后独立模型 (~942MB)
│   ├── model.safetensors
│   ├── config.json
│   ├── generation_config.json
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── chat_template.jinja
├── models/intent-0.5b-v1/eval_results.json  # 评估指标
├── models/intent-0.5b-v1/examples.json      # 推理示例
├── data/intent/schema.json                  # 意图分类体系
├── data/intent/test.json                    # 测试集
├── data/intent/eval.json                    # 评估集
└── scripts/
    ├── inference_intent.py                  # CLI 推理脚本
    └── merge_lora.py                        # LoRA 合并脚本
```
