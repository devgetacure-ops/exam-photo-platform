"""Builds the film's photo assets from the real engine run.

Inputs:  public/photo/source.png and an engine output dir (refined_alpha.png,
         decontaminate_foreground.png, jee-main_photo.jpg, processing_report.json)
Outputs: public/photo/{cutout.png, plate.jpg, prepared.jpg, landmarks.json}
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import cv2

root = Path(__file__).resolve().parent.parent / "public" / "photo"
eng = Path(sys.argv[1])
src = Image.open(root / "source.png").convert("RGB")
alpha = Image.open(eng / "refined_alpha.png").convert("L")
fg = Image.open(eng / "decontaminate_foreground.png").convert("RGB")

cut = fg.copy(); cut.putalpha(alpha)
cut.save(root / "cutout.png")

# the room without her: inpaint a dilated hole, then soften it so the seam never reads
a = np.array(alpha)
hole = cv2.dilate((a > 8).astype(np.uint8) * 255, np.ones((41, 41), np.uint8))
small = cv2.resize(np.array(src), None, fx=0.5, fy=0.5)
hs = cv2.resize(hole, None, fx=0.5, fy=0.5)
plate = cv2.inpaint(small, hs, 25, cv2.INPAINT_TELEA)
plate = cv2.resize(plate, src.size)
Image.fromarray(plate).filter(ImageFilter.GaussianBlur(2)).save(root / "plate.jpg", quality=92)

Image.open(eng / "jee-main_photo.jpg").save(root / "prepared.jpg", quality=95)

rep = json.loads((eng / "processing_report.json").read_text())
pq = rep.get("portrait_quality_report", {})
out = {
    "size": list(src.size),
    "crop": pq.get("crop_box"),
    "head": pq.get("head_bounding_box"),
    "final": {"w": rep.get("final_width"), "h": rep.get("final_height"), "bytes": rep.get("final_bytes")},
    "head_height_ratio": pq.get("head_height_ratio"),
    "points": {},
}
try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=sys.argv[2]), num_faces=1))
    res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(src)))
    lm = res.face_landmarks[0]
    W, H = src.size
    # a sparse, legible subset: oval, brows, eyes, nose, lips
    idx = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152,
           148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
           33, 160, 158, 133, 153, 144, 362, 385, 387, 263, 373, 380, 70, 63, 105, 66, 107, 336, 296, 334, 293, 300,
           1, 4, 5, 195, 197, 6, 98, 327, 61, 291, 0, 17, 13, 14, 468, 473]
    out["points"] = {str(i): [round(lm[i].x * W, 1), round(lm[i].y * H, 1)] for i in idx if i < len(lm)}
except Exception as e:  # landmarks are a garnish; never block the build on them
    print("landmarks skipped:", e)
(root / "landmarks.json").write_text(json.dumps(out))
print("ok", len(out["points"]), "points", out["crop"], out["final"])
