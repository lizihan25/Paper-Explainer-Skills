# 第三方素材与音频

本说明区分原创 prompt/代码、讲解视频以及视频中的素材。仓库的 MIT License 覆盖原创 prompts、文档与代码；媒体文件另按下列来源使用。记录日期：2026-10-23。

## 2026-10-25 配音 skill 与预览更新

`skills/local-narration/assets/reference_F.wav` 是已有 Breeze 合成 F 声线的固定参考片段，不对应特定真人。其出处、完整转录和使用条件见 [参考音频说明](skills/local-narration/assets/NOTICE.md)，该音频不采用仓库的 MIT 许可。随包附 Breeze 与 IndexTTS 模型许可副本，未分发模型权重；使用 Index 不会消除输入参考音频的条件。

新版 A 沿用 DPI-Net 原图、作者照片、原始合成 F 配音和原创 *Particle Study 01* BGM，配音从未变速音轨处理为 1.1 倍。图像和声音的来源条件沿用下方对应条目；原图在右上方用于持续位置参照，主画面的粒子和消息仍是教学示意。历史六段保持原文件与原速率，新增预览独立登记。

## 历史示例 A、B、C

| 内容 | 使用位置 | 来源与条件 |
| --- | --- | --- |
| 自绘机制、特征、卷积核、示意运动场 | A、B；C 的辅助注解 | 为论文讲解制作的示意图形；媒体不包含在仓库 MIT 授权范围内。 |
| DensePhysNet 架构图 Fig. 3、Table II | C 视频及其封面 | Zhenjia Xu et al.，RSS 2019。用作具体机制和实验的署名评述摘引；未取得独立开放再分发许可。 |
| 英文合成旁白 | A、B、C 共用音轨 | Breeze TTS 2，本地 `tts_instruction` 声线设计 F；研究与非商业用途，详见下节。 |
| 中英文字幕与图注 | A、B、C | 为本次讲解撰写；技术内容依据 DensePhysNet。 |
| BGM、作者照片 | 历史 A、B、C | 这些历史样片没有 BGM，也没有作者照片。 |

原论文：[DensePhysNet: Learning Dense Physical Object Representations via Multi-step Dynamic Interactions](https://arxiv.org/abs/1906.03853)。完整作者为 Zhenjia Xu、Jiajun Wu、Andy Zeng、Joshua B. Tenenbaum 和 Shuran Song。Fig. 3 位于 PDF 第 3 页，Table II 位于第 6 页。

该论文的 arXiv 页面链接到[非排他分发许可](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html)，这份许可授予 arXiv 分发权，不是向所有使用者提供的 CC 或 MIT 许可。原图和原表的著作权保留给其权利人。使用 C 的画面作为素材另做发布时，需要自行判断具体摘引用途或取得相应许可；本仓库没有把它们授权成可任意再用的素材。仓库不附完整论文 PDF。

## 当前 DPI-Net 三种样片

| 内容 | 来源与使用方式 |
| --- | --- |
| 原论文图 1 | [MIT CSAIL 作者项目页的 method.png](https://dpi.csail.mit.edu/imgs/method.png)，用于定位和解释方法，视频保留论文署名。 |
| 原论文图 4(c) | [论文](https://arxiv.org/abs/1810.01566)中的真实泡沫操作实验，作为控制过程的学术讲解摘引。 |
| Yunzhu Li 头像 | [作者个人主页](https://yunzhuli.github.io/)，用于论文身份介绍和记忆辅助。 |
| 自绘粒子、消息、层级和轨迹 | 为这次技术讲解编写的确定性示意动画，渲染源码在 `source/dpi_styles/`。 |
| 完整命名色族 | [3b1b/manim 默认配置](https://github.com/3b1b/manim/blob/master/manimlib/default_config.yml)，MIT，Copyright (c) 2020–2026 3Blue1Brown LLC；保留 [上游许可](source/dpi_styles/LICENSE-3B1B.txt)。 |
| 背景音乐 *Particle Study 01* | 本项目原创的程序合成电子琴和弦背景，78 BPM，没有外部录音或采样；人声时最多压低 5 dB。 |

论文全名为 *Learning Particle Dynamics for Manipulating Rigid Bodies, Deformable Objects, and Fluids*，作者 Yunzhu Li、Jiajun Wu、Russ Tedrake、Joshua B. Tenenbaum、Antonio Torralba，ICLR 2019，MIT CSAIL。以上图像在视频里用于署名技术解释；未确认原图和头像有面向所有人的开放再分发许可，仓库不单独打包这些图片或完整 PDF。源码附官方下载脚本供本地取得图 1 与头像，图 4 由使用者自行提供。

三种风格共享同一条英文旁白和混音。旁白用原先的合成 F 声线作为固定参考，以 `ref_clone_tata` 模式整段生成，再作保留音高的 1.25× 处理。这里的参考是合成声线，没有克隆特定真人。具体配置与音乐信息保存在 [源码目录](source/dpi_styles/README.md)。视频媒体仍受 Breeze 本地输出及其中第三方图像的条件约束；原创代码的 MIT 许可不改变这些条件。

## Breeze TTS 2 音频

历史三片的英文旁白由 **Breeze TTS 2 by BreezeBlue / RESONIA, INC.** 本地合成，属于合成声音。F 使用文字声线设计，没有克隆特定真人；三片共用同一条音轨，采用固定增益处理，保留原速。

官方将[推理代码的 Apache-2.0 许可](https://github.com/breezeblue-ai/breeze-tts/blob/main/LICENSE)与[模型及本地输出许可](https://huggingface.co/BreezeBlue/Breeze-TTS-2/blob/main/LICENSE)分开。后者为 **BreezeBlue Research and Non-Commercial License Agreement v1.1**，标注更新时间为 2026-09-01。

该协议第 4 节允许在论文、报告、仓库和非获利演示中发布非商业研究结果及说明样例，并要求合理注明 Breeze TTS 2。第 3 节与第 7.3 节使本地生成音频继续受非商业限制；商业使用需要另行书面许可。本仓库的示例按研究与非商业展示提供，不把旁白授权为 MIT 音频。其他使用条件以官方协议为准。

## 人物照片、音乐及后续样片

人物照片的来源、肖像身份与图片许可分别记录。作者或实验室网页提供照片，并不自动意味着允许开放再分发；新增照片应在示例清单中标明使用位置、原网页与图片权利依据。人物照片不继承仓库代码许可。

新增音乐应记录曲名、作者、获取地址、许可版本与所需署名，混音处理不改变音乐本身的许可。后续样片采用的论文图像、音频、照片和音乐，在加入公开示例时逐项登记。当前六片的条目见 [示例清单](examples/manifest.json)。

## 风格与工具名称

Prompt 中的 3Blue1Brown 表示配色与数学可视化的参考方向。仓库没有捆绑该频道的成片、音乐、标志或人物形象。Manim 与 Remotion 用于说明历史样片的实际制作工具，相关工具本身适用各自许可。
