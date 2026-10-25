# 合成参考与模型许可

`reference_F.wav` 是维护者使用本地 Breeze TTS 2 生成并选择的合成 F 声线；它是生成音频，不是模型权重，也不是真人人声录音。用途是复用同一声线完成研究与教学配音。

- 音频：24 kHz，单声道，约 13.87 秒。
- SHA256：`81ebe09bf2c693af44892b4d79c96c4ed0a6d71b27baa13fd015511766dc53f3`。
- 参考转录：Dense Phys Net builds a persistent feature map from repeated interactions. After an action, a new visual observation updates the representation. A prediction branch combines these features with the proposed action to estimate image motion.

原始声线设计用于说明来源，生产时使用固定 WAV，不逐段重新设计：

> A woman in her thirties speaking neutral American English in a comfortable lower-middle register. Her voice is clear, smooth, and fully voiced. She speaks to one colleague, with a measured conversational rhythm, small pitch movements, relaxed sentence endings, and natural brief pauses between ideas.

音频适用所用 Breeze 模型版本的研究与非商业使用条件，见 [Breeze 许可副本](LICENSE-Breeze-TTS-2.txt)。其中第 7.3 条说明生成输出的所有权不移除非商业限制。商业用途需依据对应模型版本取得适当授权；本仓库对代码或 prompt 的许可不覆盖此限制。切换配音引擎不会改变输入参考音频的使用条件。

[Index 许可副本](LICENSE-IndexTTS-2.txt) 随同保留以便第二引擎使用时核对；本包没有 Index 模型权重或 Index 生成音频。

来源：[Breeze TTS 2](https://huggingface.co/BreezeBlue/Breeze-TTS-2)、[Breeze 推理源码](https://github.com/breezeblue-ai/breeze-tts)、[IndexTTS](https://github.com/index-tts/index-tts)。许可副本来自 2026-10-25 已存在的本机模型包，适用于这些固定版本，不替代对后来版本的核查。
