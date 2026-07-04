import os
import json
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import argparse
import math


def transform_point(
    x: float,
    y: float,
    angle_deg: float,
    scale: float,
    tx: float,
    ty: float,
    cx: float,
    cy: float,
) -> tuple[float, float]:
    """Applies rotation (around cx, cy), scaling, and translation to a point (x, y)."""
    # 1. Translate relative to center
    dx = x - cx
    dy = y - cy
    # 2. Rotate
    rad = math.radians(angle_deg)
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    # 3. Scale and translate back with offset
    nx = rx * scale + cx + tx
    ny = ry * scale + cy + ty
    return nx, ny


def transform_box(
    box: dict,
    angle_deg: float,
    scale: float,
    tx: float,
    ty: float,
    cx: float,
    cy: float,
) -> dict:
    """Transforms a bounding box, computing the new axis-aligned bounding box of the transformed corners."""
    corners = [
        (box["left"], box["top"]),
        (box["right"], box["top"]),
        (box["left"], box["bottom"]),
        (box["right"], box["bottom"]),
    ]
    tx_corners = [
        transform_point(x, y, angle_deg, scale, tx, ty, cx, cy) for x, y in corners
    ]
    xs = [pt[0] for pt in tx_corners]
    ys = [pt[1] for pt in tx_corners]
    return {"left": min(xs), "top": min(ys), "right": max(xs), "bottom": max(ys)}


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic variants for visual quality benchmarks."
    )
    parser.add_argument(
        "--seed", type=int, default=18001, help="Fixed seed for transformations."
    )
    args = parser.parse_args()

    # Seed the random number generator for reproducibility
    np.random.seed(args.seed)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(
        repo_root, "tests", "fixtures", "engine_quality", "fixture_manifest.json"
    )
    annotations_path = os.path.join(
        repo_root, "tests", "fixtures", "engine_quality", "base_annotations.json"
    )
    base_dir = os.path.join(repo_root, "tests", "fixtures", "engine_quality", "base")
    variants_dir = os.path.join(
        repo_root, "tests", "fixtures", "engine_quality", "variants"
    )
    os.makedirs(variants_dir, exist_ok=True)

    with open(manifest_path) as f:
        manifest = json.load(f)

    with open(annotations_path) as f:
        base_annos = json.load(f)

    variant_manifest = []

    # Transformation types we want to cover across variants
    transforms_list = [
        {
            "name": "clean",
            "rotation": 0.0,
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 0.0,
            "contrast": 1.0,
            "noise": 0.0,
        },
        {
            "name": "rot_l",
            "rotation": -3.0,
            "scale": 0.95,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 0.0,
            "contrast": 1.0,
            "noise": 0.0,
        },
        {
            "name": "rot_r",
            "rotation": 3.0,
            "scale": 0.95,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 0.0,
            "contrast": 1.0,
            "noise": 0.0,
        },
        {
            "name": "blur",
            "rotation": 0.0,
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 1.5,
            "contrast": 1.0,
            "noise": 0.0,
        },
        {
            "name": "contrast_low",
            "rotation": 0.0,
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 0.0,
            "contrast": 0.7,
            "noise": 0.0,
        },
        {
            "name": "noise",
            "rotation": 0.0,
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "blur": 0.0,
            "contrast": 1.0,
            "noise": 0.05,
        },
    ]

    for entry in manifest:
        fid = entry["fixture_id"]
        base_anno = base_annos.get(fid)
        if not base_anno:
            print(f"Warning: No annotations found for {fid}, skipping.")
            continue

        img_path = os.path.join(base_dir, f"{fid}.jpg")
        img = Image.open(img_path)
        w, h = img.size
        cx, cy = w / 2.0, h / 2.0

        for t_cfg in transforms_list:
            variant_id = f"{fid}_{t_cfg['name']}"

            # Apply image transforms
            v_img = img.copy()

            # 1. Rotate & Scale
            if t_cfg["rotation"] != 0.0 or t_cfg["scale"] != 1.0:
                # Rotate with LANCZOS resampling to prevent aliasing
                # Note: Expand=False keeps dimensions identical
                v_img = v_img.rotate(
                    t_cfg["rotation"], resample=Image.Resampling.BICUBIC, expand=False
                )

                # Apply scale if not 1.0
                if t_cfg["scale"] != 1.0:
                    sw, sh = (
                        int(round(w * t_cfg["scale"])),
                        int(round(h * t_cfg["scale"])),
                    )
                    v_img = v_img.resize((sw, sh), Image.Resampling.LANCZOS)
                    # Pad/Crop back to original size centered
                    canvas = Image.new(
                        img.mode, (w, h), (255, 255, 255) if img.mode == "RGB" else 255
                    )
                    ox, oy = (w - sw) // 2, (h - sh) // 2
                    canvas.paste(v_img, (ox, oy))
                    v_img = canvas

            # 2. Blur
            if t_cfg["blur"] > 0.0:
                v_img = v_img.filter(ImageFilter.GaussianBlur(t_cfg["blur"]))

            # 3. Contrast
            if t_cfg["contrast"] != 1.0:
                enhancer = ImageEnhance.Contrast(v_img)
                v_img = enhancer.enhance(t_cfg["contrast"])

            # 4. Noise
            if t_cfg["noise"] > 0.0:
                arr = np.array(v_img).astype(np.float32)
                # Deterministic noise based on numpy seed
                noise = np.random.normal(0, t_cfg["noise"] * 255.0, arr.shape)
                arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
                v_img = Image.fromarray(arr, mode=img.mode)

            # Save variant as PNG for pixel-array preservation
            v_filename = f"{variant_id}.png"
            dest_path = os.path.join(variants_dir, v_filename)
            v_img.save(dest_path, format="PNG")

            # Transform annotations mathematically
            t_anno = {
                "variant_id": variant_id,
                "base_fixture_id": fid,
                "expected_valid": base_anno["expected_valid"],
                "expected_face_count": base_anno["expected_face_count"],
                "expected_issue_codes": base_anno["expected_issue_codes"],
                "image_size": [w, h],
                "face_box": None,
                "landmarks": None,
                "ground_truth_head_box": None,
                "ears_visible_expected": base_anno["ears_visible_expected"],
                "has_headwear": base_anno["has_headwear"],
            }

            # Translation offsets due to scale padding
            tx = 0.0
            ty = 0.0
            scale = t_cfg["scale"]
            if scale != 1.0:
                sw, sh = int(round(w * scale)), int(round(h * scale))
                tx = (w - sw) // 2
                ty = (h - sh) // 2

            if base_anno["face_box"]:
                t_anno["face_box"] = transform_box(
                    base_anno["face_box"], t_cfg["rotation"], scale, tx, ty, cx, cy
                )

            if base_anno["ground_truth_head_box"]:
                t_anno["ground_truth_head_box"] = transform_box(
                    base_anno["ground_truth_head_box"],
                    t_cfg["rotation"],
                    scale,
                    tx,
                    ty,
                    cx,
                    cy,
                )

            if base_anno["landmarks"]:
                lm = base_anno["landmarks"]
                lx, ly = transform_point(
                    lm["left_eye"]["x"],
                    lm["left_eye"]["y"],
                    t_cfg["rotation"],
                    scale,
                    tx,
                    ty,
                    cx,
                    cy,
                )
                rx, ry = transform_point(
                    lm["right_eye"]["x"],
                    lm["right_eye"]["y"],
                    t_cfg["rotation"],
                    scale,
                    tx,
                    ty,
                    cx,
                    cy,
                )

                custom_lms = {}
                for k, pt in lm["custom_landmarks"].items():
                    px, py = transform_point(
                        pt["x"], pt["y"], t_cfg["rotation"], scale, tx, ty, cx, cy
                    )
                    custom_lms[k] = {"x": px, "y": py}

                t_anno["landmarks"] = {
                    "left_eye": {"x": lx, "y": ly},
                    "right_eye": {"x": rx, "y": ry},
                    "custom_landmarks": custom_lms,
                }

            manifest_entry = {
                "base_fixture_id": fid,
                "variant_id": variant_id,
                "seed": args.seed,
                "transformations": t_cfg,
                "transformed_annotations": t_anno,
            }
            variant_manifest.append(manifest_entry)

    v_manifest_path = os.path.join(variants_dir, "variants_manifest.json")
    with open(v_manifest_path, "w") as f:
        json.dump(variant_manifest, f, indent=2)

    print(
        f"Generated {len(variant_manifest)} variants. Manifest saved at {v_manifest_path}"
    )


if __name__ == "__main__":
    main()
