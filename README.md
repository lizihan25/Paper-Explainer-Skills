# Paper Explainer Skills

把学术论文做成能看懂技术细节的视频和 HTML 阅读资料。讲解沿着输入、表示变化和输出展开，把关键创新单独讲透，再用原图、基线与实验判断设计的价值。

这套 prompt 来自论文动画与阅读页的实际制作反馈：原论文图应当占据主要画面，动画用于解释信息流、点流和迭代等动态机制；作者、年份和研究组帮助记忆，声音与字幕保持连续，导航只在需要时出现。内容要求与个人的配色、语速、BGM 等偏好分别说明，方便继续调整。

## 直接使用

选择一种用途与详细程度，把相应 prompt 连同论文、受众、范围和交付目标交给模型即可。四份 prompt 均可独立复制。

| 用途 | 精炼版 | 指导版 |
| --- | --- | --- |
| 论文视频 | [目标与制作要求](skills/paper-video/prompts/concise.md) | [研究、分镜、声音与成片衔接](skills/paper-video/prompts/guided.md) |
| HTML 阅读资料 | [内容与阅读效果](skills/paper-reading-html/prompts/concise.md) | [资料组织、交互、资源与页面检查](skills/paper-reading-html/prompts/guided.md) |

精炼版适合能自主规划长任务的模型；指导版补充阶段间需要衔接的内容，仍保留选题、叙事和视觉设计空间。也可以将 `skills/paper-video/` 或 `skills/paper-reading-html/` 整个目录放入支持 `SKILL.md` 的工具的技能目录。

例如：

> 使用视频精炼 prompt，介绍这篇论文最有意思的技术设计。重点沿一个输入解释模型内的信息变化，原图为主，适合时插入动画。先做三个可直接比较的风格片段，均使用英文配音和中英文字幕。

## 新样片：DPI-Net 信息流

三版以同一段 **47.21 秒、720p24** 的方法讲解比较画面。从粒子状态、动态图、多轮传播和层级，一直讲到预测、动作优化，以及执行后重新观测。旁白使用固定的合成 F 参考声线、整段生成及保留音高的 1.25× 加速；统一加入原创背景音乐 *Particle Study 01*，人声出现时压低音乐。

| Nocturne · 黑底数学剧场 | Microscope · 原图显微镜 | Atlas · 纸面自由画布 |
| --- | --- | --- |
| [![Nocturne 黑底数学剧场](examples/current/dpi-nocturne.jpg)](examples/current/dpi-nocturne.mp4) | [![Microscope 原图显微镜](examples/current/dpi-microscope.jpg)](examples/current/dpi-microscope.mp4) | [![Atlas 纸面自由画布](examples/current/dpi-atlas.jpg)](examples/current/dpi-atlas.mp4) |
| 黑底、语义色族和运动消息，展开图内计算。 | 原图占主要画面，平滑定位与放大对应部位。 | 暖色连续画布，沿空间关系移动观看位置。 |
| [播放 Nocturne](examples/current/dpi-nocturne.mp4) | [播放 Microscope](examples/current/dpi-microscope.mp4) | [播放 Atlas](examples/current/dpi-atlas.mp4) |

[六片本地画廊](examples/index.html) · [双语字幕](source/dpi_styles/subtitles/bilingual.srt) · [英文字幕](source/dpi_styles/subtitles/en.srt) · [中文字幕](source/dpi_styles/subtitles/zh.srt) · [独立渲染源码与运行说明](source/dpi_styles/README.md)

论文：Yunzhu Li、Jiajun Wu、Russ Tedrake、Joshua B. Tenenbaum、Antonio Torralba，[*Learning Particle Dynamics for Manipulating Rigid Bodies, Deformable Objects, and Fluids*](https://arxiv.org/abs/1810.01566)，ICLR 2019，MIT CSAIL。短片聚焦十句方法信息流；完整的实验比较与消融需要更长的讲解。图 1、图 4(c) 和作者头像作为有出处的学术讲解摘引，独立图片不随源码提供。

## 三种早期样片

三片使用同一段 DensePhysNet 讲稿与合成英文音轨，均为 **72.35 秒、1080p60、中上英下字幕**。它们保留当时的语速和无 BGM 版本，展示不同视觉语言。当前 prompt 已加入语速、声线连续性和轻 BGM 的新要求。

[打开本地视频画廊](examples/index.html) · [示例清单](examples/manifest.json)

| A · 科研图解 | B · 张量工作室 | C · 论文证据导览 |
| --- | --- | --- |
| [![A 科研图解](examples/previous/a-paper-schematic.jpg)](examples/previous/a-paper-schematic.mp4) | [![B 张量工作室](examples/previous/b-tensor-studio.jpg)](examples/previous/b-tensor-studio.mp4) | [![C 论文证据导览](examples/previous/c-research-editorial.jpg)](examples/previous/c-research-editorial.mp4) |
| Manim 矢量对象，逐步解释特征、卷积与递归状态。 | Remotion 斜投影特征平面，突出通道与动作卷积。 | 围绕原 Fig. 3 定位机制，再看 Table II 的实验结果。 |
| [播放 A](examples/previous/a-paper-schematic.mp4) | [播放 B](examples/previous/b-tensor-studio.mp4) | [播放 C](examples/previous/c-research-editorial.mp4) |

论文：Zhenjia Xu、Jiajun Wu、Andy Zeng、Joshua B. Tenenbaum、Shuran Song，[*DensePhysNet: Learning Dense Physical Object Representations via Multi-step Dynamic Interactions*](https://arxiv.org/abs/1906.03853)，RSS 2019。A、B 的特征与运动场为讲解示意；C 包含署名的原图、原表摘引。

## 许可与素材

原创 prompts、文档和代码采用 [MIT License](LICENSE)。视频、封面以及其中的论文图表、人物照片、音乐和模型生成音频分别适用其来源条件，详见 [第三方素材与音频说明](THIRD_PARTY.md)。

六段样片的旁白由 **Breeze TTS 2** 本地生成，用于研究和非商业展示。该模型的本地输出适用研究与非商业许可；代码的 Apache-2.0 许可不覆盖这些输出。[Breeze TTS 2 官方许可](https://huggingface.co/BreezeBlue/Breeze-TTS-2/blob/main/LICENSE)
