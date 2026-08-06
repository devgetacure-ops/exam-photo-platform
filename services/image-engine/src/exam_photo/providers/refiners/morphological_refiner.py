from __future__ import annotations

import time
from typing import Any, Optional, cast

import numpy as np
from PIL import Image, ImageFilter

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.foreground_refinement import (
    ForegroundRefinementProvider,
    RefinedMaskResult,
    RefinedMaskValidationReport,
    RefinementConfig,
    RefinementValidationIssue,
)
from exam_photo.providers.refiners.errors import (
    RefinementInputError,
    RefinementOutputError,
)
from exam_photo.providers.segmenters.mask_validation import (
    count_connected_components_dsu,
)
from exam_photo.suitability.issue_codes import IssueSeverity, SuitabilityIssueCode


def _disk_offsets(radius: int) -> list[tuple[int, int]]:
    """Returns (dy, dx) offsets within a disk of given radius."""
    offsets = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy * dy + dx * dx <= radius * radius:
                offsets.append((dy, dx))
    return offsets


def _erode(
    mask: np.ndarray[Any, Any], radius: int, offsets: list[tuple[int, int]]
) -> np.ndarray[Any, Any]:
    """Binary erosion: pixel is foreground only if ALL disk neighbours are foreground.

    Pads with background (False) to prevent boundary wraparound artifacts.
    """
    h, w = mask.shape
    padded = np.pad(mask, radius, mode="constant", constant_values=False)
    result = np.ones((h, w), dtype=bool)
    for dy, dx in offsets:
        shifted = padded[radius + dy : radius + dy + h, radius + dx : radius + dx + w]
        result &= shifted
    return result


def snap_alpha_contrast(
    alpha: np.ndarray[Any, Any], low_threshold: float, high_threshold: float
) -> np.ndarray[Any, Any]:
    """Removes the broad semi-transparent halo that creates grey outlines
    after compositing, by remapping ``[low_threshold, high_threshold]`` to
    ``[0, 1]`` and applying a smoothstep. Shared between the coarse-mask path
    (which measured these thresholds; see DEC-030) and the trusted-alpha path
    for portrait-matting backends, whose raw probability mask carries the
    same kind of broad low-confidence band.
    """
    snapped = (alpha - low_threshold) / (high_threshold - low_threshold)
    snapped = np.clip(snapped, 0.0, 1.0)
    snapped = snapped * snapped * (3.0 - 2.0 * snapped)
    return cast(np.ndarray[Any, Any], snapped.astype(np.float32))


def _dilate(
    mask: np.ndarray[Any, Any], radius: int, offsets: list[tuple[int, int]]
) -> np.ndarray[Any, Any]:
    """Binary dilation: pixel is foreground if ANY disk neighbour is foreground.

    Pads with background (False) to prevent boundary wraparound artifacts.
    """
    h, w = mask.shape
    padded = np.pad(mask, radius, mode="constant", constant_values=False)
    result = np.zeros((h, w), dtype=bool)
    for dy, dx in offsets:
        shifted = padded[radius + dy : radius + dy + h, radius + dx : radius + dx + w]
        result |= shifted
    return result


def _find_internal_holes(binary_mask: np.ndarray[Any, Any]) -> tuple[int, int]:
    """Finds internal holes in a binary mask (values 0 or 255).

    Returns (num_holes, max_hole_size_px).
    """
    h, w = binary_mask.shape
    max_size = 256
    if h > max_size or w > max_size:
        scale = max_size / max(h, w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))
        img = Image.fromarray(binary_mask)
        img_resized = img.resize((new_w, new_h), resample=Image.Resampling.NEAREST)
        mask = np.array(img_resized)
    else:
        mask = binary_mask
        new_h, new_w = h, w

    # Invert mask: foreground (255) becomes 0, background (0) becomes 1
    bg = (mask == 0).astype(np.uint8)

    from collections import deque

    queue: deque[tuple[int, int]] = deque()

    # Flood fill starting from all border pixels of bg to identify external background
    for r in range(new_h):
        if bg[r, 0] == 1:
            bg[r, 0] = 2
            queue.append((r, 0))
        if bg[r, new_w - 1] == 1:
            bg[r, new_w - 1] = 2
            queue.append((r, new_w - 1))
    for c in range(1, new_w - 1):
        if bg[0, c] == 1:
            bg[0, c] = 2
            queue.append((0, c))
        if bg[new_h - 1, c] == 1:
            bg[new_h - 1, c] = 2
            queue.append((new_h - 1, c))

    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < new_h and 0 <= nc < new_w:
                if bg[nr, nc] == 1:
                    bg[nr, nc] = 2
                    queue.append((nr, nc))

    # Now, any pixel with value 1 in bg is an internal hole!
    hole_count = 0
    max_hole_size = 0
    visited = np.zeros((new_h, new_w), dtype=bool)

    for r in range(new_h):
        for c in range(new_w):
            if bg[r, c] == 1 and not visited[r, c]:
                hole_count += 1
                hole_size = 0
                hq: deque[tuple[int, int]] = deque([(r, c)])
                visited[r, c] = True
                while hq:
                    curr_r, curr_c = hq.popleft()
                    hole_size += 1
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < new_h and 0 <= nc < new_w:
                            if bg[nr, nc] == 1 and not visited[nr, nc]:
                                visited[nr, nc] = True
                                hq.append((nr, nc))
                max_hole_size = max(max_hole_size, hole_size)

    scale_factor = (h / new_h) * (w / new_w) if new_h > 0 else 1.0
    return hole_count, int(round(max_hole_size * scale_factor))


def box_filter(img: np.ndarray[Any, Any], r: int) -> np.ndarray[Any, Any]:
    """Fast box filter using 2D cumsum without Python loops."""
    h, w = img.shape
    out = np.zeros_like(img)

    # 1. Cumsum along y axis
    cy = np.cumsum(img, axis=0)
    y_max = np.minimum(np.arange(h) + r, h - 1)
    y_min = np.arange(h) - r

    temp = cy[y_max, :]
    valid_min = y_min > 0
    if np.any(valid_min):
        temp[valid_min, :] -= cy[y_min[valid_min] - 1, :]

    # 2. Cumsum along x axis
    cx = np.cumsum(temp, axis=1)
    x_max = np.minimum(np.arange(w) + r, w - 1)
    x_min = np.arange(w) - r

    out = cx[:, x_max]
    valid_xmin = x_min > 0
    if np.any(valid_xmin):
        out[:, valid_xmin] -= cx[:, x_min[valid_xmin] - 1]

    return out


# Minimum raw segmenter probability for a pixel inside the inner face box to
# be eligible for face-core hole-filling.  Low enough to bridge a small, low-
# confidence gap (glasses glare, a stray shadow) but well below the 0.5
# foreground threshold, so a region the segmenter confidently called
# background (near 0) is never forced to foreground.
_FACE_CORE_PLAUSIBILITY_THRESHOLD = 0.15

# Matting band half-width as a fraction of estimated head height.
#
# Wider is not better.  Partial alpha produced far from the true boundary reads
# as a grey smear rather than hair, and colour decontamination can only
# propagate a bounded distance into the band, so its interior keeps background
# colour.  Measured over the reference set, 0.025 raised the retained soft-alpha
# band but more than doubled the halo score; this value keeps the band inside
# the decontamination reach while still resolving strands.
_HAIR_BAND_HEAD_HEIGHT_RATIO = 0.010


def _morph_3x3(
    mask: np.ndarray[Any, Any], radius: int, maximum: bool
) -> np.ndarray[Any, Any]:
    """Dilate (maximum) or erode (minimum) a boolean mask by ``radius`` pixels.

    Uses Pillow's C-implemented rank filters applied ``radius`` times with a 3x3
    kernel.  The pure-numpy offset morphology used for the coarse 512px pass
    costs O(disk_area) array shifts per call, which is too slow to run at the
    refinement resolution; this stays linear in ``radius`` and keeps the module
    free of any dependency beyond Pillow and numpy.
    """
    if radius <= 0:
        return mask
    img = Image.fromarray((mask.astype(np.uint8)) * 255, mode="L")
    kernel = ImageFilter.MaxFilter(3) if maximum else ImageFilter.MinFilter(3)
    for _ in range(int(radius)):
        img = img.filter(kernel)
    return np.array(img) > 127


def guided_filter(
    guidance: np.ndarray[Any, Any], p: np.ndarray[Any, Any], r: int, eps: float
) -> np.ndarray[Any, Any]:
    """Monochrome Guided Filter.
    guidance: guidance image (grayscale, 2D array [0.0, 1.0])
    p: filtering input (2D array [0.0, 1.0])
    r: radius
    eps: regularization parameter
    """
    ones = np.ones_like(guidance)
    box_n = box_filter(ones, r)

    mean_i = box_filter(guidance, r) / box_n
    mean_p = box_filter(p, r) / box_n
    mean_ip = box_filter(guidance * p, r) / box_n
    cov_ip = mean_ip - mean_i * mean_p

    mean_ii = box_filter(guidance * guidance, r) / box_n
    var_i = mean_ii - mean_i * mean_i

    a = cov_ip / (var_i + eps)
    b = mean_p - a * mean_i

    mean_a = box_filter(a, r) / box_n
    mean_b = box_filter(b, r) / box_n

    q = mean_a * guidance + mean_b
    return cast(np.ndarray[Any, Any], np.clip(q, 0.0, 1.0))


class MorphologicalForegroundRefiner(ForegroundRefinementProvider):
    """Refiner that performs boundary morphological operations using pure NumPy/Pillow."""

    def __init__(self) -> None:
        self.provider_name = "MorphologicalForegroundRefiner"
        self.provider_version = "1.0.0"

    def refine_mask(
        self,
        image: Image.Image,
        coarse_mask: Image.Image,
        probability_mask: np.ndarray[Any, Any],
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        config: Optional[RefinementConfig] = None,
        head_estimate: Optional[BoundingBox] = None,
    ) -> RefinedMaskResult:
        start_time = time.perf_counter()
        cfg = config or RefinementConfig()

        # 1. Input Validation
        if not isinstance(coarse_mask, Image.Image):
            raise RefinementInputError("coarse_mask must be a PIL Image instance")
        if coarse_mask.mode != "L":
            raise RefinementInputError(
                f"coarse_mask must be L mode, got '{coarse_mask.mode}'"
            )

        if not isinstance(probability_mask, np.ndarray):
            raise RefinementInputError("probability_mask must be a numpy ndarray")
        if probability_mask.dtype != np.float32:
            raise RefinementInputError(
                f"probability_mask must be float32, got {probability_mask.dtype}"
            )
        if len(probability_mask.shape) != 2:
            raise RefinementInputError(
                f"probability_mask must be 2D, got shape {probability_mask.shape}"
            )

        img_w, img_h = coarse_mask.size
        mask_h, mask_w = probability_mask.shape
        if (img_w, img_h) != (mask_w, mask_h):
            raise RefinementInputError(
                f"Dimension mismatch between coarse_mask ({img_w}x{img_h}) and probability_mask ({mask_w}x{mask_h})"
            )

        if probability_mask.size > 16777216:
            raise RefinementInputError(
                f"probability_mask size ({probability_mask.size}) exceeds safety limit 16777216"
            )

        if not np.all(np.isfinite(probability_mask)):
            raise RefinementInputError(
                "probability_mask must only contain finite values (no NaN or inf)"
            )

        if np.any((probability_mask < -1e-5) | (probability_mask > 1.00001)):
            raise RefinementInputError(
                "probability_mask values must strictly be in range [0.0, 1.0]"
            )

        # A portrait-matting backend has already done the edge work this class
        # normally performs.  The old path still ran the complete morphology
        # and guided-filter pipeline and only restored ``probability_mask`` at
        # the end.  On a large phone image that meant minutes of native-scale
        # processing whose result was immediately discarded.  Preserve the
        # trusted alpha up front and build only the contract artifacts and
        # validation report that downstream stages consume.
        if cfg.trust_input_alpha:
            alpha = np.clip(probability_mask.astype(np.float32, copy=True), 0.0, 1.0)
            alpha = snap_alpha_contrast(
                alpha, cfg.alpha_snap_low_threshold, cfg.alpha_snap_high_threshold
            )
            binary_arr = np.where(alpha >= 0.5, 255, 0).astype(np.uint8)
            refined_binary_mask = Image.fromarray(binary_arr, mode="L")

            trimap_arr = np.full(alpha.shape, 128, dtype=np.uint8)
            trimap_arr[alpha <= cfg.definite_background_threshold] = 0
            trimap_arr[alpha >= cfg.definite_foreground_threshold] = 255
            trimap = Image.fromarray(trimap_arr, mode="L")

            mask_np = np.array(coarse_mask) > 127
            validation_report = self._validate_refined_mask(
                coarse_mask,
                mask_np,
                alpha,
                refined_binary_mask,
                trimap,
                face,
                head_estimate,
            )
            duration = (time.perf_counter() - start_time) * 1000.0
            try:
                return RefinedMaskResult(
                    provider_name=self.provider_name,
                    provider_version=self.provider_version,
                    refined_alpha_mask=alpha,
                    refined_binary_mask=refined_binary_mask,
                    trimap=trimap,
                    input_width=img_w,
                    input_height=img_h,
                    effective_radius_px=0,
                    refinement_duration_ms=duration,
                    config_used=cfg,
                    validation=validation_report,
                )
            except Exception as e:
                raise RefinementOutputError(
                    f"Generated trusted-alpha result failed contract validation: {e}"
                ) from e

        # 2. Memory & Resolution Safety Limits and Downgrade
        quality_mode = cfg.quality_mode
        matte_quality_downgraded = False

        # Determine target refinement dimensions
        if quality_mode == "fast":
            max_dim = 512
        elif quality_mode == "balanced":
            max_dim = 1024
        else:  # high
            max_dim = max(img_w, img_h)

        # Spend the memory budget on resolution rather than dropping a whole
        # quality tier.  Demoting "high" to "balanced" pinned an ordinary 10 MP
        # phone photo to a 1024px matte, discarding hair detail the segmenter
        # had actually produced; scaling to the same pixel budget instead keeps
        # roughly 1.7x the linear resolution at identical peak memory.
        longest_edge = max(img_w, img_h)
        total_pixels = img_w * img_h
        if total_pixels > cfg.maximum_matting_pixels:
            budget_scale = float(
                np.sqrt(cfg.maximum_matting_pixels / float(total_pixels))
            )
            budget_dim = max(512, int(round(longest_edge * budget_scale)))
            if budget_dim < max_dim:
                max_dim = budget_dim
                matte_quality_downgraded = True
        if longest_edge > cfg.maximum_native_dimension and (
            max_dim > cfg.maximum_native_dimension
        ):
            max_dim = cfg.maximum_native_dimension
            matte_quality_downgraded = True

        orig_w, orig_h = img_w, img_h
        if max(img_w, img_h) > max_dim:
            scale_refine = max_dim / max(img_w, img_h)
            refine_w = int(round(img_w * scale_refine))
            refine_h = int(round(img_h * scale_refine))
        else:
            scale_refine = 1.0
            refine_w, refine_h = img_w, img_h

        # Low resolution morphology scale (Always 512px max for coarse cleanups)
        max_dim_low = 512
        if max(img_w, img_h) > max_dim_low:
            scale_low = max_dim_low / max(img_w, img_h)
            low_w = int(round(img_w * scale_low))
            low_h = int(round(img_h * scale_low))
        else:
            scale_low = 1.0
            low_w, low_h = img_w, img_h

        # 3. Morphological Sequence (Closing -> Opening) on low resolution
        coarse_mask_low = coarse_mask.resize((low_w, low_h), Image.Resampling.NEAREST)
        radius_low = cfg.effective_radius(low_w, low_h)
        offsets_low = _disk_offsets(radius_low)
        mask_np_low = np.array(coarse_mask_low) > 127
        closed_low = _erode(
            _dilate(mask_np_low, radius_low, offsets_low), radius_low, offsets_low
        )
        opened_low = _dilate(
            _erode(closed_low, radius_low, offsets_low), radius_low, offsets_low
        )

        # 4. Face/Head Core Protection on low resolution
        #
        # Patches small genuine gaps a segmenter can leave inside a real face
        # (glasses reflections, harsh lighting), not a licence to overwrite
        # whatever the segmenter said.  Forcing the whole axis-aligned
        # rectangle to foreground is wrong whenever the face box isn't a tight
        # fit -- an angled head, background visible in a box corner, an object
        # near the head -- and paints that background opaque regardless of how
        # confidently the model excluded it.  Measured case: a signboard
        # directly behind a subject's head was correctly excluded by BiRefNet
        # (raw mask clean) and then reintroduced here because the axis-aligned
        # face-box rectangle happened to overlap it.  Only pixels the
        # segmenter itself considered plausibly foreground are protected.
        cleaned_binary_low = opened_low.copy()
        if cfg.preserve_face_core and face is not None:
            prob_low_arr = np.array(
                Image.fromarray(probability_mask, mode="F").resize(
                    (low_w, low_h), Image.Resampling.BILINEAR
                )
            )
            plausible_low = prob_low_arr >= _FACE_CORE_PLAUSIBILITY_THRESHOLD
            faces_list = face if isinstance(face, list) else [face]
            for f in faces_list:
                face_box = f.bounding_box
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(low_w, low_h)
                else:
                    face_box = face_box.__class__(
                        left=face_box.left * scale_low,
                        right=face_box.right * scale_low,
                        top=face_box.top * scale_low,
                        bottom=face_box.bottom * scale_low,
                    )

                face_w = face_box.right - face_box.left
                face_h = face_box.bottom - face_box.top

                inner_left = max(
                    0, min(int(round(face_box.left + face_w * 0.1)), low_w - 1)
                )
                inner_right = max(
                    0, min(int(round(face_box.right - face_w * 0.1)), low_w)
                )
                inner_top = max(
                    0, min(int(round(face_box.top + face_h * 0.1)), low_h - 1)
                )
                inner_bottom = max(
                    0, min(int(round(face_box.bottom - face_h * 0.1)), low_h)
                )

                if inner_right > inner_left and inner_bottom > inner_top:
                    region = cleaned_binary_low[
                        inner_top:inner_bottom, inner_left:inner_right
                    ]
                    region_plausible = plausible_low[
                        inner_top:inner_bottom, inner_left:inner_right
                    ]
                    region |= region_plausible

        # 6. Build the matting band at refinement resolution.
        #
        # Previously the eroded/dilated boundary was computed at 512px and
        # upsampled with NEAREST, so the "unknown" region the guided filter is
        # allowed to touch arrived quantised into ~8px blocks on a 4000px photo.
        # The filter could then only ever produce a blocky edge, no matter how
        # much resolution the matting pass itself had.  Resampling the cleaned
        # decision smoothly and re-deriving the band here lets the band follow
        # the actual subject boundary.
        cleaned_img_low = Image.fromarray(
            (cleaned_binary_low.astype(np.uint8)) * 255, mode="L"
        )
        cleaned_refine = (
            np.array(
                cleaned_img_low.resize((refine_w, refine_h), Image.Resampling.BILINEAR)
            )
            > 127
        )

        # Band width scales with the subject, not with the frame.  A fixed band
        # is simultaneously too wide for a collar and too narrow for hair, and
        # it is the band that caps how much partial coverage can survive at all:
        # alpha outside it is forced to 0 or 1 regardless of what the matting
        # pass computed.  Sizing it from the head lets flyaway hair resolve on a
        # large subject without smearing the edge on a small one.
        band_radius_refine = int(
            round(radius_low / max(scale_low, 1e-6) * scale_refine)
        )
        if head_estimate is not None and head_estimate.height > 0:
            head_band = int(
                round(
                    _HAIR_BAND_HEAD_HEIGHT_RATIO * head_estimate.height * scale_refine
                )
            )
            band_radius_refine = max(band_radius_refine, head_band)
        band_radius_refine = max(2, min(28, band_radius_refine))

        definite_fg_refine = _morph_3x3(cleaned_refine, band_radius_refine, False)
        dilated_refine = _morph_3x3(cleaned_refine, band_radius_refine, True)

        boundary_band_refine = dilated_refine ^ definite_fg_refine

        # Guidance image at refinement scale
        image_refine = image.resize((refine_w, refine_h), Image.Resampling.BILINEAR)
        guidance_gray = np.array(image_refine.convert("L"), dtype=np.float32) / 255.0

        # Filtering input probability mask p at refinement scale
        prob_img = Image.fromarray(
            (probability_mask * 255.0).astype(np.uint8), mode="L"
        )
        prob_img_refine = prob_img.resize(
            (refine_w, refine_h), Image.Resampling.BILINEAR
        )
        p = np.array(prob_img_refine, dtype=np.float32) / 255.0

        # 7. Guided Filter Refinement
        r_guided = max(
            1, int(round(min(refine_w, refine_h) * cfg.edge_refinement_radius_ratio))
        )
        eps = 1e-4

        refined_alpha_raw = guided_filter(guidance_gray, p, r_guided, eps)

        alpha_refine: np.ndarray[Any, Any] = np.zeros(
            (refine_h, refine_w), dtype=np.float32
        )
        alpha_refine[definite_fg_refine] = 1.0
        alpha_refine[boundary_band_refine] = refined_alpha_raw[boundary_band_refine]
        alpha_refine = cast(np.ndarray[Any, Any], np.clip(alpha_refine, 0.0, 1.0))

        # 8. Upscale alpha back to original resolution if needed
        if scale_refine != 1.0:
            alpha_img = Image.fromarray(
                (alpha_refine * 255.0).astype(np.uint8), mode="L"
            )
            alpha_high_img = alpha_img.resize(
                (orig_w, orig_h), Image.Resampling.BILINEAR
            )
            alpha = np.array(alpha_high_img, dtype=np.float32) / 255.0
            alpha = np.clip(alpha, 0.0, 1.0)
        else:
            alpha = alpha_refine

        # Exam photo outputs need a distinct white-background boundary. Guided
        # filtering preserves fine edges, then this contrast step removes the
        # broad semi-transparent halo that creates grey outlines after compositing.
        alpha = snap_alpha_contrast(
            alpha, cfg.alpha_snap_low_threshold, cfg.alpha_snap_high_threshold
        )

        # Refined binary mask (thresholded at 0.5)
        binary_arr = np.where(alpha >= 0.5, 255, 0).astype(np.uint8)
        refined_binary_mask = Image.fromarray(binary_arr, mode="L")

        # Trimap generation (from low resolution, resized using NEAREST)
        trimap_radius_low = max(
            1, int(round(max(1, cfg.trimap_band_width_px // 2) * scale_low))
        )
        trimap_offsets_low = _disk_offsets(trimap_radius_low)
        eroded_trimap_low = _erode(
            cleaned_binary_low, trimap_radius_low, trimap_offsets_low
        )
        dilated_trimap_low = _dilate(
            cleaned_binary_low, trimap_radius_low, trimap_offsets_low
        )

        trimap_arr_low = np.zeros(cleaned_binary_low.shape, dtype=np.uint8)
        trimap_arr_low[dilated_trimap_low] = 128
        trimap_arr_low[eroded_trimap_low] = 255

        trimap_low_img = Image.fromarray(trimap_arr_low, mode="L")
        trimap = trimap_low_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)

        # 9. Validation on original resolution
        mask_np = np.array(coarse_mask) > 127
        validation_report = self._validate_refined_mask(
            coarse_mask,
            mask_np,
            alpha,
            refined_binary_mask,
            trimap,
            face,
            head_estimate,
        )

        if matte_quality_downgraded:
            validation_report.issue_codes.append("MATTE_QUALITY_DOWNGRADED")
            validation_report.issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.MATTE_QUALITY_DOWNGRADED,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        duration = (time.perf_counter() - start_time) * 1000.0

        try:
            return RefinedMaskResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                refined_alpha_mask=alpha,
                refined_binary_mask=refined_binary_mask,
                trimap=trimap,
                input_width=orig_w,
                input_height=orig_h,
                effective_radius_px=radius_low
                if scale_low == 1.0
                else int(round(radius_low / scale_low)),
                refinement_duration_ms=duration,
                config_used=cfg,
                validation=validation_report,
            )
        except Exception as e:
            raise RefinementOutputError(
                f"Generated result failed contract validation: {e}"
            ) from e

    def _validate_refined_mask(
        self,
        coarse_mask_pil: Image.Image,
        coarse_mask_np: np.ndarray[Any, Any],
        refined_alpha_mask: np.ndarray[Any, Any],
        refined_binary_mask: Image.Image,
        trimap: Image.Image,
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        head_estimate: Optional[BoundingBox] = None,
    ) -> RefinedMaskValidationReport:
        refined_arr = np.array(refined_binary_mask)
        refined_bin = np.where(refined_arr > 127, 255, 0).astype(np.uint8)
        foreground_coverage_ratio = float(np.mean(refined_bin == 255))

        edge_transition_ratio = float(
            np.sum((refined_alpha_mask > 1e-5) & (refined_alpha_mask < 1.0 - 1e-5))
            / refined_alpha_mask.size
        )

        coarse_bin = np.where(coarse_mask_np, 255, 0).astype(np.uint8)

        # Connected-component validation is topological rather than
        # pixel-exact.  Running the Python DSU over a 10-16 MP candidate mask
        # dominates the complete pipeline even though the same check at a
        # bounded resolution detects the fragmentation it is designed for.
        # Match the existing internal-hole validator's bounded-resolution
        # policy and keep all coverage/bounding-box measurements at native
        # resolution below.
        component_max_dim = 512
        if max(refined_bin.shape) > component_max_dim:
            component_scale = component_max_dim / max(refined_bin.shape)
            component_h = max(1, int(round(refined_bin.shape[0] * component_scale)))
            component_w = max(1, int(round(refined_bin.shape[1] * component_scale)))
            coarse_for_components = np.array(
                Image.fromarray(coarse_bin, mode="L").resize(
                    (component_w, component_h), Image.Resampling.NEAREST
                )
            )
            refined_for_components = np.array(
                Image.fromarray(refined_bin, mode="L").resize(
                    (component_w, component_h), Image.Resampling.NEAREST
                )
            )
        else:
            coarse_for_components = coarse_bin
            refined_for_components = refined_bin

        coarse_cc, _ = count_connected_components_dsu(coarse_for_components)
        refined_cc, _ = count_connected_components_dsu(refined_for_components)
        connectivity_improvement = refined_cc <= coarse_cc

        intersection = np.logical_and(coarse_mask_np, refined_arr > 127).sum()
        union = np.logical_or(coarse_mask_np, refined_arr > 127).sum()
        coarse_iou = float(intersection / union) if union > 0 else 1.0

        issue_codes = []
        issues = []

        # 1. Check alpha invalid
        if not np.all(np.isfinite(refined_alpha_mask)) or np.any(
            (refined_alpha_mask < -1e-5) | (refined_alpha_mask > 1.00001)
        ):
            issue_codes.append("REFINEMENT_ALPHA_INVALID")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_ALPHA_INVALID,
                    severity=IssueSeverity.ERROR,
                    blocking_for_processing=True,
                    confidence=1.0,
                )
            )

        # 2. Check binary invalid
        if np.any((refined_arr != 0) & (refined_arr != 255)):
            issue_codes.append("REFINEMENT_BINARY_INVALID")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_BINARY_INVALID,
                    severity=IssueSeverity.ERROR,
                    blocking_for_processing=True,
                    confidence=1.0,
                )
            )

        # 3. Check trimap invalid
        trimap_arr = np.array(trimap)
        if np.any((trimap_arr != 0) & (trimap_arr != 128) & (trimap_arr != 255)):
            issue_codes.append("REFINEMENT_TRIMAP_INVALID")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_TRIMAP_INVALID,
                    severity=IssueSeverity.ERROR,
                    blocking_for_processing=True,
                    confidence=1.0,
                )
            )

        # 4. Overall coverage checks
        coarse_coverage = float(np.mean(coarse_mask_np))
        if coarse_coverage > 0:
            coverage_ratio = foreground_coverage_ratio / coarse_coverage
            if coverage_ratio < 0.85:
                issue_codes.append("REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )
            elif coverage_ratio > 1.15:
                issue_codes.append("REFINEMENT_FOREGROUND_EXPANDED_EXCESSIVELY")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_EXPANDED_EXCESSIVELY,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        # 5. Bounding box area shrinkage check
        y_indices, x_indices = np.where(coarse_mask_np)
        bounding_box_before = None
        if len(y_indices) > 0:
            bounding_box_before = BoundingBox(
                left=float(x_indices.min()),
                top=float(y_indices.min()),
                right=float(x_indices.max() + 1),
                bottom=float(y_indices.max() + 1),
            )

        ref_y, ref_x = np.where(refined_arr > 127)
        bounding_box_after = None
        if len(ref_y) > 0:
            bounding_box_after = BoundingBox(
                left=float(ref_x.min()),
                top=float(ref_y.min()),
                right=float(ref_x.max() + 1),
                bottom=float(ref_y.max() + 1),
            )

        if bounding_box_before is not None and bounding_box_after is not None:
            bbox_ratio = bounding_box_after.area / bounding_box_before.area
            if bbox_ratio < 0.85:
                if "REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY" not in issue_codes:
                    issue_codes.append("REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY")
                    issues.append(
                        RefinementValidationIssue(
                            code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY,
                            severity=IssueSeverity.WARNING,
                            blocking_for_processing=False,
                            confidence=1.0,
                        )
                    )

        # 6. Face coverage dropped check
        img_w, img_h = coarse_mask_pil.size
        face_coverage_before = None
        face_coverage_after = None
        face_coverage_delta = None

        if face is not None:
            faces_list = face if isinstance(face, list) else [face]
            if len(faces_list) > 1:
                issue_codes.append("SUITABILITY_MULTIPLE_FACES")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES,
                        severity=IssueSeverity.ERROR,
                        blocking_for_processing=True,
                        confidence=1.0,
                    )
                )
            if faces_list:
                f = faces_list[0]
                face_box = f.bounding_box
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(img_w, img_h)

                ymin, ymax = (
                    max(0, int(round(face_box.top))),
                    min(img_h, int(round(face_box.bottom))),
                )
                xmin, xmax = (
                    max(0, int(round(face_box.left))),
                    min(img_w, int(round(face_box.right))),
                )
                if ymax > ymin and xmax > xmin:
                    coarse_face_pixels = coarse_mask_np[ymin:ymax, xmin:xmax].sum()
                    refined_face_pixels = (
                        refined_arr[ymin:ymax, xmin:xmax] > 127
                    ).sum()
                    total_face_box_pixels = (ymax - ymin) * (xmax - xmin)
                    face_coverage_before = float(
                        coarse_face_pixels / total_face_box_pixels
                    )
                    face_coverage_after = float(
                        refined_face_pixels / total_face_box_pixels
                    )
                    face_coverage_delta = face_coverage_after - face_coverage_before

                    if coarse_face_pixels > 0:
                        face_ratio = refined_face_pixels / coarse_face_pixels
                        if face_ratio < 0.98:
                            issue_codes.append("REFINEMENT_FACE_COVERAGE_DROPPED")
                            issues.append(
                                RefinementValidationIssue(
                                    code=SuitabilityIssueCode.REFINEMENT_FACE_COVERAGE_DROPPED,
                                    severity=IssueSeverity.WARNING,
                                    blocking_for_processing=False,
                                    confidence=1.0,
                                )
                            )

                    # Central face protection check (inner 80% of face box must drop <= 1%)
                    face_w = face_box.right - face_box.left
                    face_h = face_box.bottom - face_box.top
                    c_ymin = max(0, int(round(face_box.top + face_h * 0.1)))
                    c_ymax = min(img_h, int(round(face_box.bottom - face_h * 0.1)))
                    c_xmin = max(0, int(round(face_box.left + face_w * 0.1)))
                    c_xmax = min(img_w, int(round(face_box.right - face_w * 0.1)))
                    if c_ymax > c_ymin and c_xmax > c_xmin:
                        coarse_c_face = coarse_mask_np[
                            c_ymin:c_ymax, c_xmin:c_xmax
                        ].sum()
                        refined_c_face = (
                            refined_arr[c_ymin:c_ymax, c_xmin:c_xmax] > 127
                        ).sum()
                        if coarse_c_face > 0:
                            c_ratio = refined_c_face / coarse_c_face
                            if c_ratio < 0.99:
                                if (
                                    "REFINEMENT_FACE_COVERAGE_DROPPED"
                                    not in issue_codes
                                ):
                                    issue_codes.append(
                                        "REFINEMENT_FACE_COVERAGE_DROPPED"
                                    )
                                    issues.append(
                                        RefinementValidationIssue(
                                            code=SuitabilityIssueCode.REFINEMENT_FACE_COVERAGE_DROPPED,
                                            severity=IssueSeverity.WARNING,
                                            blocking_for_processing=False,
                                            confidence=1.0,
                                        )
                                    )

        # 7. Head-region coverage dropped check
        head_region_coverage_before = None
        head_region_coverage_after = None
        head_region_coverage_delta = None

        h_box = head_estimate
        if h_box is None and face is not None:
            faces_list = face if isinstance(face, list) else [face]
            if faces_list:
                f = faces_list[0]
                face_box = f.bounding_box
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(img_w, img_h)
                face_w = face_box.right - face_box.left
                face_h = face_box.bottom - face_box.top
                # Estimate provisional head region from face
                h_box = BoundingBox(
                    left=max(0.0, face_box.left - face_w * 0.2),
                    top=max(0.0, face_box.top - face_h * 0.5),
                    right=min(float(img_w), face_box.right + face_w * 0.2),
                    bottom=min(float(img_h), face_box.bottom + face_h * 0.1),
                )

        if h_box is not None:
            if (
                h_box.left >= 0.0
                and h_box.right <= 1.0
                and h_box.top >= 0.0
                and h_box.bottom <= 1.0
                and (h_box.right - h_box.left) < 1.0
            ):
                h_box = h_box.to_pixel(img_w, img_h)

            h_ymin, h_ymax = (
                max(0, int(round(h_box.top))),
                min(img_h, int(round(h_box.bottom))),
            )
            h_xmin, h_xmax = (
                max(0, int(round(h_box.left))),
                min(img_w, int(round(h_box.right))),
            )
            if h_ymax > h_ymin and h_xmax > h_xmin:
                coarse_head_pixels = coarse_mask_np[h_ymin:h_ymax, h_xmin:h_xmax].sum()
                refined_head_pixels = (
                    refined_arr[h_ymin:h_ymax, h_xmin:h_xmax] > 127
                ).sum()
                total_head_pixels = (h_ymax - h_ymin) * (h_xmax - h_xmin)
                head_region_coverage_before = float(
                    coarse_head_pixels / total_head_pixels
                )
                head_region_coverage_after = float(
                    refined_head_pixels / total_head_pixels
                )
                head_region_coverage_delta = (
                    head_region_coverage_after - head_region_coverage_before
                )

                if coarse_head_pixels > 0:
                    head_ratio = refined_head_pixels / coarse_head_pixels
                    if head_ratio < 0.85:
                        issue_codes.append("REFINEMENT_HEAD_REGION_COVERAGE_DROPPED")
                        issues.append(
                            RefinementValidationIssue(
                                code=SuitabilityIssueCode.REFINEMENT_HEAD_REGION_COVERAGE_DROPPED,
                                severity=IssueSeverity.ERROR,
                                blocking_for_processing=True,
                                confidence=1.0,
                            )
                        )
                    elif head_ratio < 0.95:
                        issue_codes.append("REFINEMENT_HEAD_REGION_COVERAGE_DROPPED")
                        issues.append(
                            RefinementValidationIssue(
                                code=SuitabilityIssueCode.REFINEMENT_HEAD_REGION_COVERAGE_DROPPED,
                                severity=IssueSeverity.WARNING,
                                blocking_for_processing=False,
                                confidence=1.0,
                            )
                        )

        # 8. Connected components/Subject fragmented
        if refined_cc > 1:
            issue_codes.append("REFINEMENT_SUBJECT_FRAGMENTED")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_SUBJECT_FRAGMENTED,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 9. Large internal holes
        hole_count, max_hole_size = _find_internal_holes(refined_arr)
        largest_hole_ratio = (
            float(max_hole_size / refined_alpha_mask.size)
            if refined_alpha_mask.size > 0
            else 0.0
        )
        large_hole_count = 0
        if hole_count > 0 and max_hole_size > 1000:
            large_hole_count = hole_count
            issue_codes.append("REFINEMENT_LARGE_INTERNAL_HOLE")
            issue_codes.append("REFINEMENT_LARGE_HOLES_DETECTED")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_LARGE_INTERNAL_HOLE,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_LARGE_HOLES_DETECTED,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 10. Excessive transition edge band
        unknown_trimap_ratio = (
            float(np.sum(trimap_arr == 128) / trimap_arr.size)
            if trimap_arr.size > 0
            else 0.0
        )
        definite_foreground_ratio = (
            float(np.sum(trimap_arr == 255) / trimap_arr.size)
            if trimap_arr.size > 0
            else 0.0
        )
        definite_background_ratio = (
            float(np.sum(trimap_arr == 0) / trimap_arr.size)
            if trimap_arr.size > 0
            else 0.0
        )

        if edge_transition_ratio > 0.15 or unknown_trimap_ratio > 0.15:
            issue_codes.append("REFINEMENT_UNKNOWN_REGION_EXCESSIVE")
            issue_codes.append("REFINEMENT_EDGE_BAND_EXCESSIVE")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_UNKNOWN_REGION_EXCESSIVE,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_EDGE_BAND_EXCESSIVE,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 11. Coarse IoU check
        if coarse_iou < 0.90:
            if "REFINEMENT_COARSE_IOU_LOW" not in issue_codes:
                issue_codes.append("REFINEMENT_COARSE_IOU_LOW")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_COARSE_IOU_LOW,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        if abs(foreground_coverage_ratio - coarse_coverage) > 0.15:
            if "REFINEMENT_COVERAGE_DIVERGED" not in issue_codes:
                issue_codes.append("REFINEMENT_COVERAGE_DIVERGED")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_COVERAGE_DIVERGED,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        is_valid = (
            len([iss for iss in issues if iss.severity == IssueSeverity.ERROR]) == 0
        )

        return RefinedMaskValidationReport(
            is_valid=is_valid,
            foreground_coverage_before=coarse_coverage,
            foreground_coverage_after=foreground_coverage_ratio,
            foreground_coverage_delta=foreground_coverage_ratio - coarse_coverage,
            coarse_iou=coarse_iou,
            edge_transition_ratio=edge_transition_ratio,
            unknown_trimap_ratio=unknown_trimap_ratio,
            definite_foreground_ratio=definite_foreground_ratio,
            definite_background_ratio=definite_background_ratio,
            connected_components_before=coarse_cc,
            connected_components_after=refined_cc,
            connectivity_improvement=connectivity_improvement,
            face_coverage_before=face_coverage_before,
            face_coverage_after=face_coverage_after,
            face_coverage_delta=face_coverage_delta,
            head_region_coverage_before=head_region_coverage_before,
            head_region_coverage_after=head_region_coverage_after,
            head_region_coverage_delta=head_region_coverage_delta,
            bounding_box_before=bounding_box_before,
            bounding_box_after=bounding_box_after,
            large_hole_count=large_hole_count,
            largest_hole_ratio=largest_hole_ratio,
            issue_codes=issue_codes,
            issues=issues,
        )
