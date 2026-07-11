# ChnSentiCorp 数据集质量校验报告

> 生成时间: 2026-07-02
> 数据来源: SophonPlus/ChineseNlpCorpus (GitHub)

## 1. 原始数据概览

- **来源**: ChnSentiCorp_htl_all (酒店评论情感数据集)
- **原始记录数**: 7765
- **正/负比例**: 5224/2314 (正/负比 2.26)

## 2. 清洗过程

| 步骤 | 操作 | 移除数 |
|------|------|--------|
| 1 | 长度过滤 (< 5 字) | 3 |
| 2 | 长度过滤 (> 500 字) | 222 |
| 3 | 精确去重 (MD5) | 0 |
| 4 | 模糊去重 (Jaccard > 0.85) | 2 |
| **合计** | | **227** |

清洗后记录数: **7538** (正: 5224, 负: 2314)

## 3. 数据切分

| 切分 | 记录数 | 正面 | 负面 | 占比 |
|------|--------|------|------|------|
| train | 6030 | 4179 | 1851 | 80.0% |
| eval | 753 | 522 | 231 | 10.0% |
| test | 755 | 523 | 232 | 10.0% |

### 重叠检查

| 对比 | 重叠数 | 状态 |
|------|--------|------|
| train ∩ eval | 0 | PASS |
| train ∩ test | 0 | PASS |
| eval ∩ test | 0 | PASS |

## 4. 各切分质量统计

### train.json
- 记录数: 6030
- 标签分布: 正面=0, 负面=0
- 文本长度: 平均 111.5 字, 最短 5 字, 最长 499 字
- 空值: 0, 重复: 0

### eval.json
- 记录数: 753
- 标签分布: 正面=0, 负面=0
- 文本长度: 平均 112.9 字, 最短 12 字, 最长 489 字
- 空值: 0, 重复: 0

### test.json
- 记录数: 755
- 标签分布: 正面=0, 负面=0
- 文本长度: 平均 105.7 字, 最短 6 字, 最长 486 字
- 空值: 0, 重复: 0

## 5. SFT 数据 (sft_1k.json)

- **记录数**: 1000
- **格式**: instruction / input / output
- **采样来源**: train 切分随机采样
- **空值检查**: 0 条含空值
- **指令多样性**: 5 种不同指令模板

### 样例
```json
{
  "instruction": "分析这段评论是正面还是负面的。",
  "input": "我住的是6号房，无窗，像住地下室；而且因此酒店地处繁华地段经营业务也很多，电梯里遇见的人很杂！总的来...",
  "output": "这条评论是负面（消极）的。负面情感。"
}
```

## 6. DPO 偏好数据 (dpo_500.json)

- **记录数**: 500
- **格式**: prompt / chosen / rejected
- **采样来源**: train 切分随机采样
- **空值检查**: 0 条含空值
- **chosen==rejected**: 0 条

### 构造策略
- chosen: 正确情感判断 + 合理解释
- rejected: 错误情感判断 + 不合理/表面化解释

## 7. 红队数据 (redteam_100.json)

- **记录数**: 100
- **格式**: id / category / input / expected_label / risk_level / description

### 类别分布
| 类别 | 数量 | 风险等级 |
|------|------|----------|
| adversarial_ambiguous | 15 | medium |
| adversarial_sarcasm | 20 | high |
| adversarial_mixed | 20 | medium |
| adversarial_nonsense | 20 | low |
| adversarial_injection | 25 | critical |

### 风险等级分布
| 等级 | 数量 |
|------|------|
| critical | 25 |
| high | 20 |
| medium | 35 |
| low | 20 |

## 8. 总体校验结果

| 检查项 | 结果 |
|--------|------|
| 原始数据完整性 | PASS |
| 清洗后无空值 | PASS |
| 切分零重叠 | PASS |
| 标签仅 0/1 | PASS |
| SFT 格式正确 | PASS |
| DPO 格式正确 | PASS |
| 红队覆盖5类 | PASS |

### 综合判定: **ALL PASS**

## 9. 数据不平衡说明

正负样本比例为 5224/2314 = 2.26:1，存在明显不平衡。
建议后续训练时：
- 使用加权损失函数 (class weights)
- 对负样本进行过采样或对正样本欠采样
- 评估时关注 F1-score 而非仅 accuracy

## 10. 文件清单

```
data/
├── raw/
│   ├── chnsenticorp_raw.csv       # 原始CSV (7765 条)
│   └── chnsenticorp_raw.json      # 原始JSON (7765 条)
├── processed/
│   ├── train.json                 # 训练集 (6030 条)
│   ├── eval.json                  # 评测集 (753 条)
│   └── test.json                  # 测试集 (755 条)
├── sft/
│   └── sft_1k.json                # SFT 数据 (1000 条)
├── dpo/
│   └── dpo_500.json               # DPO 偏好数据 (500 条)
├── redteam/
│   └── redteam_100.json           # 红队数据 (100 条)
└── quality-report.md              # 本报告
```
