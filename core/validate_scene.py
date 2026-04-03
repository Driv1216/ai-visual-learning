import json
import sys
from pathlib import Path

from scene_schema import SceneSpec


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python core/validate_scene.py <path_to_scene_json>")
        sys.exit(1)

    scene_path = Path(sys.argv[1])

    if not scene_path.exists():
        print(f"Scene file not found: {scene_path}")
        sys.exit(1)

    with scene_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    scene = SceneSpec(**raw)

    print(f"Scene '{scene.scene_id}' is valid.")
    print(f"Title: {scene.scene_title}")
    print(f"Narration segments: {len(scene.narration)}")
    print(f"Visual steps: {len(scene.visual_timeline)}")


if __name__ == "__main__":
    main()