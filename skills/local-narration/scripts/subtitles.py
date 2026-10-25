"""Align bilingual captions to actual processed chunks using local English ASR."""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import re
import sys


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def spoken(text, cfg):
    for original, pronunciation in cfg["pronunciations"].items():
        text = text.replace(original, pronunciation)
    return text


def tokens(text, cfg):
    text = text.lower()
    for variants in cfg["subtitles"]["aliases"]:
        canonical = variants[0]
        for variant in sorted(variants, key=len, reverse=True):
            text = re.sub(r"(?<!\w)" + re.escape(variant.lower()) + r"(?!\w)", canonical.lower(), text)
    return re.findall(r"[a-z0-9]+", text)


def stamp(seconds, ass=False):
    units = round(seconds * (100 if ass else 1000))
    scale = 100 if ass else 1000
    return f"{units // (3600 * scale):01d}" + f":{units // (60 * scale) % 60:02d}:{units // scale % 60:02d}" + (f".{units % scale:02d}" if ass else f",{units % scale:03d}")


def export(cues, output):
    for language in ("en", "zh", "bilingual"):
        blocks = []
        for index, cue in enumerate(cues, 1):
            text = cue["zh"] + "\n" + cue["en"] if language == "bilingual" else cue[language]
            # SRT hours convention uses two digits.
            start, end = stamp(cue["start"]).zfill(12), stamp(cue["end"]).zfill(12)
            blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
        (output / f"subtitles.{language}.srt").write_text("\n".join(blocks), encoding="utf-8-sig")
    header = """[Script Info]
Title: Local bilingual narration
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,42,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,0,0,0,0,100,100,0,0,1,2,1,2,90,90,54,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def escape(text):
        return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")

    lines = [header]
    for cue in cues:
        text = escape(cue["zh"]) + r"\N{\fs32\c&H00E0E0E0&}" + escape(cue["en"])
        lines.append(f'Dialogue: 0,{stamp(cue["start"], True)},{stamp(cue["end"], True)},Default,,0,0,0,,{text}\n')
    (output / "subtitles.bilingual.ass").write_text("".join(lines), encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    output = args.run.resolve()
    run = json.loads((output / "run.json").read_text(encoding="utf-8"))
    cfg = run["configuration"]
    env = Path(cfg["python"]).parent
    os.environ["PATH"] = str(env / "Library/bin") + os.pathsep + os.environ["PATH"]
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    handles = [os.add_dll_directory(str(env / "Library/bin"))] if os.name == "nt" else []
    import numpy as np
    from faster_whisper import WhisperModel
    snapshots = Path(cfg["subtitles"]["asr_cache"]) / "models--Systran--faster-whisper-small.en/snapshots"
    candidates = sorted(path for path in snapshots.glob("*") if (path / "model.bin").is_file())
    if not candidates:
        raise FileNotFoundError("Local small.en ASR model missing; configure an existing local model.")
    model = WhisperModel(str(candidates[-1]), device="cpu", compute_type="int8", cpu_threads=4, local_files_only=True)
    if sys.platform == "win32":
        class DirectMelFilters(np.ndarray):
            def __matmul__(self, other):
                return np.einsum("ij,jk->ik", np.asarray(self), other, optimize=False)
        model.feature_extractor.mel_filters = model.feature_extractor.mel_filters.view(DirectMelFilters)
    script = json.loads((output / "script-bilingual.json").read_text(encoding="utf-8"))
    groups = []
    previous = None
    for row in script["sentences"]:
        key = row.get("paragraph", 1)
        if key != previous:
            groups.append([])
            previous = key
        groups[-1].append(row)
    if len(groups) != len(run["paragraphs"]):
        raise ValueError("Caption groups do not match generated audio paragraphs.")
    report = {"status": "aligning", "engine": "local faster-whisper-small.en CPU/int8",
              "source": "Actual processed audio chunks after speed adjustment", "paragraphs": [], "cues": []}
    problems = []
    for paragraph, rows in zip(run["paragraphs"], groups):
        segments, _ = model.transcribe(str(output / paragraph["processed_file"]), language="en", word_timestamps=True,
                                       beam_size=5, temperature=0, condition_on_previous_text=False, vad_filter=False)
        segments = list(segments)
        words = [{"word": word.word, "start": word.start, "end": word.end}
                 for segment in segments for word in segment.words or []]
        observed, owners = [], []
        for index, word in enumerate(words):
            normalized = tokens(word["word"], cfg)
            observed.extend(normalized)
            owners.extend([index] * len(normalized))
        expected, bounds = [], []
        for row in rows:
            normalized = tokens(spoken(row["en"], cfg), cfg)
            bounds.append((len(expected), len(expected) + len(normalized)))
            expected.extend(normalized)
        comparison = SequenceMatcher(a=expected, b=observed, autojunk=False)
        differences = [{"operation": op, "expected": expected[a:b], "observed": observed[c:d]}
                       for op, a, b, c, d in comparison.get_opcodes() if op != "equal"]
        item = {"paragraph": paragraph["index"], "recognized": " ".join(s.text.strip() for s in segments),
                "words": words, "differences": differences, "exact_normalized_match": expected == observed}
        report["paragraphs"].append(item)
        if differences:
            problems.append(f'Paragraph {paragraph["index"]}: content mismatch; inspect raw ASR and actual audio.')
            continue
        for row, (start, end) in zip(rows, bounds):
            if end <= start:
                problems.append("Empty caption token range.")
                continue
            first, last = words[owners[start]], words[owners[end - 1]]
            if last["end"] <= first["start"]:
                problems.append("Invalid ASR caption time range.")
                continue
            report["cues"].append({"en": row["en"], "zh": row["zh"],
                                  "start": max(paragraph["start_seconds"], paragraph["start_seconds"] + first["start"] - .035),
                                  "end": min(paragraph["end_seconds"], paragraph["start_seconds"] + last["end"] + .08)})
        save(output / "alignment.json", report)
    cues = report["cues"]
    for index in range(len(cues) - 1):
        cues[index]["end"] = min(cues[index]["end"], cues[index + 1]["start"])
    if any(cue["end"] <= cue["start"] or cue["start"] < 0 or cue["end"] > run["duration_seconds"] + .001 for cue in cues):
        problems.append("Subtitle timing is nonmonotonic or outside the final audio.")
    report.update(status="needs_review" if problems else "aligned", problems=problems)
    save(output / "alignment.json", report)
    if problems:
        raise RuntimeError("Subtitle alignment requires review; see alignment.json. Audio files are retained.")
    export(cues, output)
    print(json.dumps({"subtitles": "aligned", "cues": len(cues), "order": "Chinese above English"}), flush=True)


if __name__ == "__main__":
    main()
