"""Print face-detector confidence ladders for reference-set photos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = REPO_ROOT / "services" / "image-engine" / "src"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

from benchmark_reference_pairs import discover_pairs  # noqa: E402
from exam_photo.providers.mediapipe_face_detector import (  # noqa: E402
    MediapipeFaceDetector,
)


def main() -> int:
    keys = sys.argv[1:] or ["3-3", "5-1"]
    manifest = json.loads(
        (REPO_ROOT / "model-manifests/face-detector.json").read_text()
    )
    detector_path = REPO_ROOT / str(manifest["local_model_path_default"])
    detector_sha = str(manifest["sha256"])
    pairs = {
        key: input_path
        for key, input_path, _ideal_path in discover_pairs(
            Path(r"C:\Users\dmbar\Pictures\Test Images"),
            Path(r"C:\Users\dmbar\Pictures\Test Images- Ideal Outputs"),
        )
    }
    for key in keys:
        image = Image.open(pairs[key]).convert("RGB")
        print(f"{key} path={pairs[key]} size={image.size}", flush=True)
        detector = MediapipeFaceDetector(
            detector_path, detector_sha, min_detection_confidence=0.5
        )
        with detector:
            for confidence in (0.5, 0.35, 0.25, 0.15, 0.10, 0.05, 0.01):
                result = detector.detect_faces(
                    image,
                    {
                        "min_detection_confidence": confidence,
                        "max_num_faces": 10,
                    },
                )
                boxes = [
                    (
                        round(face.bounding_box.left),
                        round(face.bounding_box.top),
                        round(face.bounding_box.width),
                        round(face.bounding_box.height),
                    )
                    for face in result.detections
                ]
                scores = [round(face.confidence, 3) for face in result.detections]
                print(
                    f"  conf={confidence:.2f} count={len(result.detections)} "
                    f"scores={scores} boxes={boxes}",
                    flush=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
