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


def get_scene_audio_path(scene: SceneSpec, repo_root: Path) -> Path:
    out_dir = (
        repo_root
        / "courses"
        / "machine-learning"
        / "generated"
        / "scene_audio"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{scene.scene_id}.wav"


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
        help="Overwrite the output file if it already exists",
    )
    parser.add_argument(
        "--gap-ms",
        type=int,
        default=250,
        help="Silence gap in milliseconds between narration segments",
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    scene_path = Path(args.scene).resolve()

    if not scene_path.exists():
        print(f"Scene file not found: {scene_path}")
        sys.exit(1)

    scene = load_scene(scene_path)
    seg_dir = get_segment_dir(scene, repo_root)
    out_path = get_scene_audio_path(scene, repo_root)

    if not seg_dir.exists():
        print(f"Segment directory not found: {seg_dir}")
        sys.exit(1)

    if out_path.exists() and not args.force:
        print(f"Scene audio already exists: {out_path}")
        print("Use --force to overwrite.")
        sys.exit(0)

    print(f"Scene: {scene.scene_id}")
    print(f"Segment dir: {seg_dir}")
    print(f"Output file: {out_path}")
    print(f"Gap: {args.gap_ms} ms")
    print()

    combined = AudioSegment.silent(duration=0)
    gap = AudioSegment.silent(duration=args.gap_ms)

    missing = []
    durations = []

    for i, segment in enumerate(scene.narration):
        seg_path = seg_dir / f"{segment.id}.wav"

        if not seg_path.exists():
            missing.append(seg_path.name)
            continue

        audio = AudioSegment.from_file(seg_path, format="wav")
        combined += audio
        durations.append((segment.id, len(audio)))

        if i < len(scene.narration) - 1:
            combined += gap

    if missing:
        print("Missing segment files:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)

    combined.export(out_path, format="wav")

    total_ms = len(combined)

    print("Segment durations:")
    for seg_id, dur_ms in durations:
        print(f"  {seg_id}: {dur_ms / 1000:.2f}s")

    print()
    print(f"Final scene audio created: {out_path}")
    print(f"Total duration: {total_ms / 1000:.2f}s")


if __name__ == "__main__":
    main()