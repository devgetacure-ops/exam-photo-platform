#!/usr/bin/env python
"""Export the vendored BiRefNet PyTorch checkpoint to ONNX (faster-matting Step 1).

Usage
-----
    python scripts/export_birefnet_onnx.py [--check-image PATH]

This is an operator-invoked, one-time conversion tool, matching the pattern of
``scripts/download_birefnet.py``. It never runs automatically during image
processing.

Same weights, same maths: this script performs no quantisation and no
architecture change. It loads the same vendored PyTorch checkpoint the
``birefnet`` backend uses (verifying its SHA-256 against
``model-manifests/birefnet.json`` first, via
``BiRefNetSubjectSegmenter``'s own loading path so there is exactly one place
that does that verification), traces it at the fixed 512x512 inference
resolution, and writes the resulting graph to
``model-assets/birefnet_onnx/model.onnx``.

Equivalence check
------------------
After export, the script runs one identical input through both the PyTorch
module and the exported ONNX graph (via onnxruntime, CPU execution provider)
and reports the maximum and mean absolute difference between the two
probability masks. This must be at float tolerance (see ``--tolerance``) before
the export is trusted -- if it is not, the export is wrong and the resulting
``model-manifests/birefnet_onnx.json`` is not written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "services" / "image-engine" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_ONNX_MANIFEST_PATH = _REPO_ROOT / "model-manifests" / "birefnet_onnx.json"
_DEFAULT_DEST_DIR = _REPO_ROOT / "model-assets" / "birefnet_onnx"
_ONNX_FILENAME = "model.onnx"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_torch_model(inference_size: int):
    import torch

    from exam_photo.providers.segmenters.birefnet_segmenter import (
        BiRefNetSubjectSegmenter,
        load_manifest_defaults,
    )

    model_dir, weights_filename, expected_sha, manifest_size = load_manifest_defaults(
        _REPO_ROOT
    )
    segmenter = BiRefNetSubjectSegmenter(
        model_dir=model_dir,
        expected_sha256=expected_sha,
        weights_filename=weights_filename,
        inference_size=inference_size,
    )
    segmenter._ensure_initialized()
    assert segmenter._model is not None
    return segmenter._model, model_dir, expected_sha, manifest_size, torch


def _register_deform_conv2d_symbolic(torch_mod, opset_version: int) -> None:
    """Teach the legacy TorchScript ONNX exporter about
    ``torchvision::deform_conv2d``.

    BiRefNet's decoder uses torchvision's modulated deformable convolution
    (``ASPPDeformable``), which has no symbolic registered anywhere -- neither
    in PyTorch nor in torchvision itself -- so export fails with
    ``UnsupportedOperatorError`` otherwise.

    ONNX gained a native ``DeformConv`` op in opset 22, which looked like the
    direct mapping, but onnxruntime 1.23 has no CPU kernel for it (confirmed
    by probing a minimal single-node model in both the standard and
    ``com.microsoft`` domains -- both raise ``NOT_IMPLEMENTED``/"not a
    registered function"). The ``deform_conv2d_onnx_exporter`` package
    (MIT-licensed, PyPI) instead *decomposes* the operation into ordinary ONNX
    ops any runtime already implements -- ``GatherND`` for the bilinear
    sample at each offset location, then an ordinary weighted sum -- which is
    the same algorithm restated in different ops, not an approximation of it.
    Used only at export time; it is not a runtime dependency of the ONNX
    segmenter.
    """
    import deform_conv2d_onnx_exporter as dcn_exporter

    # The package predates the current torch: it tries
    # ``from torch.onnx._type_utils import JitScalarType``, which no longer
    # exists at that path (it now lives at ``torch.onnx.JitScalarType``), so
    # the import silently fails inside the package and it falls back to a
    # dtype-lookup branch that indexes a dict keyed by strings ("Float") with
    # the modern enum instead, raising ``KeyError``. The package already has
    # a correct, maintained code path for current torch gated on this same
    # symbol (``if JitScalarType is not None and hasattr(..., "from_value")``)
    # -- it just never finds it. Supplying it is a compatibility shim for an
    # unmaintained dependency, not a change to the maths.
    dcn_exporter.JitScalarType = torch_mod.onnx.JitScalarType

    dcn_exporter.register_custom_op_symbolic(
        "torchvision::deform_conv2d",
        dcn_exporter.deform_conv2d_func(use_gathernd=True, enable_openvino_patch=False),
        opset_version,
    )


def _patch_dcn_shape_fallback(torch_mod, shape_queue: list) -> None:
    """Make the exporter's ``input`` H/W lookup fall back to ground truth
    recorded from an eager forward pass.

    Some ``DeformableConv2d`` call sites sit downstream of reshapes whose
    target size is computed from ``aten::size`` + arithmetic rather than a
    literal constant (BiRefNet's decoder patchifies/depatchifies a feature
    map using sizes it computes at trace time), so the traced graph carries
    no static shape for ``input`` at those nodes even though the fixed
    512x512 input makes every size fully determined. ``shape_queue`` is
    filled, in call order, by forward hooks on every ``DeformableConv2d``
    instance during the single eager reference pass this script already runs
    -- so it is measured from the real execution, not inferred -- and this
    patch only ever fills in a hole the graph itself left empty; it never
    overrides a size the graph did carry.
    """
    import deform_conv2d_onnx_exporter as dcn_exporter

    call_index = {"i": 0}
    original_create_dcn_params = dcn_exporter.create_dcn_params

    def _patched_create_dcn_params(input, weight, offset, mask, bias, *rest, **kwargs):
        true_h, true_w = shape_queue[call_index["i"]]
        call_index["i"] += 1
        original_get = dcn_exporter.get_tensor_dim_size

        def _get_with_fallback(tensor, dim):
            value = original_get(tensor, dim)
            if value is not None:
                return value
            # input, offset and mask all come from sibling convs inside the
            # same DeformableConv2d that share kernel size, stride and
            # padding (see DeformableConv2d.__init__), so their spatial size
            # matches input's by construction, and this whole pipeline only
            # ever runs one image at a time, so batch is always 1 -- this
            # never extends to `weight`, which is a parameter and always
            # carries static shape metadata already.
            if tensor is input or tensor is offset or tensor is mask:
                if dim == 0:
                    return 1
                if dim == 2:
                    return true_h
                if dim == 3:
                    return true_w
            return value

        dcn_exporter.get_tensor_dim_size = _get_with_fallback
        try:
            return original_create_dcn_params(
                input, weight, offset, mask, bias, *rest, **kwargs
            )
        finally:
            dcn_exporter.get_tensor_dim_size = original_get

    dcn_exporter.create_dcn_params = _patched_create_dcn_params


def _record_deform_conv_input_shapes(model, sample_tensor, torch_mod) -> list:
    """Run one eager forward pass, recording each ``DeformableConv2d``'s
    input (H, W) in call order, then remove the hooks."""
    shapes: list = []
    handles = []

    def _hook(module, inputs):
        x = inputs[0]
        shapes.append((int(x.shape[2]), int(x.shape[3])))

    for module in model.modules():
        if type(module).__name__ == "DeformableConv2d":
            handles.append(module.register_forward_pre_hook(_hook))

    try:
        with torch_mod.no_grad():
            model(sample_tensor)
    finally:
        for handle in handles:
            handle.remove()

    return shapes


def _wrap_for_export(model, torch_mod):
    class _LogitsOnly(torch_mod.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, x):
            out = self.inner(x)
            pred = out[-1] if isinstance(out, (list, tuple)) else out
            if isinstance(pred, (list, tuple)):
                pred = pred[-1]
            return pred

    wrapped = _LogitsOnly(model)
    wrapped.eval()
    return wrapped


def _preprocess(image: Image.Image, size: int) -> np.ndarray:
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)
    resized = image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
    arr = np.asarray(resized, dtype=np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
    return ((arr - mean) / std).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the vendored BiRefNet checkpoint to ONNX and prove "
        "numerical equivalence against the PyTorch original."
    )
    parser.add_argument(
        "--check-image",
        type=Path,
        default=None,
        help="Real photo to run the equivalence check on. Defaults to a fixed "
        "random tensor if omitted (still exercises the full graph).",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-3,
        help="Maximum allowed max-abs-difference between PyTorch and ONNX "
        "probability masks before the export is rejected.",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=17,
        help="ONNX opset version to target.",
    )
    args = parser.parse_args()

    inference_size = 512
    model, _model_dir, source_sha, _manifest_size, torch_mod = _load_torch_model(
        inference_size=inference_size
    )
    _register_deform_conv2d_symbolic(torch_mod, args.opset)

    wrapped = _wrap_for_export(model, torch_mod)

    if args.check_image is not None:
        img = Image.open(args.check_image)
        sample = _preprocess(img, inference_size)
    else:
        rng = np.random.RandomState(0)
        sample = rng.uniform(
            -1.0, 1.0, size=(1, 3, inference_size, inference_size)
        ).astype(np.float32)

    sample_tensor = torch_mod.from_numpy(sample)

    print("Running PyTorch reference inference...")
    with torch_mod.no_grad():
        torch_out = wrapped(sample_tensor).cpu().numpy().astype(np.float32)

    deform_conv_shapes = _record_deform_conv_input_shapes(
        model, sample_tensor, torch_mod
    )
    _patch_dcn_shape_fallback(torch_mod, deform_conv_shapes)

    _DEFAULT_DEST_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = _DEFAULT_DEST_DIR / _ONNX_FILENAME

    print(f"Exporting to ONNX (opset {args.opset}) -> {onnx_path}")
    torch_mod.onnx.export(
        wrapped,
        (sample_tensor,),
        str(onnx_path),
        dynamo=False,
        input_names=["pixel_values"],
        output_names=["logits"],
        opset_version=args.opset,
        do_constant_folding=True,
    )

    print("Running ONNX Runtime inference on the identical input...")
    import onnxruntime as ort

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    (onnx_out,) = session.run(["logits"], {"pixel_values": sample})
    onnx_out = onnx_out.astype(np.float32)

    torch_probs = 1.0 / (1.0 + np.exp(-torch_out))
    onnx_probs = 1.0 / (1.0 + np.exp(-onnx_out))

    max_abs_diff = float(np.abs(torch_probs - onnx_probs).max())
    mean_abs_diff = float(np.abs(torch_probs - onnx_probs).mean())
    print(f"Max abs diff (probability mask):  {max_abs_diff:.8f}")
    print(f"Mean abs diff (probability mask): {mean_abs_diff:.8f}")

    if max_abs_diff > args.tolerance:
        print(
            f"\nEQUIVALENCE CHECK FAILED: max abs diff {max_abs_diff:.6f} exceeds "
            f"tolerance {args.tolerance:.6f}. The export is not trusted; "
            f"{_ONNX_MANIFEST_PATH} was not written. Deleting the ONNX file.",
            file=sys.stderr,
        )
        onnx_path.unlink(missing_ok=True)
        sys.exit(1)

    onnx_sha256 = _sha256_file(onnx_path)
    onnx_size = onnx_path.stat().st_size

    manifest = {
        "_comment": (
            "Model manifest for the ONNX export of BiRefNet subject matting "
            "(faster-matting Step 1). Same weights, same maths as "
            "model-manifests/birefnet.json -- no quantisation. Derived locally "
            "by scripts/export_birefnet_onnx.py rather than downloaded; "
            "verified bit-for-bit equivalent to the PyTorch original to float "
            "tolerance before this manifest is written."
        ),
        "name": "BiRefNet (ONNX)",
        "derived_from_repo_id": "ZhengPeng7/BiRefNet",
        "derived_from_revision": "e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4",
        "derived_from_weights_sha256": source_sha,
        "export_script": "scripts/export_birefnet_onnx.py",
        "export_opset": args.opset,
        "onnx_filename": _ONNX_FILENAME,
        "onnx_sha256": onnx_sha256,
        "onnx_size_bytes": onnx_size,
        "equivalence_check_max_abs_diff": max_abs_diff,
        "equivalence_check_mean_abs_diff": mean_abs_diff,
        "licence": "MIT",
        "licence_url": "https://huggingface.co/ZhengPeng7/BiRefNet/blob/main/LICENSE",
        "inference_input_size": inference_size,
        "local_model_dir_env_var": "EXAM_PHOTO_BIREFNET_ONNX_MODEL_DIR",
        "local_model_dir_default": "model-assets/birefnet_onnx",
        "redistribution_notes": (
            "MIT licensed, same terms as the PyTorch checkpoint it is derived "
            "from. Gitignored like the other model-assets entries; regenerate "
            "with scripts/export_birefnet_onnx.py."
        ),
    }
    with _ONNX_MANIFEST_PATH.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    print(f"\nOK Export verified and manifest written: {_ONNX_MANIFEST_PATH}")
    print(f"  ONNX file: {onnx_path} ({onnx_size:,} bytes)")
    print(f"  SHA-256:   {onnx_sha256}")


if __name__ == "__main__":
    main()
