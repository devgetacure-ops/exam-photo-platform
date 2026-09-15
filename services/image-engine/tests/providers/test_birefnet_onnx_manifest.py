"""The ONNX BiRefNet manifest written beside the weights wins (DEC-101).

The graph is exported on the host that runs it, so a server whose model-fetch
installed a newer torch holds different bytes from the ones whose checksum is
committed. The export records its own checksum beside the file, on the model
volume, and the loader must prefer it.
"""

import json
from pathlib import Path

from exam_photo.providers.segmenters.birefnet_onnx_segmenter import (
    LOCAL_MANIFEST_FILENAME,
    load_manifest_defaults,
)

COMMITTED_SHA = "a" * 64
EXPORTED_SHA = "b" * 64


def _repo(tmp_path: Path) -> Path:
    manifests = tmp_path / "model-manifests"
    manifests.mkdir()
    (manifests / "birefnet_onnx.json").write_text(
        json.dumps(
            {
                "onnx_filename": "model.onnx",
                "onnx_sha256": COMMITTED_SHA,
                "inference_input_size": 512,
                "local_model_dir_default": "model-assets/birefnet_onnx",
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_without_a_local_manifest_the_committed_checksum_is_used(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)

    model_dir, filename, sha, size = load_manifest_defaults(root)

    assert model_dir == root / "model-assets" / "birefnet_onnx"
    assert (filename, sha, size) == ("model.onnx", COMMITTED_SHA, 512)


def test_the_manifest_beside_the_weights_wins(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    model_dir = root / "model-assets" / "birefnet_onnx"
    model_dir.mkdir(parents=True)
    (model_dir / LOCAL_MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "onnx_filename": "model.onnx",
                "onnx_sha256": EXPORTED_SHA,
                "inference_input_size": 512,
            }
        ),
        encoding="utf-8",
    )

    returned_dir, filename, sha, size = load_manifest_defaults(root)

    assert returned_dir == model_dir
    assert (filename, sha, size) == ("model.onnx", EXPORTED_SHA, 512)
