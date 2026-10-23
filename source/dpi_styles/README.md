# 重建 DPI-Net 三种视觉片段

渲染器用 Pillow 绘制确定性画面，经 FFmpeg 输出 1280×720、24 fps 的无声视频。三个风格共享讲稿与时间轴；输出包含中上英下字幕。成片的统一配音和 BGM 另行混入。

独立字幕也随源码提供：[中英双语](subtitles/bilingual.srt)、[英文](subtitles/en.srt)、[中文](subtitles/zh.srt)。最终时间轴为 47.208333 秒。`voice_configuration.json`、`mix_report.json` 与 `music_source.json` 记录示例的声音设置；合成参考音和模型权重另行准备。

需要 Python 3、Pillow 与可用的 FFmpeg。在本目录运行：

```sh
python -m pip install Pillow
python fetch_assets.py
```

下载脚本从[作者项目页](https://dpi.csail.mit.edu/)获取图 1，从 [Yunzhu Li 个人主页](https://yunzhuli.github.io/)获取头像，供本地重建使用。素材保留原有权利，下载目录已从源码版本管理中排除。

图 4 需自行从[论文](https://arxiv.org/pdf/1810.01566)准备完整图面，保存为 `assets/dpi_net_fig4.png`。此渲染器使用 **1836×1230** 图像坐标，并从底部截取 (c) 的真实泡沫操作行；裁切应包含完整图 4、三个子图行与边缘，字体与布局须与原图对应。若手头裁图边界不同，请同时调整 `render.py` 中 `RESULT.crop(...)` 的坐标。也可通过 `python fetch_assets.py --figure4 my-figure4.png` 复制已准备好的同尺寸图片。原图和头像没有作为独立素材随仓库再分发。

默认在 Windows 读取已安装的 Microsoft YaHei 和 Cambria。其他系统可设置 `FONT_REGULAR`、`FONT_BOLD`、`FONT_SERIF`、`FONT_SERIF_BOLD`，分别指向带中文字形的常规/粗体字体与衬线常规/粗体字体；也可用 `FONT_DIR` 提供同名字体文件。字体文件不随仓库提供。

```sh
python render.py --stills
python render.py --style all
python render.py --style microscope --start 12 --end 17
```

`--ffmpeg` 或 `FFMPEG_BINARY` 指定 FFmpeg；`--no-subs` 关闭内嵌字幕。时间轴优先读取 `script.timed.json`，否则读取 `script.json`。图中的粒子与消息为机制示意，按原文设计解释关系。

原始图像来源见 `sources.json`。色板取自 [3b1b/manim 默认配置](https://github.com/3b1b/manim/blob/master/manimlib/default_config.yml)，保留 [3Blue1Brown 的 MIT 许可](LICENSE-3B1B.txt)。视频与声音的使用条件见仓库根目录的 [THIRD_PARTY.md](../../THIRD_PARTY.md)。
