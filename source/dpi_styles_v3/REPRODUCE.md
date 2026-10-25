# A 版预览：持续原图定位

本版将完整方法图固定在右上角。主区解释粒子状态、图结构、消息传播、层级和控制，红框用 0.85 秒平滑过渡定位原图模块。总览保持固定，原图控制面板在主区另行放大。画面原生 1920×1080、60 fps；总时长 53.500 秒。

默认风格为 A（机制动画与持续原图定位）→ C（自由画布）→ B（原图局部导览）。本片是 DPI-Net 方法片段，未扩展成完整实验综述。

## 可修改内容

- `render_preview.py`：渲染画面；图像目录、输出目录和 FFmpeg 均为命令行参数。字体目录用 `FONT_DIR` 环境变量配置，默认系统 Windows 字体目录。
- `prepare_audio.py`：从既有未变速连续 F 配音生成 1.1 倍版本，按实际变速后音轨做 ASR 词时间对齐，生成新的 78 BPM 配乐与混音。不会重新生成声线。
- `script.timed.json`：英文讲稿、中文翻译、镜头与实际时间。三份 SRT 同源。
- `check_camera.py`：针对旧 B 版的 12–14.5 秒生成连续采样诊断片段；不是完整 B 版。

Python 依赖：Pillow、NumPy、SoundFile、SciPy、faster-whisper；渲染使用已有 FFmpeg。ASR 指向已经下载的 faster-whisper-small.en 模型目录，程序不会下载模型。Windows 环境的 FFmpeg/音视频 DLL 目录在当前子进程中配置。

```powershell
& $python .\prepare_audio.py --source-project $previousProject --ffmpeg $ffmpeg --asr-model $localWhisperModel --output $outputDirectory
& $python .\render_preview.py --assets $figureDirectory --ffmpeg $ffmpeg --output $outputDirectory
```

`$previousProject` 需要包含未变速的 `audio/narration_raw.wav` 和 `styles/script.json`。`$figureDirectory` 需要 `dpi_net_method.png`；`yunzhu-li.jpg` 为可选身份照片。纸图与照片来源见 `sources.json`，公开工程不附第三方原始素材。新项目可先用 `local-narration` 生成自己的旁白，再用本图形逻辑和时间轴组织画面。

## 配音、字幕与检查

固定合成 F 声线沿用旧连续录音，对未变速音频只应用一次 `atempo=1.1`。恒定增益、旁白下压低配乐 5 dB，中上英下字幕。配乐是同一项目原创的 Particle Study 01，按新时长重新生成，不是更早被否定的曲目。

`asr.json` 保留本次 ASR 原始结果。DPI Net 的拆词不改变内容；`cluster routes` 对应原稿和原论文的 `cluster roots`，本片记录了一处可复查的同音拼写修正，详见 `alignment.json`。该项不是 ASR 原文完全一致的证明。时间轴来自实际 1.1 倍音轨，未直接等比缩放旧字幕。

`verification.json` 记录解码参数、关键帧、字幕范围与定位框连续性。声音自然度仍需实际试听判断，ASR 不能代替听感评价。

## B 版抖动诊断的范围

旧 B 版在浮点裁切后再次把缩放尺寸与粘贴位置取整；每段缩放从约 1.02 回到 0.92，存在约 9.8% 的段间回缩。实际旧片 12.28–14 秒抽帧保留在本地 QA 中。修正版直接从完整原图用浮点相机做一次仿射采样，固定段间倍率，并以 60 fps 编码。`camera_diagnosis.json` 记录这些已确认的问题；它们不能被表述为所有主观抖动的唯一原因。

只渲染了一版完整 A 预览与 2.5 秒 B 诊断片，旧视频保持原样。
