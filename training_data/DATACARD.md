# Japanese Elderly Care AI Companion Dataset v10.1

## Overview
- **Total**: 12,073 conversations
- **Format**: ShareGPT JSONL
- **Language**: Japanese (with Kansai dialect, ~12% density)
- **Splits**: train 9,655 / val 1,208 / test 1,210
- **Avg Turns**: 5.8 turns/conversation
- **Avg Chars**: 245 chars/conversation
- **Avg Human Length**: 41 chars
- **Avg AI Length**: 44 chars
- **AI Unique Responses**: 10,501
- **AI Repeat Rate**: 69.8%
- **Top-10 Response Share**: 16.1%
- **4+ turn dialogues**: 12,073 (100%)

## Source Composition
| Source | Count | % | Description |
|--------|-------|---|-------------|
| real_elderly_whisper | 10,297 | 85.3% | GPU-Whisper transcribed real elderly interviews (11 videos, V10 expanded extraction) |
| V9_topic_balanced | 576 | 4.8% | V9 topic-balanced synthetic conversations |
| real_elderly_youtube_v5 | 454 | 3.8% | YouTube VTT elderly speech |
| V5_synthetic | 286 | 2.4% | AI-generated: 15 scenarios, 8 personas |
| real_corpus_slice | 248 | 2.1% | Real Japanese conversation corpus |
| V5_realistic | 198 | 1.6% | Extended daily scenarios |
| V5_cantonese_expanded | 14 | 0.1% | Cantonese conversations |

## Real Data
| Type | Count | % |
|------|-------|---|
| Real human data | 11,192 | 92.7% |
| Real elderly speech | 10,751 | 89.0% |
| Topic-balanced (V9) | 576 | 4.8% |
| Synthetic (V5) | 498 | 4.1% |

## Topic Distribution (14 topics)
| Topic | Count | % |
|-------|-------|---|
| Gratitude (感恩) | 3,431 | 28.4% |
| Pension (年金) | 2,889 | 23.9% |
| Nostalgia (怀旧) | 1,430 | 11.8% |
| General (一般) | 865 | 7.2% |
| Family (家族) | 792 | 6.6% |
| Health (健康) | 597 | 4.9% |
| Death/Bereavement (临终) | 593 | 4.9% |
| Work (工作) | 494 | 4.1% |
| Hobby (兴趣) | 477 | 4.0% |
| Daily (日常) | 155 | 1.3% |
| Facility (设施) | 126 | 1.0% |
| Loneliness (孤独) | 93 | 0.8% |
| Community (邻里) | 68 | 0.6% |
| Technology (科技) | 63 | 0.5% |

## Multi-turn Distribution
| Turns | Count | % |
|-------|-------|---|
| 4 | 4,219 | 34.9% |
| 5 | 1,150 | 9.5% |
| 6 | 4,665 | 38.6% |
| 7 | 280 | 2.3% |
| 8 | 1,580 | 13.1% |
| 10+ | 179 | 1.5% |

## All Video Sources (15 videos)
### Original (8 videos)
| Video | Duration | Type | Conversations |
|-------|----------|------|---------------|
| 06e_und6-C8 | 61min | Interview | 2,465 |
| rQJEtScQqlU | 81min | Interview | 1,520 |
| W2pW9-R0YfY | 56min | Monologue | 931 |
| srYz8XQ0Rao | ~15min | VTT | 185 |
| Xa3Cr55SMXA | ~15min | VTT | 171 |
| 2STVCsOoe5Y | ~15min | VTT | 169 |
| E0QuMj0dcnc | ~15min | VTT | 110 |
| igfukXU_i-Y | 29min | Monologue | 239 |

### New "年金いくら？" Series (7 videos, 191min)
| Video | Duration | Content | Conversations |
|-------|----------|---------|---------------|
| i9hThYGy7QI | 36min | 計画的無年金者62歳 | 1,106 |
| QC2mjYdXXXw | 28min | 元介護助手71歳女性 | 980 |
| QbnnL0940ew | 38min | 91歳元看護師長 | 975 |
| fbgRFiig3Qc | 30min | 障がい持つ子供と妻、介護の現実 | 714 |
| 5cvvDAQ_J9o | 27min | 元ゼネコン82歳と現役介護士78歳 | 580 |
| K0AAUXZnvUk | 18min | 85歳マック勤務女性 | 562 |
| mZwghdKpUU4 | 14min | 72歳老人ホーム検討中 | 427 |

## Version History
| Version | Records | Real Elderly | Avg Turns | Avg Chars | AI Unique | Repeat Rate | Key |
|---------|---------|-------------|-----------|-----------|-----------|------------|-----|
| v5 | 794 | 6.2% | - | - | - | - | Initial synthetic |
| v7 | 3,898 | 79.1% | 3.1 | 50 | ~50 | ~99% | Whisper GPU (bad QA) |
| v8.2 | 4,126 | 81.6% | 5.7 | 183 | 928 | 89.9% | +7 videos, multi-turn |
| v9.1 | 4,521 | 70.4% | 6.1 | 260 | 2,056 | 81.2% | 200+ templates, topic balanced |
| **v10.1** | **12,073** | **89.0%** | **5.8** | **245** | **10,501** | **69.8%** | **14 topics, 400+ templates, +167% data** |

## V10.1 Key Improvements
1. **数据量暴增**：4,521→12,073 (+167%)，从Whisper JSON提取了75%未用的语音段
2. **话题扩展**：8→14话题，新增临终/怀旧/科技/感恩/经济困难/邻里社区
3. **意图检测升级**：4→8种意图 (新增nostalgia/grief/confusion/gratitude)
4. **AI回复模板**：86→400+，按14话题×8意图三维匹配
5. **反復率大幅改善**：81.2%→69.8%，AI去重回复 2,056→10,501 (×5.1)
6. **真实数据率**：75.9%→92.7%
7. **AI回复长度**：35→44字 (+26%)
8. **关西方言密度**：8%→12%

## Usage
```bash
llamafactory-cli train \
  --dataset training_data/train.jsonl \
  --val_dataset training_data/val.jsonl \
  --format sharegpt \
  --model_name_or_path Qwen2.5-7B-Instruct \
  --lora_rank 16
```
