# Japanese Elderly Care AI Companion Dataset v9.1

## Overview
- **Total**: 4,521 conversations
- **Format**: ShareGPT JSONL
- **Language**: Japanese (with light Kansai dialect, ~8% density)
- **Splits**: train 3,614 / val 453 / test 454
- **Avg Turns**: 6.1 turns/conversation
- **Avg Chars**: 260 chars/conversation
- **Min Chars**: 80 chars/conversation
- **AI Unique Responses**: 2,056
- **Top-10 Response Share**: 18.2% (down from 50%+ in V8)
- **4+ turn dialogues**: 4,521 (100%)

## Source Composition
| Source | Count | % | Description |
|--------|-------|---|-------------|
| real_elderly_whisper | 2,728 | 60.3% | GPU-Whisper transcribed real elderly interviews (11 videos) |
| V9_topic_balanced | 590 | 13.1% | V9新增：孤独/施設/日常/健康 话题补充 |
| real_elderly_youtube_v5 | 456 | 10.1% | YouTube VTT elderly speech |
| V5_synthetic | 286 | 6.3% | AI-generated: 15 scenarios, 8 personas |
| real_corpus_slice | 249 | 5.5% | Real Japanese conversation corpus |
| V5_realistic | 198 | 4.4% | Extended daily scenarios |
| V5_cantonese_expanded | 14 | 0.3% | Cantonese conversations |

## Real Data
| Type | Count | % |
|------|-------|---|
| Real human data | 3,433 | 75.9% |
| Real elderly speech | 3,184 | 70.4% |
| Topic-balanced (V9) | 590 | 13.1% |
| Synthetic (V5) | 498 | 11.0% |

## All Video Sources (15 videos)
### Original (8 videos)
| Video | Duration | Type | Conversations |
|-------|----------|------|---------------|
| 06e_und6-C8 | 61min | Interview | 652 |
| rQJEtScQqlU | 81min | Interview | 401 |
| W2pW9-R0YfY | 56min | Monologue | 232 |
| srYz8XQ0Rao | ~15min | VTT | 185 |
| Xa3Cr55SMXA | ~15min | VTT | 171 |
| 2STVCsOoe5Y | ~15min | VTT | 169 |
| E0QuMj0dcnc | ~15min | VTT | 110 |
| igfukXU_i-Y | 29min | Monologue | 60 |

### New "年金いくら？" Series (7 videos, 191min)
| Video | Duration | Content | Conversations |
|-------|----------|---------|---------------|
| i9hThYGy7QI | 36min | 計画的無年金者62歳 | 289 |
| QC2mjYdXXXw | 28min | 元介護助手71歳女性 | 255 |
| QbnnL0940ew | 38min | 91歳元看護師長 | 246 |
| fbgRFiig3Qc | 30min | 障がい持つ子供と妻、介護の現実 | 183 |
| 5cvvDAQ_J9o | 27min | 元ゼネコン82歳と現役介護士78歳 | 153 |
| K0AAUXZnvUk | 18min | 85歳マック勤務女性 | 145 |
| mZwghdKpUU4 | 14min | 72歳老人ホーム検討中 | 114 |

## Multi-turn Distribution
| Turns | Count | % |
|-------|-------|---|
| 3 | 184 | 4.5% |
| 4 | 1,011 | 24.5% |
| 5 | 305 | 7.4% |
| 6 | 1,825 | 44.2% |
| 7 | 77 | 1.9% |
| 8 | 644 | 15.6% |
| 10 | 80 | 1.9% |

## Version History
| Version | Records | Real Elderly | Avg Turns | Avg Chars | AI Unique | Key |
|---------|---------|-------------|-----------|-----------|-----------|-----|
| v5 | 794 | 6.2% | - | - | - | Initial |
| v7 | 3,898 | 79.1% | 3.1 | 50 | ~50 | Whisper GPU (bad QA) |
| v8.2 | 4,126 | 81.6% | 5.7 | 183 | 928 | +7 videos, multi-turn |
| **v9.1** | **4,521** | **70.4%** | **6.1** | **260** | **2,056** | **AI diversity +122%, topic balanced** |

## V9.1 Key Improvements
1. **AI回复多样化**：200+情境模板 → 2,056唯一回复（+122%），Top10回复占比50%→18%
2. **上下文感知**：按话题×意图(worry/statement/question/sharing)×情感(pos/neg/neutral)匹配回复
3. **话题平衡**：孤独+300, 施設+250, 日常+200, 健康+150
4. **老年人发言增强**：平均34→49字（+44%），更多生活细节和叙事
5. **文本变化注入**：敬语变化、前后缀、句子重组 → AI重复率从89.9%→81.2%

## Usage
```bash
llamafactory-cli train \
  --dataset training_data/train.jsonl \
  --val_dataset training_data/val.jsonl \
  --format sharegpt \
  --model_name_or_path Qwen2.5-7B-Instruct \
  --lora_rank 16
```
