# 护工记录数据集 — 质量审计报告

**审计日期**: 2026-06-29
**数据量**: 500 条
**语言分布**: {'zh': 250, 'ja': 125, 'en': 125}

---

## 总览

| 检查项 | 问题数 | 严重程度 |
|--------|--------|----------|
| 完全重复文本 | 0 | 🟢 通过 |
| 前30字近似重复 | 20 | 🟡 注意 |
| BP 文本-结构不一致 | 13 | 🟡 注意 |
| 体温 文本-结构不一致 | 18 | 🟡 注意 |
| 医学数值不合理 | 64 | 🔴 严重 |
| 居民档案前后矛盾 | 0 | 🟢 通过 |
| 文本过短 (<25字) | 0 | 🟢 通过 |
| 文本过长 (>250字) | 1 | 🟢 通过 |
| 【】括号不平 | 0 | 🟢 通过 |
| 分类-内容不匹配 | 179 | 🔴 严重 |
| 空标签 | 0 | 🟢 通过 |
| 需跟进但无详情 | 0 | 🟢 通过 |

---

## 逐项详情

### 1. 重复检测

- **完全重复**: 0 条（应全部修复）
- **前30字相同**: 20 条（可能是模板化生成导致，建议人工抽检）

### 2. 文本-结构字段一致性

**BP 不一致** (13 条):

- `REC-JA-0059`: Text BP~134.0 vs struct 150/不快

- `REC-ZH-0315`: Text BP~125.0 vs struct 150/68

- `REC-EN-0460`: Text BP~37.6 vs struct 150/80

- `REC-ZH-0234`: Text BP~125.0 vs struct 150/88

- `REC-ZH-0345`: Text BP~125.0 vs struct 134/72

- `REC-EN-0445`: Text BP~19.0 vs struct 148/76

- `REC-EN-0458`: Text BP~85 vs struct 134/82

- `REC-EN-0443`: Text BP~85 vs struct 138/90

- `REC-ZH-0288`: Text BP~125.0 vs struct 150/82

- `REC-JA-0197`: Text BP~2.0 vs struct 122/90

- ... 还有 3 条

**体温不一致** (18 条):

- `REC-EN-0454`: Text T=17.0 vs struct 36.8

- `REC-EN-0127`: Text T=37.6 vs struct 38.4

- `REC-EN-0490`: Text T=13.0 vs struct 36.5

- `REC-EN-0116`: Text T=3.0 vs struct 36.3

- `REC-EN-0444`: Text T=12.0 vs struct 36.9

- `REC-EN-0109`: Text T=2.0 vs struct 36.5

- `REC-EN-0456`: Text T=6.0 vs struct 36.2

- `REC-EN-0432`: Text T=13.0 vs struct 37.0

- `REC-EN-0473`: Text T=11.0 vs struct 36.7

- `REC-EN-0452`: Text T=19.0 vs struct 36.8

### 3. 医学数值不合理 (64 条)

- `REC-JA-0032`: SpO2=122.0 out of range

- `REC-JA-0054`: SpO2=128.0 out of range

- `REC-JA-0059`: SpO2=134.0 out of range

- `REC-JA-0029`: SpO2=132.0 out of range

- `REC-JA-0018`: SpO2=134.0 out of range

- `REC-JA-0015`: SpO2=118.0 out of range

- `REC-JA-0036`: SpO2=140.0 out of range

- `REC-JA-0041`: SpO2=134.0 out of range

- `REC-ZH-0085`: SpO2=126.0 out of range

- `REC-ZH-0105`: SpO2=118.0 out of range

- `REC-ZH-0083`: SpO2=150.0 out of range

- `REC-JA-0028`: SpO2=128.0 out of range

- `REC-JA-0051`: SpO2=126.0 out of range

- `REC-JA-0021`: SpO2=126.0 out of range

- `REC-JA-0026`: SpO2=122.0 out of range

- ... 还有 49 条

### 4. 居民档案一致性 (0 条冲突)

### 5. 文本长度问题

- **过短** (<25字): 0 条
- **过长** (>250字): 1 条
- **【】括号不平**: 0 条

### 6. 分类-内容不匹配 (179 条)

- `REC-EN-0122`: Cat 04 (Fall Incidents) but no keywords found in text

- `REC-ZH-0263`: Cat 08 (家属沟通) but no keywords found in text

- `REC-EN-0128`: Cat 06 (Shift Handover) but no keywords found in text

- `REC-ZH-0262`: Cat 01 (日常护理) but no keywords found in text

- `REC-ZH-0334`: Cat 01 (日常护理) but no keywords found in text

- `REC-EN-0430`: Cat 08 (Family Communication) but no keywords found in text

- `REC-EN-0454`: Cat 01 (Daily Care) but no keywords found in text

- `REC-EN-0469`: Cat 01 (Daily Care) but no keywords found in text

- `REC-EN-0121`: Cat 04 (Fall Incidents) but no keywords found in text

- `REC-EN-0425`: Cat 09 (Emotional Care) but no keywords found in text

- `REC-EN-0489`: Cat 09 (Emotional Care) but no keywords found in text

- `REC-ZH-0367`: Cat 01 (日常护理) but no keywords found in text

- `REC-EN-0492`: Cat 06 (Shift Handover) but no keywords found in text

- `REC-ZH-0374`: Cat 09 (情绪心理) but no keywords found in text

- `REC-EN-0468`: Cat 07 (Rehabilitation) but no keywords found in text

- ... 还有 164 条

### 7. 标签问题

- 空标签: 0 条
- `follow_up_needed=true` 但无 `follow_up_detail`: 0 条

---

## 分类分布

| 分类 | 日(ja) | 中(zh) | 英(en) | 合计 |
|------|--------|--------|--------|------|
| 01 日常护理 | 45 | 55 | 22 | 122 |
| 02 健康监测 | 16 | 24 | 13 | 53 |
| 03 服药管理 | 4 | 4 | 3 | 11 |
| 04 跌倒事件 | 10 | 25 | 15 | 50 |
| 05 异常事件 | 12 | 25 | 13 | 50 |
| 06 交接班记录 | 8 | 24 | 13 | 45 |
| 07 康复活动 | 11 | 21 | 15 | 47 |
| 08 家属沟通 | 10 | 40 | 13 | 63 |
| 09 情绪心理 | 9 | 32 | 18 | 59 |

---

## 总结

| 风险等级 | 数量 | 说明 |
|----------|------|------|
| 🔴 严重 | 2 项 | 需要修复 |
| 🟡 注意 | 3 项 | 建议审查 |
| 🟢 通过 | — | 其余检查项 |
