"""The two models that check what a photograph is of (DEC-133).

``YunetFaceVerifier`` is a second face detector, independent of BlazeFace,
used to confirm the subject is a real human face and to count people.
``ExplicitImageClassifier`` scores how likely an image is explicit, before an
upload is stored.

Both are optional: ``load_*`` returns ``None`` when the asset is missing, and
the caller skips the check, so a machine without the models still prepares
photographs. The deployed engine fetches them with
``scripts/download_subject_checks.py``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox

#: Longest side the image is scaled to before YuNet runs. Large enough that a
#: face filling 3% of the frame is still about 20 px, which YuNet finds.
_YUNET_MAX_SIDE = 640
#: YuNet's own floor; the rules apply their own, higher thresholds.
_YUNET_MIN_SCORE = 0.3


@dataclass(frozen=True)
class VerifiedFace:
    box: BoundingBox
    score: float


def _manifest_path(repo_root: Path, name: str) -> tuple[Path, str]:
    manifest = json.loads(
        (repo_root / "model-manifests" / name).read_text(encoding="utf-8")
    )
    return repo_root / str(manifest["local_model_path_default"]), str(
        manifest["sha256"]
    )


def _verified(path: Path, expected_sha256: str) -> bool:
    if not path.is_file():
        return False
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_sha256


class YunetFaceVerifier:
    """OpenCV's YuNet face detector, run on a downscaled copy of the image."""

    def __init__(self, model_path: Path) -> None:
        import cv2

        self._cv2 = cv2
        self._detector = cv2.FaceDetectorYN.create(
            str(model_path), "", (320, 320), _YUNET_MIN_SCORE, 0.3, 50
        )

    def detect(self, image: Image.Image) -> List[VerifiedFace]:
        rgb = np.asarray(image.convert("RGB"))
        height, width = rgb.shape[:2]
        scale = min(1.0, _YUNET_MAX_SIDE / max(height, width))
        bgr = np.ascontiguousarray(rgb[:, :, ::-1])
        if scale < 1.0:
            bgr = self._cv2.resize(
                bgr,
                (max(1, int(width * scale)), max(1, int(height * scale))),
                interpolation=self._cv2.INTER_AREA,
            )
        self._detector.setInputSize((bgr.shape[1], bgr.shape[0]))
        _, found = self._detector.detect(bgr)
        rows: Any = found if found is not None else []
        faces: List[VerifiedFace] = []
        for row in rows:
            x, y, w, h = (float(v) / scale for v in row[:4])
            faces.append(
                VerifiedFace(
                    box=BoundingBox(left=x, top=y, right=x + w, bottom=y + h),
                    score=float(row[-1]),
                )
            )
        return sorted(faces, key=lambda f: f.score, reverse=True)


class ExplicitImageClassifier:
    """ViT classifier with classes normal/nsfw; returns P(nsfw)."""

    def __init__(self, model_path: Path) -> None:
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        self._session = ort.InferenceSession(
            str(model_path), options, providers=["CPUExecutionProvider"]
        )
        self._input = self._session.get_inputs()[0].name

    def score(self, image: Image.Image) -> float:
        pixels = np.asarray(
            image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        tensor = ((pixels / 255.0 - 0.5) / 0.5).transpose(2, 0, 1)[None]
        logits: Any = self._session.run(None, {self._input: tensor})[0][0]
        exp = np.exp(logits - np.max(logits))
        return float(exp[1] / np.sum(exp))


def load_face_verifier(repo_root: Path) -> Optional[YunetFaceVerifier]:
    path, sha = _manifest_path(repo_root, "face-verifier-yunet.json")
    return YunetFaceVerifier(path) if _verified(path, sha) else None


def load_explicit_classifier(repo_root: Path) -> Optional[ExplicitImageClassifier]:
    path, sha = _manifest_path(repo_root, "explicit-image-classifier.json")
    return ExplicitImageClassifier(path) if _verified(path, sha) else None
