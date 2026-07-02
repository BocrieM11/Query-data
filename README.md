# 跌倒检测与离床检测数据集汇总

本项目汇集了跌倒检测、离床检测及相关领域的公开数据集资源，涵盖图像目标检测、视频分析、传感器信号、毫米波雷达等多种模态，适用于智能监护、医疗健康等场景的研究与开发。

---

## 目录

- [一、跌倒检测数据集](#一跌倒检测数据集)
  - [1. 跌倒行为目标检测数据集（YOLO格式）](#1-跌倒行为目标检测数据集yolo格式)
  - [2. Fall Vision（哈佛大学Dataverse）](#2-fall-vision哈佛大学dataverse)
  - [3. UR Fall Detection Dataset（URFD）](#3-ur-fall-detection-dataseturfd)
  - [4. Le2i Fall Detection Dataset](#4-le2i-fall-detection-dataset)
  - [5. SisFall Dataset](#5-sisfall-dataset)
  - [6. Pre-VFall（预跌倒检测数据集）](#6-pre-vfall预跌倒检测数据集)
  - [7. CCTV Incident 跌倒检测数据集（合成数据）](#7-cctv-incident-跌倒检测数据集合成数据)
  - [8. GMDCSA-24](#8-gmdcsa-24)
- [二、离床检测数据集](#二离床检测数据集)
  - [9. SPT：毫米波雷达睡眠姿势转换数据集](#9-spt毫米波雷达睡眠姿势转换数据集)
  - [10. ViFusionTST 离床意图预测](#10-vifusiontst-离床意图预测)
- [三、其他相关数据集](#三其他相关数据集)
  - [11. 病房床位状态检测数据集](#11-病房床位状态检测数据集)
  - [12. 睡眠健康与日常表现数据集](#12-睡眠健康与日常表现数据集)
- [四、徘徊/异常行为检测数据集](#四徘徊异常行为检测数据集)
  - [13. MIT 监控异常检测（NNMF方法）](#13-mit-监控异常检测nnmf方法)
- [五、日常活动识别基准数据集](#五日常活动识别基准数据集)
  - [14. MSRDailyActivity3D（日常活动识别）](#14-msrdailyactivity3d日常活动识别)
- [六、步态分析数据集](#六步态分析数据集)
  - [15. Health&Gait（多模态步态分析）](#15-healthgait多模态步态分析)
- [数据集速览表](#数据集速览表)

---

## 一、跌倒检测数据集

### 1. 跌倒行为目标检测数据集（YOLO格式）

| 属性 | 内容 |
|------|------|
| 规模 | **5,200张** 高质量人工标注图像 |
| 标注格式 | YOLO格式（.txt），支持 YOLOv5/v8/v10/v11、Faster R-CNN、SSD 等 |
| 场景覆盖 | 室内居家、走廊、病房等多类真实监护场景 |
| 类别 | 单类别（跌倒/fall） |
| 特点 | 姿态多样、光照复杂、遮挡丰富、人工精标 |

**获取方式：**

- [阿里云开发者社区](https://developer.aliyun.com/article/1683492)
- 网盘链接（提取码: `cva9`）

---

### 2. Fall Vision（哈佛大学Dataverse）

| 属性 | 内容 |
|------|------|
| 类型 | 视频数据集 |
| 规模 | 大规模基准数据集，32,131次下载 |
| 内容 | 58名志愿者，包含从床上、椅子、站立位置跌倒的视频 |
| 格式 | MP4视频 + CSV关键点文件（17个COCO关键点） |

**获取方式：**

- [哈佛Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/75QPKK)

> ⚠️ **注意：** 部分文件可能需要申请访问权限。

---

### 3. UR Fall Detection Dataset（URFD）

| 属性 | 内容 |
|------|------|
| 类型 | 视频 + 传感器数据集 |
| 设备 | 2个 Microsoft Kinect 相机 + 加速度计 |
| 内容 | 包含跌倒序列和日常活动（ADL）序列 |
| 格式 | 深度图CSV特征文件（含 HeightWidthRatio、MajorMinorRatio 等11维特征） |

**获取方式：**

- [官网](http://fenix.ur.edu.pl/mkepski/ds/uf.html)

---

### 4. Le2i Fall Detection Dataset

| 属性 | 内容 |
|------|------|
| 类型 | 视频数据集 |
| 场景 | Home（60视频）、Coffee room（70）、Office（64）、Lecture room（27） |
| 分辨率 | 320×240，25 FPS |
| 标注 | 包含跌倒开始帧和结束帧 |

**获取方式：**

- [Kaggle](https://www.kaggle.com/datasets/tuyenldvn/falldataset-imvia)
- [原始官网](http://le2i.cnrs.fr/Fall-detection-Dataset)

---

### 5. SisFall Dataset

| 属性 | 内容 |
|------|------|
| 类型 | 传感器数据集（可穿戴设备） |
| 规模 | 38名受试者，15种跌倒动作 + 19种日常活动（ADL） |
| 传感器 | 腰部固定三轴加速度计，200 Hz采样率 |
| 格式 | 传感器时序数据 |

**获取方式：**

- [原数据集（PMC）](https://pmc.ncbi.nlm.nih.gov/articles/PMC5870683/)
- [Kaggle](https://www.kaggle.com/datasets/aneesh10/sis-fall)
- [Mendeley Data](https://data.mendeley.com/datasets/6r7j7r8v9k/1)

---

### 6. Pre-VFall（预跌倒检测数据集）

| 属性 | 内容 |
|------|------|
| 类型 | 多模态图像数据集 |
| 规模 | **22,000+张** 图像实例 |
| 内容 | 正常（normal）、预跌倒前兆（prefall：虚弱/头晕/谵妄）、跌倒（fall）三类 |
| 特点 | **首个适合跌倒前（pre-impact）检测的公开数据集** |
| 格式 | 图像 + keygradient向量幅度/方向特征 |

**获取方式：**

- [Figshare](https://doi.org/10.6084/m9.figshare.26488216.v3)
- [GitHub代码](https://github.com/chollette/Pre-VFall-Vision-Sensor-Simulated-Early-Signs-of-Fall-Dataset)

---

### 7. CCTV Incident 跌倒检测数据集（合成数据）

| 属性 | 内容 |
|------|------|
| 类型 | 合成数据集 |
| 视角 | CCTV俯视视角 |
| 标注 | 边界框 + 17个COCO标准关键点骨架 |
| 兼容性 | 支持 YOLOv8 / YOLO11-Pose |
| 隐私 | 完全合成，无真实人物，规避GDPR风险 |

**获取方式：**

- [下载链接](http://i71i.com/8zdi)
- [Kaggle](https://www.kaggle.com/datasets/simuletic/cctv-incident-fall-and-lying-down-dataset)

---

### 8. GMDCSA-24

| 属性 | 内容 |
|------|------|
| 类型 | 视频数据集 |
| 场景 | 3种不同自然家庭环境 |
| 受试者 | 4名演员（带来动作多样性） |
| 内容 | 跌倒 + 日常活动（ADL） |
| 论文 | Data in Brief 期刊 |

**获取方式：**

- [论文页面](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11416611/)
- [扩展版本 E-GMDCSA24（事件相机数据）](https://doi.org/10.18710/T0GJXA)

---

## 二、离床检测数据集

### 9. SPT：毫米波雷达睡眠姿势转换数据集

| 属性 | 内容 |
|------|------|
| 类型 | 毫米波雷达数据集 |
| 规模 | 20名志愿者（15男5女，19-25岁），1,400个姿势转换样本 |
| 7种姿势转换 | 仰卧→侧卧、侧卧→仰卧、仰卧→俯卧、俯卧→仰卧、侧卧→俯卧、俯卧→侧卧、侧卧→侧卧 |
| 设备 | TI IWR6843ISK-ODS 毫米波雷达 |
| 数据内容 | 原始雷达数据（.bin）+ 处理后热图（.png） |
| 总大小 | 约 **117.84 GB** |

**获取方式：**

- [Kaggle](https://www.kaggle.com/datasets/ranhukaggle/sleep-posture-transition-dataset/)

---

### 10. ViFusionTST 离床意图预测

| 属性 | 内容 |
|------|------|
| 类型 | 负载传感器数据集（**非公开**） |
| 规模 | 长期护理机构95张床、连续6个月数据 |
| 传感器 | 床脚单颗低成本负载传感器 |
| 任务 | 预测早期离床意图（非离床后才报警） |
| 性能 | Accuracy 0.885, F1 0.794 |
| 论文 | IJCAI 2025 AI4TS Workshop |

**获取方式：**

- [论文（arXiv）](https://arxiv.org/abs/2506.22498)

> ⚠️ **数据集未公开**，可尝试联系作者 [hao.liu@ubc.ca](mailto:hao.liu@ubc.ca) 询问是否可共享。

---

## 三、其他相关数据集

### 11. 病房床位状态检测数据集

| 属性 | 内容 |
|------|------|
| 类型 | 图像目标检测 |
| 规模 | 953张图片 |
| 类别 | 2类：病床空闲（empty）、躺在病床（lying） |
| 格式 | YOLO格式 |

**获取方式：**

- CSDN（需积分/付费）

---

### 12. 睡眠健康与日常表现数据集

| 属性 | 内容 |
|------|------|
| 类型 | 结构化表格数据（非视觉） |
| 规模 | 100,000条记录，32列 |
| 性质 | 合成数据 |
| 用途 | 睡眠质量预测、健康数据分析 |
| 与视觉检测关联度 | **低**（不包含视频/图像/传感器信号） |

**获取方式：**

- [Kaggle](https://www.kaggle.com/datasets/mohankrishnathalla/sleep-health-and-daily-performance-dataset)

---

## 四、徘徊/异常行为检测数据集

### 13. MIT 监控异常检测（NNMF方法）

| 属性 | 内容 |
|------|------|
| 类型 | 视频异常行为检测（含代码） |
| 来源 | GitHub 开源项目 `ntienvu/abnormal_detection_video_surveillance` |
| 核心方法 | 非负矩阵分解（Nonnegative Matrix Factorization, NNMF） |
| 数据集 | MIT Video Surveillance Dataset（预处理为 .mat 格式） |
| 编程语言 | MATLAB 100% |
| 作者 | Dr Vu Nguyen (vu@ieee.org) |
| Stars/Forks | 12 stars / 9 forks |

**方法原理：**

1. **正常模式建模** — 从训练视频提取特征，用 NNMF 将高维数据分解为两个低维非负矩阵的乘积，学习正常行为的"基模式"
2. **异常检测** — 新视频帧特征与学习到的基模式对比，**重构误差大的帧**被标记为异常
3. **实现** — 使用贝叶斯非参数因子分析识别 K=40 个隐藏模式，代码改用 MATLAB 内置 `nnmf` 函数优化速度

**代码文件结构：**

| 文件 | 用途 |
|------|------|
| `demo_abnormal_detection.m` | 主演示脚本，运行完整异常检测流程 |
| `script_extract_feature.m` | 特征提取脚本（背景减除预处理） |
| `Overlay_MIT_Background.m` | 背景叠加可视化工具 |
| `mit_surveillance_processed_data.mat` | 预处理后的 MIT 数据集 |
| `mit_bg.jpg` | MIT 数据集背景图像 |

**运行方式：**

```matlab
% 在 MATLAB 中直接运行
run demo_abnormal_detection.m
```

**获取方式：**

- [GitHub 仓库](https://github.com/ntienvu/abnormal_detection_video_surveillance)

**与养老院监护场景的关联分析：**

| 维度 | 分析 |
|------|------|
| 技术路线 | 基于**特征提取 + 矩阵分解**的经典机器学习方法，非深度学习 |
| 适用场景 | MIT 数据集为**监控摄像头**视角的行人异常检测（奔跑、徘徊等） |
| 与跌倒/离床检测匹配度 | ⚠️ **中等偏低** — MIT 场景为室外/走廊监控，与室内床边场景差异较大 |
| 代码可复用性 | ⚠️ **有限** — MATLAB 实现，需迁移到 Python（可用 `sklearn.decomposition.NMF`） |
| 学术参考价值 | ✅ **较高** — NNMF 在异常检测中的方法论可参考 |

**优点：** 代码完整可运行验证 / 方法经典有学术论文支撑 / 轻量级无需 GPU / 适合理解异常检测基础原理

**缺点：** MATLAB 实现非 Python / 数据集场景与养老院不完全匹配 / 2015-2016 年方法非深度学习 SOTA / 特征提取依赖背景减除对动态场景敏感

> 💡 **迁移建议：** 参考其"特征提取 → 矩阵分解 → 重构误差 → 异常判定"流程，用 Python + `sklearn.decomposition.NMF` 重新实现，将 MIT 数据集替换为跌倒/离床检测数据集。也可考虑用 Autoencoder 替代 NNMF 以提升效果。



---

## 五、日常活动识别基准数据集

### 14. MSRDailyActivity3D（日常活动识别）

| 属性 | 内容 |
|------|------|
| 类型 | 视频数据集（仅保留RGB） |
| 来源 | Kaggle `mdmofazzalhossain789/msrdailyactivity3d-isolated-person` |
| 原始出处 | Microsoft Research (MSR) |
| 规模 | **320个视频**，16种活动，10名受试者 |
| 采集方式 | 每名受试者每种活动执行 **2次** |
| 分辨率 | 640×480（RGB），30 FPS |
| 原始内容 | RGB视频 + 深度视频（已移除） + 3D骨架关节坐标（已移除） |
| 用途 | 人体活动识别（HAR）、动作分类、姿态识别、多模态深度学习基准 |

**16种日常活动：**

| 编号 | 活动 | 英文名称 |
|:---:|------|----------|
| 1 | 用杯子喝水 | Drink from a cup |
| 2 | 吃饭/零食 | Eat a meal/snack |
| 3 | 读书 | Read a book |
| 4 | 打电话 | Call on cellphone |
| 5 | 书写 | Write on a paper |
| 6 | 使用笔记本电脑 | Use laptop |
| 7 | 使用吸尘器 | Use vacuum cleaner |
| 8 | 欢呼（举手） | Cheer up (hands up) |
| 9 | 静坐 | Sit still |
| 10 | 扔纸 | Toss paper |
| 11 | 玩游戏 | Play a game |
| 12 | 躺在沙发上 | Lie down on sofa |
| 13 | 行走 | Walk |
| 14 | 弹吉他 | Play guitar |
| 15 | 起立 | Stand up |
| 16 | 坐下 | Sit down |

**获取方式：**

- [Kaggle](https://www.kaggle.com/datasets/mdmofazzalhossain789/msrdailyactivity3d-isolated-person)

**与跌倒/离床检测的关联分析：**

| 维度 | 分析 |
|------|------|
| 直接关联度 | ⚠️ **中等** — 不含跌倒动作，但提供丰富的日常活动(ADL)样本 |
| 核心价值 | ✅ **高** — 可作为**负样本/正常行为**对照，用于跌倒检测二分类器的非跌倒类训练数据 |
| 关键活动 | "Lie down on sofa"（躺沙发）可与跌倒后躺地姿态做对比学习；"Walk"（行走）、"Stand up/Sit down"（起立/坐下）是离床检测前序动作 |
| 数据模态 | ⚠️ 仅保留RGB视频，原始深度图和骨架数据已移除 |
| 代码/基准 | ✅ 是 HAR 领域广泛使用的基准数据集，有大量现有方法可参考对比 |

> 💡 **使用建议：** 将本数据集的16种日常活动作为"非跌倒"负样本，与跌倒数据集（如 f_mask_b_1）中的正样本混合，构建二分类训练集。特别关注 "Lie down on sofa" 与跌倒后卧姿的区分，这是跌倒误报的主要来源之一。

---

## 六、步态分析数据集

### 15. Health&Gait（多模态步态分析）

| 属性 | 内容 |
|------|------|
| 类型 | 多模态视频数据集 |
| 来源 | GitHub `AVAuco/healthgait` |
| 开发团队 | AVA group，科尔多瓦大学（University of Cordoba） |
| 规模 | **1,564个视频，398名参与者**，在受控环境中行走 |
| Stars | ☆ 16 |
| 许可 | 非商业用途免费；二次分发需作者同意 |
| 论文 | Scientific Data (2025)，DOI: `10.1038/s41597-024-04327-4` |
| 特点 | **首个无需专用传感器、仅凭摄像头即可进行步态分析的数据集** |

**多模态数据内容：**

| 模态 | 方法/工具 | 格式 |
|------|-----------|------|
| 2D 姿态估计 | AlphaPose | JSON |
| 语义分割 | DensePose | PNG 图像 |
| 光流 | TVL1 / GMFlow | PNG 图像 |
| 人体剪影 | YOLOv8 | JPEG 图像 |

**参与者数据：**

- **人体测量数据：** 身高、体重、BMI、腰围/臀围/颈围、脂肪质量百分比、肌肉质量
- **步态参数（传感器实测）：** 由 OptoGait 和 MuscleLAB 传感器采集
- **步态参数（姿态估计）：** 步长、跨步长、步频、速度、摆动相/支撑相

**获取方式：**

- [GitHub 仓库](https://github.com/AVAuco/healthgait)
- [论文 (Scientific Data)](https://doi.org/10.1038/s41597-024-04327-4)

**同团队相关仓库：**

- [AVAuco/ucophyrehab](https://github.com/AVAuco/ucophyrehab) — UCO 物理康复数据集，基于姿态估计的运动分析

**与跌倒检测的关联分析：**

| 维度 | 分析 |
|------|------|
| 直接关联度 | ⚠️ **中等** — 聚焦正常步态分析，不含跌倒动作 |
| 核心价值 | ✅ **高** — 可作为**正常行走步态基准**，用于：① 跌倒前步态异常（如蹒跚、拖行）的对比基线；② 区分正常行走与跌倒过程中的运动模式差异 |
| 多模态参考 | ✅ 姿态估计 + 光流 + 剪影的组合方案可直接复用至跌倒检测任务 |
| 参与人群 | 398人规模较大，涵盖不同体型（BMI、体脂等），有利于泛化 |

> 💡 **使用建议：** 将其正常步态数据作为"非跌倒"对照样本；参考其多模态特征提取流程（AlphaPose → 光流 → 剪影），复用于跌倒检测视频的特征工程。

---

## 数据集速览表

| 序号 | 数据集名称 | 类型 | 规模 | 模态 | 公开状态 |
|:---:|-----------|------|------|------|:---:|
| 1 | 跌倒行为目标检测 | 图像 | 5,200张 | RGB图像 + YOLO标注 | ✅ 公开 |
| 2 | Fall Vision | 视频 | 58人 | RGB视频 + COCO关键点 | ⚠️ 需申请 |
| 3 | URFD | 视频+传感器 | — | RGB/深度图 + 加速度计 | ✅ 公开 |
| 4 | Le2i Fall Detection | 视频 | 221视频 | RGB视频 | ✅ 公开 |
| 5 | SisFall | 传感器 | 38人 | 三轴加速度计 | ✅ 公开 |
| 6 | Pre-VFall | 图像 | 22,000+张 | RGB图像 + 特征向量 | ✅ 公开 |
| 7 | CCTV Incident | 合成图像 | — | 合成RGB + COCO关键点 | ✅ 公开 |
| 8 | GMDCSA-24 | 视频 | 4人 | RGB视频 | ✅ 公开 |
| 9 | SPT | 雷达 | 20人/1,400样本 | 毫米波雷达 | ✅ 公开 |
| 10 | ViFusionTST | 传感器 | 95床/6个月 | 负载传感器 | ❌ 非公开 |
| 11 | 病房床位状态检测 | 图像 | 953张 | RGB图像 + YOLO标注 | ⚠️ 付费 |
| 12 | 睡眠健康与日常表现 | 表格 | 100,000条 | 结构化数据 | ✅ 公开 |
| 13 | MIT 监控异常检测（NNMF） | 视频+代码 | MIT 数据集 | RGB视频 + MATLAB代码 | ✅ 公开 |
| 14 | MSRDailyActivity3D | 视频 | 320个/16类 | RGB视频（仅RGB） | ✅ 公开 |
| 15 | Health&Gait | 多模态视频 | 1,564个/398人 | RGB + 姿态 + 光流 + 剪影 | ⚠️ 非商用免费 |

---

## 项目结构

```
识别/
├── README.md                             # 本文件
├── validate.py                           # 数据集校验脚本
├── rebuild.py                            # 重建脚本
│
├── data/
│   ├── fall_videos/                      # 243 个跌倒视频（MP4）
│   ├── fall_keypoints/                   # 243 个关键点 CSV（17点COCO，逐帧）
│   └── msr_daily3d/                      # 320 个日常活动视频（AVI，16类）
│       ├── drink/                        # 喝水 (20)
│       ├── eat/                          # 吃饭 (20)
│       ├── read book/                    # 读书 (20)
│       ├── walk/                         # 行走 (20)
│       ├── lie down on sofa/             # 躺沙发 (20) ← 跌倒检测关键负样本
│       ├── sit down/                     # 坐下 (20)
│       ├── stand up/                     # 起立 (20)
│       └── ... (共16类)                  # 其余日常活动
│
├── bedexit.v1i.yolov8/                   # 离床检测（YOLO格式，900张）
│   ├── train/                            # 800张
│   ├── valid/                            # 50张
│   ├── test/                             # 50张
│   └── data.yaml                         # 标签配置（5类）
│
├── llm_data/
│   ├── dataset_info.json                 # 列映射描述（3任务）
│   ├── fall_instruction/
│   │   └── data.json                     # 243 条跌倒检测指令
│   ├── bedexit_instruction/
│   │   └── data.json                     # 900 条离床检测指令
│   └── normal_instruction/
│       └── data.json                     # 320 条日常活动描述
│
├── f_mask_b_1.rar                        # 原始压缩包（保留）
├── f_mask_b_1_keypoints_csv.rar
├── archive.zip                           # MSRDailyActivity3D 压缩包
└── bedexit.v1i.yolov8.zip
```

## 数据统计

| 数据集 | 内容 | 规模 | 格式 |
|--------|------|:---:|------|
| `data/fall_videos/` | 跌倒视频（正样本） | 243 | MP4 |
| `data/fall_keypoints/` | 逐帧关键点 | 243 | CSV (17点COCO) |
| `data/msr_daily3d/` | 日常活动（负样本） | 320 | AVI (16类) |
| `bedexit.v1i.yolov8/` | 离床检测 | 900 | JPG + YOLO标注 |
| `llm_data/fall_instruction/` | 跌倒检测指令 | 243 | JSON (instruction/videos) |
| `llm_data/normal_instruction/` | 日常活动描述 | 320 | JSON (instruction/videos) |
| `llm_data/bedexit_instruction/` | 离床检测指令 | 900 | JSON (instruction/images) |

### 三类数据的任务角色

| 数据 | 跌倒检测 | 离床检测 | 徘徊检测 |
|------|:---:|:---:|:---:|
| fall_videos (243) | **正样本** | — | — |
| msr_daily3d walk (20) | 负样本 | — | **负样本** |
| msr_daily3d lie_down (20) | **关键负样本** | — | — |
| msr_daily3d sit/stand (40) | 负样本 | 参考 | — |
| msr_daily3d 其余 (240) | 负样本 | — | — |
| bedexit (900) | — | **正/负样本** | — |



---

## 参考与引用

如需在学术论文中引用以上数据集，请参阅各数据集官方页面中的引用说明。主要数据来源包括：

- 阿里云开发者社区
- Harvard Dataverse
- Kaggle
- Mendeley Data
- Figshare
- PMC (PubMed Central)

---

> 📅 最后更新：2026年6月
