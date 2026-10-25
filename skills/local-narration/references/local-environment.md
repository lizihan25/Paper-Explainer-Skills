# 配置本机环境与音质

## 路径配置

公开版本只提供 [config/example.json](../config/example.json)。复制为 `config/local.json`，填入已有 Python、FFmpeg、两套引擎源码/模型、Index 辅助模型及 small.en ASR 缓存的实际位置。私有 `local.json` 已被本 skill 的 `.gitignore` 排除；分享生成的 `run.json` 前也需处理其中的本机路径。

配置选择顺序为 `--config`、环境变量 `LOCAL_NARRATION_CONFIG`、skill 内 `config/local.json`。配置中的所有相对路径以**该配置文件的目录**为基准，包含 `reference.audio`；随包 F 的默认值是 `../assets/reference_F.wav`。支持 `~`、`${NAME}`、`$NAME` 与 `%NAME%`，缺少环境变量时明确报错，不会把未展开的变量当作文件名。

示例中的环境变量是可选写法，可直接换成绝对路径或配置目录的相对路径：

| 变量 | 指向 |
| --- | --- |
| `NARRATION_PYTHON` | 已安装依赖的 Python 可执行文件 |
| `NARRATION_FFMPEG` | FFmpeg 可执行文件 |
| `NARRATION_TTS_ROOT` | 含 `repos/breeze-tts`、`repos/index-tts`、`models/Breeze-TTS-2`、`models/IndexTTS-2` 的现有目录 |
| `NARRATION_ASR_CACHE` | 含 `models--Systran--faster-whisper-small.en/snapshots/<revision>/model.bin` 的现有缓存目录 |

其他目录结构可直接分别修改 `engines.*.repository`、`engines.*.model` 和 `aux_paths`。公开包不包含模型、环境、下载器或自动安装步骤。

## 运行

在已有配音环境中，以下命令从 skill 目录运行；也可把脚本、输入和输出换为绝对路径。Python 必须与配置一致。

```powershell
Copy-Item -LiteralPath './config/example.json' -Destination './config/local.json'
# Set existing resource paths in config/local.json before continuing.
python -B -X utf8 ./scripts/narrate.py --resolve-config
python -B -X utf8 ./scripts/narrate.py --check --engine breeze
python -B -X utf8 ./scripts/narrate.py --input ./examples/script-bilingual.json --output ./outputs/run-01 --engine breeze --speed 1.1
```

已有 `local.json` 时保留它，不再运行复制行。`--resolve-config` 只解析路径，不导入音频库、不加载模型、不要求资源存在。`--check` 检查已有资源、参考音频身份、Python 与 CUDA；它不证明第三方推理接口兼容。`--config <文件>` 可切换到其他本机配置。默认 Breeze，`--engine index` 使用同一 F 参考。输出使用新目录；仅音频任务用 `--audio-only`，此时可输入空行分段的 UTF-8 TXT。

默认输入为双语 JSON，见 [示例](../examples/script-bilingual.json)，字幕按 `sentences` 排序，同段由 `paragraph` 标识。每个输出目录包含原始 `raw_*.wav`、处理后 `chunk_*.wav`、拼接 `narration.wav`、原文/发音文本及 `run.json`。Breeze 原稿保存为浮点 WAV；Index 保留原始输出格式，后续转换不会恢复已损失的精度。

## 字幕

使用本地 small.en ASR，从变速后的实际片段取得词时序。英文内容核对通过后导出双语、英文、中文 SRT 和双语 ASS。展示原文与给定中文保持不变，发音替换单独保存。ASS 为 1920×1080 画布，微软雅黑，中文 42、英文 32、底部居中，中文在上；目标电脑缺少该字体时选择已安装的中文字体，目标尺寸改变时检查缩放和遮挡。SRT 字体由播放器或视频工程决定。

ASR 在独立 CPU 进程运行，Windows 使用既有 NumPy/OpenMP 兼容方式。识别、差异和起止时间保留在 `alignment.json`。内容或时间不匹配时保留音频与差异，暂不导出字幕；核查后运行 `scripts/subtitles.py --run <输出目录>`。速度或剪辑改变后重新对齐。

2026-10-25 本机验证的 FFmpeg 没有 `ass` 滤镜；字幕侧车文件已验证，预览采用 Pillow 排字合成。其他电脑先核对渲染器的字体与字幕能力，再决定烧录方式；不假定所有 FFmpeg 构建都支持 `-vf ass`。

## 已验证的运行接口

2026-10-25 在维护者既有 Windows / CUDA 环境中验证过 Breeze 与 Index，均生成两段英文并导出四条双语字幕。路径可移植不代表已验证所有操作系统或任意上游版本；新电脑先检查已有环境，再做短段实际生成。

Breeze 适配当前本地 `breeze_infer.runtime`、`FastBreezeStreamingRuntime` 等接口：eager attention，关闭 backbone decode 加速，并将 `DepthDecoderGraph.fast` 设为 false。参考为 F 完整三句、24 kHz 单声道，CFG 1 用于参考克隆；最初声线设计的 CFG 4 不作为生产克隆参数。

Index 适配本地 `indextts.infer_v2.IndexTTS2`，需要现有 `vendor_runtime` 与 `aux_paths` 参数支持；并非保证任意未修改的上游 checkout 可直接替换。使用 fp16，关闭自定义 CUDA kernel、DeepSpeed 和 Qwen 情绪模型。接口不一致时先对照已有调用链，再做最小适配。

Numba/Torch 缓存在每次输出目录中，离线变量在加载模型前设置，不下载新模型。默认 CUDA，不可用时报告环境问题。更换引擎或参考要重新试听跨段音色。

## 声线、速度和使用条件

固定 F 是用 Breeze TTS 2 生成的合成声线，不对应特定真人。普通生产使用同一参考 WAV 与完整转录，不每段重新设计声音；seed 相同不保证音色完全一致。用户试听曾反馈 F 的沙沙感更少，这不代替新音频的实际试听。

默认对未变速原稿做一次 `atempo=1.1`。用户已反馈 1.25 太快。既有 1.25 成片优先从原稿重做；只剩提速音轨时换算为 `1.1/1.25=0.88`，再重新检查字幕时间。默认使用保留峰值余量的固定增益，目标约 −23 LUFS、真峰值上限 −1.5 dBTP；余量不足时接受较低响度。

参考音频的来源、完整转录、SHA256 和限制见 [素材说明](../assets/NOTICE.md)。Breeze 本地模型及输出带研究与非商业使用条件；切换 Index 不会消除输入参考的条件。发布用途改变时查阅所用版本许可，包内副本不代表上游未来版本。

官方来源：[Breeze 推理仓库](https://github.com/breezeblue-ai/breeze-tts)、[Breeze 模型](https://huggingface.co/BreezeBlue/Breeze-TTS-2)、[IndexTTS](https://github.com/index-tts/index-tts)。
