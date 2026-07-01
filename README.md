# 日语老年关怀AI伴侣 — 训练数据集

> **AI Elderly Care Companion Training Dataset**  
> 目标模型：Qwen2.5-7B-Instruct（LLaMA-Factory LoRA微调）  
> 当前版本：**V10.1** | 2026年7月1日  
> 仓库：[github.com/BocrieM11/Query-data](https://github.com/BocrieM11/Query-data)

---

## 项目简介

本项目构建了一个面向**日语老年人AI关怀伴侣**的微调训练数据集。数据来源于15个YouTube日本老年人采访视频的Whisper语音转写，结合真实日语对话语料库和合成数据，覆盖14个生活话题。

老年人发言保留了真实的语音特征（关西方言~12%、填充词、自然叙事节奏），AI回复按照话题×意图×情感三维匹配，适用于LLaMA-Factory的LoRA微调。

## 数据集速览（V10.1）

```
训练集:    9,655 条  (80%)
验证集:    1,208 条  (10%)
测试集:    1,210 条  (10%)
─────────────────────────
总计:     12,073 条
```

| 指标 | 数值 |
|------|------|
| 真实数据率 | 92.7% |
| 平均轮次 | 5.8 轮/对话 |
| 平均字符 | 245 字/对话 |
| 人类发言平均长度 | 41 字 |
| AI回复平均长度 | 44 字 |
| AI去重回复数 | 10,501 |
| AI回复重复率 | 69.8% |
| Top-10回复占比 | 16.1% |
| 关西方言密度 | ~12% |
| 话题数 | 14 |
| 意图类型 | 8 |

### 14个话题分布

| 话题 | 占比 | 话题 | 占比 |
|------|------|------|------|
| 感恩/满足 | 28.4% | 兴趣/爱好 | 4.0% |
| 年金/经济 | 23.9% | 日常生活 | 1.3% |
| 怀旧/回忆 | 11.8% | 养老设施 | 1.0% |
| 一般话题 | 7.2% | 孤独 | 0.8% |
| 家庭 | 6.6% | 邻里/社区 | 0.6% |
| 健康 | 4.9% | 科技/数字 | 0.5% |
| 临终/丧失 | 4.9% | | |
| 工作/职业 | 4.1% | | |

---

## 目录结构

```
养老agent/
│
├── README.md                          ← 你正在读的文件
├── CHANGELOG.md                       ← 中文更新日志（V5→V10.1）
├── .gitignore                         ← Git忽略配置
│
├── ═══ 训练数据（核心输出） ═══
│
├── training_data/
│   ├── train.jsonl                    ← 训练集 9,655条 (9.6 MB)
│   ├── val.jsonl                      ← 验证集 1,208条
│   ├── test.jsonl                     ← 测试集 1,210条
│   ├── v10_new_whisper.jsonl          ← V10新提取的Whisper原始对话
│   ├── metadata.json                  ← 数据集元数据
│   └── DATACARD.md                    ← 数据集详细卡片（英文）
│
├── ═══ 真实音频转写数据 ═══
│
├── real_elderly_audio/                ← 9.6 MB（仅文本，原始音频已删除）
│   ├── *_whisper.json                 ← 11个视频的Whisper转写结果
│   │   ├── 06e_und6-C8_whisper.json   (65歳以上年金インタビュー, 61min)
│   │   ├── rQJEtScQqlU_whisper.json   (60-80代老後夫婦, 81min)
│   │   ├── W2pW9-R0YfY_whisper.json   (76歳一人暮らし, 56min, 独白)
│   │   ├── igfukXU_i-Y_whisper.json   (83歳老人ホーム, 29min, 独白)
│   │   ├── QbnnL0940ew_whisper.json   (91歳元看護師長, 38min)
│   │   ├── 5cvvDAQ_J9o_whisper.json   (元ゼネコン82歳, 27min)
│   │   ├── QC2mjYdXXXw_whisper.json   (元介護助手71歳, 28min)
│   │   ├── i9hThYGy7QI_whisper.json   (計画的無年金者62歳, 36min)
│   │   ├── mZwghdKpUU4_whisper.json   (72歳老人ホーム検討, 14min)
│   │   ├── K0AAUXZnvUk_whisper.json   (85歳マック勤務, 18min)
│   │   └── fbgRFiig3Qc_whisper.json   (介護の現実, 30min)
│   ├── *.ja.vtt                       ← 5个YouTube VTT字幕文件
│   ├── whisper_interviews.json        ← 汇总的采访数据
│   ├── cleaned_elderly_speech.json    ← 清洗后的老年人发言
│   ├── vtt_*.json                     ← VTT解析中间产物
│   └── new_video_info.json            ← 新视频信息
│
├── ═══ 真实日语语料分析 ═══
│
├── corpus_analysis/
│   ├── real_corpus_all.jsonl          ← 全语料汇总 130条 (4.2 MB)
│   └── by_type/
│       ├── apology_roleplay_FF.jsonl  ← 道歉角色扮演 (32条)
│       ├── firstmeeting_friends_FF.jsonl ← 初次见面女性朋友 (23条)
│       ├── firstmeeting_hierarchical_FF_MM_audio.jsonl ← 层级关系初次见面 (16条)
│       ├── friends_FF.jsonl           ← 女性朋友对话 (5条)
│       ├── friends_MM_FF.jsonl        ← 混合性别朋友对话 (19条)
│       ├── kansai_dialect.jsonl       ← 关西方言对话 (4条)
│       ├── native_learner_mixed.jsonl ← 母语者与学习者混合 (20条)
│       └── work_worry_theme.jsonl     ← 工作与担忧主题 (11条)
│
├── ═══ 原始对话设计文档 ═══
│
├── 对话/
│   ├── 用户画像.md                    ← 8种老年人用户画像定义
│   ├── V1～V4 日本养老院老人&AI陪护*.md ← 日语对话4个迭代版本
│   ├── 中国北方养老院老人&AI陪护*.md  ← 中文普通话对话
│   ├── 中国粤语养老院老人&AI陪护*.md  ← 中文粤语对话
│   ├── 美国养老院老人&AI陪护*.md      ← 英文（美式）对话
│   ├── 英国养老院老人&AI陪护*.md      ← 英文（英式）对话
│   ├── 法国养老院老人&AI陪护*.md      ← 法文对话
│   ├── 泰国养老院老人&AI陪护*.md      ← 泰文对话
│   └── 韩国养老院老人&AI陪护*.md      ← 韩文对话
│
├── ═══ 多语言ShareGPT输出（旧版） ═══
│
├── sharegpt_output/                   ← 4.3 MB（V5旧版输出）
│   ├── all.jsonl                      ← 全语言汇总
│   ├── index.json                     ← 索引
│   ├── by_country/                    ← 按国家/语言分类（8国）
│   │   ├── JP.jsonl  (日本)  ├── CN_N.jsonl (中国北方)
│   │   ├── CN_YUE.jsonl (中国粤语) ├── US.jsonl (美国)
│   │   ├── UK.jsonl (英国) ├── FR.jsonl (法国)
│   │   ├── KR.jsonl (韩国) └── TH.jsonl (泰国)
│   └── by_persona/                    ← 按8种人设分类（64个文件）
│
├── ═══ Python脚本（数据处理管道） ═══
│
├── improve_dataset_v81.py             ← V8.1 说话人识别+数据质量修复
├── transcribe_new_videos.py           ← V8.2 新视频Whisper转写+合并
├── improve_dataset_v9.py              ← V9 AI回复系统重写（200+模板）
├── inject_variation.py                ← V9.1 变化注入降低重复率
├── extract_more_whisper.py            ← V10 宽松策略提取更多Whisper对话
├── improve_dataset_v10.py             ← V10 核心优化（400+模板/14话题）
├── inject_variation_v10.py            ← V10.1 增强版变化注入
│
├── build_final_dataset.py             ← 构建最终数据集
├── fix_and_rebuild.py                 ← 修复+重建
├── final_quality_fix.py               ← 最终质量修复
├── expand_dataset.py                  ← 数据集扩展
├── convert_to_sharegpt.py             ← 格式转换为ShareGPT
├── prepare_training_data.py           ← 训练数据准备
├── merge_whisper_data.py              ← Whisper数据合并
├── improve_dataset_v8.py              ← V8旧版改进
├── analyze_real_corpus.py             ← 真实语料分析
├── whisper_transcribe.py              ← Whisper转写
├── scrape_more_youtube.py             ← YouTube视频爬取
├── search_and_download.py             ← YouTube搜索下载
├── vtt_parser_v2.py                   ← VTT字幕解析v2
├── vtt_final_parser.py                ← VTT字幕最终解析
│
├── ═══ 日志和临时文件 ═══
│
├── transcribe_log.txt                 ← 转写日志
├── diagnosis.txt                      ← 数据诊断报告
├── whisper_analysis.txt               ← Whisper数据分析
├── whisper_samples.txt                ← Whisper样本
├── v8_check.txt                       ← V8质量检查
├── v81_samples.txt                    ← V8.1样本
├── v91_final_check.txt                ← V9.1最终检查
├── analysis_output.txt                ← 分析输出
├── new_videos.txt / new_videos_raw.txt ← 新视频信息
└── CHANGELOG.md                       ← 中文更新日志
```

---

## 数据格式

ShareGPT JSONL 格式，每行一个JSON对象：

```json
{
  "id": "whisper_v81_06e_und6-C8_0001",
  "conversations": [
    {"from": "human", "value": "あのー、年金のことでちょっと相談したいねん。"},
    {"from": "gpt", "value": "はい、こんにちは！年金のことで何かお困りですか？"},
    {"from": "human", "value": "毎月の年金が入っても、家賃と光熱費で半分以上飛んでいくんよ…。"},
    {"from": "gpt", "value": "年金のことはご心配ですよね。毎月のやりくり、大変だと思います。一緒に家計の見直しをしてみませんか？"}
  ],
  "source": "real_elderly_whisper",
  "quality": "real_transcribed_v10",
  "language": "ja",
  "country_code": "JP",
  "scenario": "interview: 65歳以上年金インタビュー",
  "video_id": "06e_und6-C8",
  "num_turns": 6,
  "total_chars": 280
}
```

---

## 数据来源构成

| 来源 | 条数 | 占比 | 说明 |
|------|------|------|------|
| real_elderly_whisper | 10,297 | 85.3% | GPU Whisper转写的真实老年采访（11视频） |
| V9_topic_balanced | 576 | 4.8% | V9话题平衡补充（孤独/设施/日常/健康） |
| real_elderly_youtube_v5 | 454 | 3.8% | YouTube VTT字幕老年发言 |
| V5_synthetic | 286 | 2.4% | AI生成15场景×8人设 |
| real_corpus_slice | 248 | 2.1% | 真实日语对话语料切片 |
| V5_realistic | 198 | 1.6% | 扩展日常场景 |
| V5_cantonese_expanded | 14 | 0.1% | 粤语对话 |

---

## 15个YouTube视频来源

| 视频ID | 时长 | 类型 | 内容 |
|--------|------|------|------|
| 06e_und6-C8 | 61min | 采访 | 65歳以上年金インタビュー |
| rQJEtScQqlU | 81min | 采访 | 60-80代老後夫婦年金生活 |
| W2pW9-R0YfY | 56min | 独白 | 76歳一人暮らし体験談 |
| igfukXU_i-Y | 29min | 独白 | 83歳一人暮らし老人ホームの現実 |
| QbnnL0940ew | 38min | 采访 | 91歳元看護師長 |
| 5cvvDAQ_J9o | 27min | 采访 | 元ゼネコン82歳と現役介護士78歳 |
| QC2mjYdXXXw | 28min | 采访 | 元介護助手71歳女性 |
| i9hThYGy7QI | 36min | 采访 | 計画的無年金者62歳 |
| mZwghdKpUU4 | 14min | 采访 | 72歳老人ホーム検討中 |
| K0AAUXZnvUk | 18min | 采访 | 85歳マック勤務女性 |
| fbgRFiig3Qc | 30min | 采访 | 障がい持つ子供と妻、介護の現実 |
| srYz8XQ0Rao | ~15min | VTT | YouTube字幕 |
| Xa3Cr55SMXA | ~15min | VTT | YouTube字幕 |
| 2STVCsOoe5Y | ~15min | VTT | YouTube字幕 |
| E0QuMj0dcnc | ~15min | VTT | YouTube字幕 |

> 共约 **460分钟** 原始素材。所有音频已完成转写，原始文件已删除以节省空间。

---

## 版本演进

| 版本 | 总条数 | 真实数据率 | AI去重回复 | AI重复率 | 主要改进 |
|------|--------|-----------|-----------|---------|---------|
| V5 | 794 | 6.2% | ~10 | - | 初始AI合成数据 |
| V7 | 3,898 | 79.1% | ~50 | ~99% | Whisper GPU转写（有QA提取问题） |
| V8.1 | 3,600+ | 81.6% | 100+ | - | 说话人识别→丢弃采访者提问 |
| V8.2 | 4,126 | 81.6% | 928 | 89.9% | 新增7视频（+191分钟） |
| V9 | 4,500+ | 75.9% | 1,800+ | 91.9% | AI回复系统重写（200+模板） |
| V9.1 | 4,521 | 75.9% | 2,056 | 81.2% | 变化注入，Top-10占比18.2% |
| **V10.1** | **12,073** | **92.7%** | **10,501** | **69.8%** | **数据+167%, 14话题400+模板** |

详见 [CHANGELOG.md](CHANGELOG.md)。

---

## AI回复系统设计

V10.1使用 **14话题 × 8意图** 的三维匹配矩阵（400+模板）：

### 话题覆盖
`年金` `健康` `家族` `设施` `日常` `孤独` `工作` `兴趣` `临终` `怀旧` `科技` `感恩` `邻里` `通用`

### 意图检测
`statement`（陈述）`worry`（担忧）`question`（提问）`sharing`（分享）`grief`（哀伤）`nostalgia`（怀念）`confusion`（困惑）`gratitude`（感恩）

### 回复策略
- 人类发言 < 20字 → AI追问细节
- 人类发言 > 80字 → AI先共情再长回复
- 情感 negative + 临终话题 → 不急着给建议，先陪伴
- 12%的AI回复带关西方言（让AI更亲和）

---

## 使用方法

### 环境要求
```bash
pip install llamafactory
```

### LLaMA-Factory LoRA微调
```bash
llamafactory-cli train \
  --dataset training_data/train.jsonl \
  --val_dataset training_data/val.jsonl \
  --format sharegpt \
  --model_name_or_path Qwen2.5-7B-Instruct \
  --lora_rank 16 \
  --lora_alpha 32 \
  --learning_rate 2e-5 \
  --num_train_epochs 3 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 8 \
  --output_dir ./output/elderly-care-lora-v10
```

### 重新生成数据集
```bash
# 步骤1: 从Whisper JSON提取对话
python extract_more_whisper.py

# 步骤2: V10核心优化（修复错配+合成数据清理+话题扩展）
python improve_dataset_v10.py

# 步骤3: 变化注入（降低重复率）
python inject_variation_v10.py
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 语音转文字 | OpenAI Whisper medium (GPU fp16, RTX 4060, CUDA 12.4) |
| 视频下载 | yt-dlp (Python模块) |
| 数据格式 | ShareGPT JSONL |
| 语料来源 | YouTube + 日本語自然会話コーパス |
| 目标模型 | Qwen2.5-7B-Instruct |
| 微调框架 | LLaMA-Factory (LoRA) |
| 文本特征 | 关西方言 ~12%、填充词 ~25%、自然口语标记 |

---

## 已知问题

| 问题 | 优先级 | 说明 |
|------|--------|------|
| AI回复重复率69.8% | 中 | 相比V9.1已有大幅改善，仍有优化空间 |
| 部分话题数据不均衡 | 中 | 孤独(0.8%)、科技(0.5%)偏少 |
| 缺少评估基准 | 高 | 需要人工评估或LLM-as-judge |
| 方言覆盖不完整 | 低 | 仅关西方言，无东北/九州方言 |

---

## 脚本依赖关系

```
YouTube视频下载 (search_and_download.py, scrape_more_youtube.py)
        │
        ▼
Whisper转写 (whisper_transcribe.py, transcribe_new_videos.py)
        │
        ▼
VTT解析 (vtt_parser_v2.py, vtt_final_parser.py)
        │
        ▼
V8.1 话者识别 (improve_dataset_v81.py) ──→ V8.2 新视频合并 (transcribe_new_videos.py)
        │                                            │
        ▼                                            ▼
V9 回复系统重写 (improve_dataset_v9.py) ──→ V9.1 变化注入 (inject_variation.py)
        │
        ▼
V10 Whisper提取 (extract_more_whisper.py) ──→ V10优化 (improve_dataset_v10.py)
        │
        ▼
V10.1 变化注入 (inject_variation_v10.py) ──→ 最终数据集 training_data/
```

---

## 许可与引用

本项目仅用于研究和教育目的。YouTube视频内容版权归原作者所有。

数据集中的人名和可识别信息已被匿名化处理。

---

> **最后更新**：2026年7月1日 | V10.1 | [BocrieM11/Query-data](https://github.com/BocrieM11/Query-data)
