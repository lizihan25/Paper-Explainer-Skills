"""Generate local narration with a stable synthetic voice and explicit processing."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time

from configuration import load_config

SKILL = Path(__file__).resolve().parents[1]
DLL_HANDLES = []


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configure(cfg, output=None):
    env = Path(cfg["python"]).parent
    os.environ["PATH"] = os.pathsep.join([str(env), str(env / "Library/bin"), str(env / "Scripts"), os.environ["PATH"]])
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "HF_HUB_DISABLE_IMPLICIT_TOKEN", "PYTHONDONTWRITEBYTECODE"):
        os.environ[key] = "1"
    if output is not None:
        os.environ["NUMBA_CACHE_DIR"] = str(output / "cache/numba")
        os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(output / "cache/torch")
    if os.name == "nt":
        DLL_HANDLES.append(os.add_dll_directory(str(env / "Library/bin")))


def preflight(cfg, engine, need_subtitles=True):
    spec = cfg["engines"][engine]
    paths = {"python": Path(cfg["python"]), "ffmpeg": Path(cfg["ffmpeg"]),
             "repository": Path(spec["repository"]), "model": Path(spec["model"]),
             "reference": Path(cfg["reference"]["audio"])}
    if engine == "index":
        paths.update({key: Path(value) for key, value in spec["aux_paths"].items()})
    snapshots = Path(cfg["subtitles"]["asr_cache"]) / "models--Systran--faster-whisper-small.en/snapshots"
    if need_subtitles and not any((path / "model.bin").is_file() for path in snapshots.glob("*")):
        raise FileNotFoundError("Local subtitle ASR model missing; review the subtitle configuration.")
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing local resources: " + "; ".join(missing))
    if Path(sys.executable).resolve() != paths["python"].resolve():
        raise RuntimeError("Run with the Python executable selected in the configuration.")
    if digest(paths["reference"]) != cfg["reference"]["sha256"]:
        raise RuntimeError("Reference identity changed; update the selected reference explicitly.")
    import torch
    import soundfile
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable. Check the existing environment before generating.")
    torch.set_num_threads(4)
    info = soundfile.info(paths["reference"])
    return {"engine": engine, "python": sys.executable, "torch": torch.__version__,
            "cuda_device": torch.cuda.get_device_name(0), "reference_sha256": digest(paths["reference"]),
            "reference_sample_rate": info.samplerate, "reference_seconds": info.duration,
            "default_speed": cfg["processing"]["speed"], "resources_present": True}


def load_breeze(cfg):
    spec = cfg["engines"]["breeze"]
    sys.path.insert(0, spec["repository"])
    from breeze_infer.runtime import load_runtime, update_generation_config_for_breeze, set_all_seeds
    from breeze_infer.templates import prepare_inputs, get_template
    import models.fast_streaming as streaming
    from models.cudagraph.depth_decoder_graph import DepthDecoderGraph

    class WindowsDepthGraph(DepthDecoderGraph):
        def __init__(self, *args, **kwargs):
            kwargs["fast"] = False
            super().__init__(*args, **kwargs)

    streaming.DepthDecoderGraph = WindowsDepthGraph
    tokenizer, model, codec = load_runtime(Path(spec["model"]), device="cuda:0", attn_implementation="eager")
    update_generation_config_for_breeze(model)
    settings = streaming.FastStreamingConfig(**spec["streaming"])
    runtime = streaming.FastBreezeStreamingRuntime(model, codec, settings, tokenizer=tokenizer)

    def synthesize(text, raw_path, identity):
        import numpy as np
        import soundfile as sf
        request = {"id": identity, "speaker": "S0", "text": text,
                   "ref_audio_path": cfg["reference"]["audio"],
                   "ref_text": cfg["reference"]["text"]}
        inputs = prepare_inputs(tokenizer, codec, model, [request], get_template(spec["mode"]),
                                guidance_scale=spec["guidance_scale"], guidance_scale_ref=None, guidance_scale_ins=None)
        set_all_seeds(cfg["seed"])
        chunks = [chunk.audio for chunk in runtime.iter_audio_chunks(inputs, request_id=identity, seed=cfg["seed"])]
        if not chunks:
            raise RuntimeError("Engine produced no audio.")
        data = np.concatenate(chunks).reshape(-1)
        if not np.isfinite(data).all():
            raise RuntimeError("Engine produced non-finite audio.")
        sf.write(raw_path, data, runtime.sample_rate, subtype="FLOAT")

    return synthesize


def load_index(cfg):
    spec = cfg["engines"]["index"]
    repo = Path(spec["repository"])
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(repo / "vendor_runtime"))
    from indextts.infer_v2 import IndexTTS2
    model = Path(spec["model"])
    tts = IndexTTS2(cfg_path=str(model / "config.yaml"), model_dir=str(model), device="cuda:0",
                    use_fp16=True, use_cuda_kernel=False, use_deepspeed=False,
                    use_qwen_emo=False, aux_paths=spec["aux_paths"])

    def synthesize(text, raw_path, identity):
        import numpy as np
        import torch
        random.seed(cfg["seed"])
        np.random.seed(cfg["seed"])
        torch.manual_seed(cfg["seed"])
        tts.infer(spk_audio_prompt=cfg["reference"]["audio"], text=text,
                  output_path=str(raw_path), max_text_tokens_per_segment=200,
                  interval_silence=200, use_random=False, verbose=False, **spec["sampling"])

    return synthesize


def process_audio(cfg, raw_path, chunk_path, speed):
    import numpy as np
    import soundfile as sf
    ffmpeg = cfg["ffmpeg"]
    speed_path = chunk_path.with_name(chunk_path.stem + "_speed.wav")
    subprocess.run([ffmpeg, "-v", "error", "-n", "-i", str(raw_path), "-af", f"atempo={speed:.8g}",
                    "-ar", "24000", "-ac", "1", "-c:a", "pcm_f32le", str(speed_path)], check=True)
    proc = cfg["processing"]
    measure = subprocess.run([ffmpeg, "-hide_banner", "-i", str(speed_path), "-af",
                              f'loudnorm=I={proc["target_lufs"]}:TP={proc["true_peak_db"]}:print_format=json',
                              "-f", "null", "-"], capture_output=True, text=True, check=True)
    stats = json.JSONDecoder().raw_decode(measure.stderr[measure.stderr.rfind("{"):])[0]
    loudness, true_peak = float(stats["input_i"]), float(stats["input_tp"])
    if not math.isfinite(loudness) or not math.isfinite(true_peak):
        raise RuntimeError("Silent or invalid generation; inspect the raw audio.")
    gain_db = min(proc["target_lufs"] - loudness, proc["true_peak_db"] - true_peak)
    subprocess.run([ffmpeg, "-v", "error", "-n", "-i", str(speed_path), "-af", f"volume={gain_db:.8f}dB",
                    "-c:a", "pcm_s24le", str(chunk_path)], check=True)
    audio, sr = sf.read(chunk_path, dtype="float32")
    if not np.isfinite(audio).all() or np.max(np.abs(audio)) >= 1:
        raise RuntimeError("Non-finite or clipped processed audio.")
    return audio, sr, {"input_lufs_after_speed": loudness, "input_true_peak_db_after_speed": true_peak,
                       "fixed_gain_db": gain_db, "peak": float(np.max(np.abs(audio))),
                       "duration_seconds": len(audio) / sr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Private JSON configuration; otherwise LOCAL_NARRATION_CONFIG or config/local.json")
    parser.add_argument("--resolve-config", action="store_true", help="Print resolved configuration without importing or loading audio models")
    parser.add_argument("--check", action="store_true", help="Check local resources and CUDA without loading the TTS model")
    parser.add_argument("--engine", choices=("breeze", "index"), default="breeze")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--audio-only", action="store_true", help="Explicitly omit subtitles; allow plain UTF-8 text input")
    args = parser.parse_args()
    cfg, config_path = load_config(args.config)
    if args.resolve_config:
        print(json.dumps({"config_file": str(config_path), "configuration": cfg}, ensure_ascii=False, indent=2))
        return
    speed = cfg["processing"]["speed"] if args.speed is None else args.speed
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        parser.error("Speed must be between 0.5 and 2.0.")
    configure(cfg)
    environment = preflight(cfg, args.engine, need_subtitles=not args.audio_only)
    if args.check:
        print(json.dumps(environment, ensure_ascii=False), flush=True)
        return
    if args.input is None or args.output is None:
        parser.error("Generation requires --input and --output.")
    source = args.input.read_text(encoding="utf-8-sig").strip()
    bilingual = None
    if args.input.suffix.lower() == ".json":
        bilingual = json.loads(source)
        rows = bilingual.get("sentences", [])
        if not rows or any(not str(row.get("en", "")).strip() for row in rows):
            parser.error("JSON requires a nonempty sentences array with English text.")
        if not args.audio_only and any(not str(row.get("zh", "")).strip() for row in rows):
            parser.error("Bilingual subtitles require the corresponding Chinese text in every row.")
        groups = []
        seen = set()
        previous = None
        for row in rows:
            key = row.get("paragraph", 1)
            if key != previous:
                if key in seen:
                    parser.error("Keep each paragraph's caption rows consecutive.")
                seen.add(key)
                groups.append([])
                previous = key
            groups[-1].append(row)
        paragraphs = [" ".join(row["en"].strip() for row in group) for group in groups]
    else:
        if not args.audio_only:
            parser.error("Default delivery includes bilingual subtitles. Use a bilingual JSON script, or explicitly select --audio-only for TXT input.")
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", source) if p.strip()]
    if not paragraphs:
        parser.error("The input script is empty.")
    for index, paragraph in enumerate(paragraphs, 1):
        if len(paragraph.split()) > cfg["max_words_per_paragraph"]:
            parser.error(f"Paragraph {index} is too long for the configured capacity. Split at a complete idea or review capacity settings.")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Choose a new or empty output directory; existing audio is preserved.")
    output.mkdir(parents=True, exist_ok=True)
    configure(cfg, output)
    (output / "script-original.txt").write_text("\n\n".join(paragraphs), encoding="utf-8")
    if bilingual is not None:
        save(output / "script-bilingual.json", bilingual)
    spoken = []
    for paragraph in paragraphs:
        for original, pronunciation in cfg["pronunciations"].items():
            paragraph = paragraph.replace(original, pronunciation)
        spoken.append(paragraph)
    (output / "script-spoken.txt").write_text("\n\n".join(spoken), encoding="utf-8")
    manifest = {"status": "generating", "engine": args.engine, "speed": speed,
                "environment": environment, "configuration": cfg, "paragraphs": [],
                "quality_scope": "Signal checks only; word completeness and listening remain separate.",
                "music": False, "subtitles": not args.audio_only}
    save(output / "run.json", manifest)
    started = time.monotonic()
    try:
        import numpy as np
        import soundfile as sf
        synthesize = load_breeze(cfg) if args.engine == "breeze" else load_index(cfg)
        sr = 24000
        assembled = [np.zeros(round(cfg["processing"]["leading_silence_seconds"] * sr), dtype="float32")]
        cursor = len(assembled[0]) / sr
        for index, text in enumerate(spoken, 1):
            raw_path = output / f"raw_{index:04d}.wav"
            chunk_path = output / f"chunk_{index:04d}.wav"
            synthesize(text, raw_path, f"narration-{index:04d}")
            audio, sample_rate, stats = process_audio(cfg, raw_path, chunk_path, speed)
            assert sample_rate == sr
            manifest["paragraphs"].append({"index": index, "original": paragraphs[index - 1], "spoken": text,
                                           "start_seconds": cursor, "end_seconds": cursor + len(audio) / sr,
                                           "raw_file": raw_path.name, "processed_file": chunk_path.name, **stats})
            assembled.append(audio)
            cursor += len(audio) / sr
            gap = cfg["processing"]["gap_seconds"] if index < len(spoken) else cfg["processing"]["trailing_silence_seconds"]
            assembled.append(np.zeros(round(gap * sr), dtype="float32"))
            cursor += len(assembled[-1]) / sr
            save(output / "run.json", manifest)
            print(f"Completed paragraph {index}/{len(spoken)}", flush=True)
        final = np.concatenate(assembled)
        sf.write(output / "narration.wav", final, sr, subtype="PCM_24")
        manifest.update(status="audio_completed", duration_seconds=len(final) / sr,
                        generation_seconds=time.monotonic() - started, sample_rate=sr,
                        narration_sha256=digest(output / "narration.wav"))
        save(output / "run.json", manifest)
        if not args.audio_only:
            subprocess.run([sys.executable, "-B", "-X", "utf8", str(SKILL / "scripts/subtitles.py"),
                            "--run", str(output)], check=True)
            manifest["subtitles_status"] = "aligned"
        manifest["status"] = "completed"
        print(json.dumps({"status": "completed", "output": str(output / "narration.wav"),
                          "duration_seconds": manifest["duration_seconds"], "speed": speed}), flush=True)
    except Exception as exc:
        manifest.update(status="audio_completed_subtitles_need_review" if manifest["status"] == "audio_completed" else "failed",
                        error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        save(output / "run.json", manifest)


if __name__ == "__main__":
    main()
