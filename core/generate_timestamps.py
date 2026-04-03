import argparse
import json
import sys
from pathlib import Path

from pydub import AudioSegment

from scene_schema import SceneSpec


def load_scene(scene_path: Path) -> SceneSpec:
    with scene_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return SceneSpec(**raw)


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_segment_dir(scene: SceneSpec, repo_root: Path) -> Path:
    return (
        repo_root
        / "courses"
        / "machine-learning"
        / "generated"
        / "audio_segments"
        / scene.scene_id
    )


def get_timestamp_path(scene: SceneSpec, repo_root: Path) -> Path:
    out_dir = (
        repo_root
        / "courses"
        / "machine-learning"
        / "generated"
        / "timestamps"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{scene.scene_id}.json"


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
        help="Overwrite timestamp file if it already exists",
    )
    parser.add_argument(
        "--gap-ms",
        type=int,
        default=250,
        help="Gap in milliseconds inserted between segments during concat",
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    scene_path = Path(args.scene).resolve()

    if not scene_path.exists():
        print(f"Scene file not found: {scene_path}")
        sys.exit(1)

    scene = load_scene(scene_path)
    seg_dir = get_segment_dir(scene, repo_root)
    out_path = get_timestamp_path(scene, repo_root)

    if not seg_dir.exists():
        print(f"Segment directory not found: {seg_dir}")
        sys.exit(1)

    if out_path.exists() and not args.force:
        print(f"Timestamp file already exists: {out_path}")
        print("Use --force to overwrite.")
        sys.exit(0)

    timeline = []
    current_time = 0.0
    gap_sec = args.gap_ms / 1000.0

    print(f"Scene: {scene.scene_id}")
    print(f"Segment dir: {seg_dir}")
    print(f"Output file: {out_path}")
    print(f"Gap: {args.gap_ms} ms")
    print()

    for i, segment in enumerate(scene.narration):
        seg_path = seg_dir / f"{segment.id}.wav"

        if not seg_path.exists():
            print(f"Missing segment file: {seg_path}")
            sys.exit(1)

        audio = AudioSegment.from_file(seg_path, format="wav")
        duration = len(audio) / 1000.0

        start = current_time
        end = start + duration

        timeline.append({
            "id": segment.id,
            "text": segment.text,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(duration, 3)
        })

        print(f"{segment.id}: {start:.3f}s -> {end:.3f}s ({duration:.3f}s)")

        current_time = end
        if i < len(scene.narration) - 1:
            current_time += gap_sec

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)

    print()
    print(f"Timestamps written to: {out_path}")
    print(f"Total timeline duration: {current_time:.3f}s")


if __name__ == "__main__":
    main()