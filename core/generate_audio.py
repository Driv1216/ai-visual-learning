import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

from scene_schema import SceneSpec


API_URL = "https://api.sarvam.ai/text-to-speech"
DEFAULT_TIMEOUT = 90


def load_scene(scene_path: Path) -> SceneSpec:
    with scene_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return SceneSpec(**raw)


def get_api_key() -> str:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise ValueError(
            "SARVAM_API_KEY is not set.\n\n"
            "PowerShell:\n"
            '  $env:SARVAM_API_KEY="your_key_here"\n'
            "  python core/generate_audio.py --scene <scene_path>\n"
        )
    return api_key


def scene_output_dir(scene: SceneSpec, repo_root: Path) -> Path:
    return (
        repo_root
        / "courses"
        / "machine-learning"
        / "generated"
        / "audio_segments"
        / scene.scene_id
    )


def synthesize_segment(
    api_key: str,
    text: str,
    language: str,
    speaker: str,
    model: str,
) -> bytes:
    cleaned = " ".join(text.split()).strip()

    payload = {
        "text": cleaned,
        "target_language_code": language,
        "speaker": speaker,
        "model": model,
    }

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json",
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Sarvam API error {response.status_code}: {response.text}"
        )

    data = response.json()

    if "audios" not in data or not data["audios"]:
        raise RuntimeError(f"Unexpected Sarvam response: {data}")

    audio_b64 = data["audios"][0]
    audio_bytes = base64.b64decode(audio_b64)

    # Validate WAV header: RIFF....WAVE
    if not audio_bytes.startswith(b"RIFF") or audio_bytes[8:12] != b"WAVE":
        raise RuntimeError("Invalid WAV data received from API")

    return audio_bytes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scene",
        required=True,
        help="Path to scene JSON file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output files already exist",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Pause between API requests in seconds",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    scene_path = Path(args.scene).resolve()

    if not scene_path.exists():
        print(f"Scene file not found: {scene_path}")
        sys.exit(1)

    scene = load_scene(scene_path)
    api_key = get_api_key()

    out_dir = scene_output_dir(scene, repo_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scene: {scene.scene_id}")
    print(f"Output dir: {out_dir}")
    print(f"Narration segments: {len(scene.narration)}")
    print("Voice config:")
    print(f"  Language: {scene.voice.language}")
    print(f"  Speaker : {scene.voice.speaker}")
    print(f"  Model   : {scene.voice.model}")
    print()

    ok_count = 0

    for segment in scene.narration:
        out_path = out_dir / f"{segment.id}.wav"

        if out_path.exists() and not args.force:
            print(f"[SKIP] {segment.id} -> {out_path.name}")
            ok_count += 1
            continue

        print(f"[GEN ] {segment.id} ({len(segment.text)} chars)")

        last_error = None
        for attempt in range(3):
            try:
                audio_bytes = synthesize_segment(
                    api_key=api_key,
                    text=segment.text,
                    language=scene.voice.language,
                    speaker=scene.voice.speaker,
                    model=scene.voice.model,
                )

                with out_path.open("wb") as f:
                    f.write(audio_bytes)

                print(f"[ OK ] {segment.id} -> {out_path.name}")
                ok_count += 1
                last_error = None
                break

            except Exception as e:
                last_error = e
                print(f"[TRY ] {segment.id} attempt {attempt + 1}/3 failed: {e}")
                time.sleep(1.0)

        if last_error is not None:
            print(f"[FAIL] {segment.id}: {last_error}")
            sys.exit(1)

        time.sleep(args.sleep)

    print()
    print(f"Generated {ok_count}/{len(scene.narration)} segment files.")


if __name__ == "__main__":
    main()