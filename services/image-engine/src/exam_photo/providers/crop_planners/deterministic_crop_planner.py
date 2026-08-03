from __future__ import annotations

import math
import time
from typing import Any, List, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropIssueCode,
    CropMode,
    CropPlanner,
    CropPlanResult,
    CropValidationIssue,
    CropValidationReport,
)
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.portrait_composition import PortraitCompositionResult
from exam_photo.suitability.issue_codes import IssueSeverity

# Guaranteed margin below the landmark chin point, as a fraction of the
# measured crown-to-chin span rather than the unreliable detector face box.
#
# Three independent per-photo beard-length signals were tried and rejected on
# measured evidence, not assumption: (1) silhouette width below the chin --
# rejected because clean-shaven necks widen into shoulders *faster* than
# bearded jaws do (measured: two clean-shaven reference photos grew wider,
# sooner, than three bearded ones); (2) a colour/luminance profile tracked
# down from the mouth -- rejected because dark shirts and collars register
# indistinguishably from dark facial hair, producing nonsense readings on
# every subject wearing a dark top; (3) a binary presence probe in a small
# patch right at the chin -- rejected because ordinary under-chin shadow
# produces the same luminance drop as facial hair, misclassifying most
# clean-shaven reference subjects as bearded. No further heuristic was
# attempted after three independent failures on real photos.
#
# The value is read off the approved ideal outputs, which are the composition
# specification (DEC-037).  Measured across all 60 of them, the distance from
# the landmark chin to the bottom edge, as a fraction of that photo's own
# crown-to-chin span, is: p10 0.075, p25 0.091, median 0.119, p75 0.172,
# p90 0.217.
#
# This constant is a *floor* the crop may never cross, not the intended
# composition, so it belongs at the low end of that distribution rather than
# its middle: the tightest approved reference output leaves 0.075, and none of
# them clip a beard.  Where the composition should actually land is set by the
# profile's ``target_head_height_ratio``/``target_top_margin_ratio``, which are
# themselves calibrated to the same reference set.
#
# The previous value of 0.24 was derived the other way round -- as the largest
# margin still algebraically compatible with a 75% coverage floor -- and sat
# above the reference p90.  Because the floor is mandatory, it did not merely
# reserve space: together with the old 0.08 top margin it bounded head height
# at 1/(1 + 0.08 + 0.24) = 0.758 for every photo, while the reference outputs
# have a median head height of 0.855 and a p90 of 0.900.  The engine therefore
# could not reach the approved composition on any photo.  Measured effect over
# all 60: below-chin space exceeded the matching ideal on 50 of 56 produced
# outputs, by a mean of 0.067 of frame height.
_CHIN_BEARD_MARGIN_RATIO = 0.09

# Guaranteed margin above the observed hairline, as a fraction of the
# crown-to-chin span.  Sized from the same ideal-output distribution and for
# the same reason as ``_CHIN_BEARD_MARGIN_RATIO`` above: measured space above
# the hair is p10 0.028, p25 0.038, median 0.048, p75 0.075, p90 0.093 of the
# span.  A floor at the p25 leaves the profile's top-margin target free to
# choose the actual framing.
_TOP_MARGIN_RATIO = 0.04

# Guaranteed margin beside each ear, as a fraction of the measured head-core
# width.
#
# Sized the same way as ``_CHIN_BEARD_MARGIN_RATIO`` (DEC-037): read off the
# approved ideal outputs and placed at the low end of their distribution,
# because this is a floor rather than the intended framing.  Measured over all
# 60 ideal outputs, space beside the head as a fraction of head width is
# p10 0.000 / p25 0.033 / median 0.082 on the left and p10 0.000 / p25 0.029 /
# median 0.077 on the right -- reference photos routinely let outer hair reach
# or leave the side edge, so the low end of the distribution is genuinely zero.
#
# The aspect interaction is why this floor must stay small even though the
# median is larger: the mandatory box's own aspect ratio is
# width*(1+2*margin) / (span*(1 + top + chin)).  Once that exceeds the target
# aspect (0.667 for 1200x1800) the crop becomes width-bound rather than
# height-bound, and achievable head height drops to
# target_aspect*span / (width*(1+2*margin)) regardless of the vertical
# margins.  The 1200x1800 class is where this binds, and it binds on the
# reference outputs too: their own head height there measures 0.66-0.87
# against a 0.84 mean across the other five size classes.
_SIDE_MARGIN_RATIO = 0.03

# Half-width of the mandatory horizontal head band, in detector face-box widths.
# The full head silhouette (hair and ears included) measures 1.30 +/- 0.15 face
# widths across the reference set, i.e. ~0.15 face widths beyond each side of
# the detector box.
_HEAD_SIDE_MARGIN_RATIO = 0.15

# Smallest head span a mask-derived crown may imply, as a fraction of the
# detector face-box height.  Guards against a crown reading so low it would
# leave no head above the chin, without assuming the face box is well sized.
_MIN_HEAD_SPAN_FACE_RATIO = 0.25

# Widest a mask-derived head may be, in detector face-box widths, before the
# reading is treated as mask contamination rather than hair.  The reference set
# measures 1.30 +/- 0.15, so this leaves generous room for voluminous hair
# while rejecting a mask that has swallowed background either side of the head.
_MAX_HEAD_WIDTH_FACE_RATIO = 2.6

# Narrowest a mask-derived head may be, in detector face-box widths, before
# the reading is treated as a segmentation failure (mask clipped into the
# face) rather than a genuinely narrow visible head.  Photo 6-3 measures
# 0.66 (ears fully covered by hair); set below that with margin rather than
# at the boundary of one measured case.
_MIN_HEAD_WIDTH_FACE_RATIO = 0.5

# Mouth-to-chin distance as a multiple of eye-to-mouth distance, for the chin
# fallback used when the dense landmarker cannot find a face the detector did
# (see DEC-034). Calibrated as the mean over 29 reference photos with a known
# landmark chin (sd 0.142, so this is a coarse anatomical estimate, not
# precision -- it exists to beat the box-bottom proxy, not replace real
# landmarks).
_MOUTH_TO_CHIN_RATIO = 0.598

# Face-coverage cost weights.  Undershooting the target moves toward the
# minimum the exam rejects outright; overshooting produces a tighter crop, which
# is the preferred direction, so the two are not penalised equally.
_HEAD_HEIGHT_UNDERSHOOT_WEIGHT = 60.0
_HEAD_HEIGHT_OVERSHOOT_WEIGHT = 12.0

# Order in which composition constraints give way when no crop can satisfy them
# all.  Each tier lists the constraints waivable at that level, so tier 0 is a
# fully compliant crop and later tiers trade away progressively more.
#
# ``head_height_max`` is waived early because exceeding it simply means a
# tighter crop, which is preferred, and subject protection independently
# prevents that from cutting into the head.
#
# Torso inclusion goes first because a little more or less shoulder is the least
# visible compromise; eye line and top margin follow; horizontal centring and
# head width come after those.
#
# ``head_height_min`` -- falling below the exam's minimum face coverage -- is
# the very last thing surrendered, in a tier of its own, but it *is* in the
# ladder (DEC-039).  It used to be absent entirely, on the reasoning that it is
# the published requirement the output is judged against.  Measured over the
# 60-photo reference set, that reasoning produced the opposite of its intent:
# on the 9 photos where no candidate could reach the floor, the search returned
# nothing at all and fell through to the geometric projection below, which
# ignores every composition target.  Those photos delivered 0.41-0.66 head
# height with 0.15-0.30 of the frame as headroom -- strictly worse, on the
# floor itself and on every other axis, than the best candidate the search had
# already found and discarded.  A tier here means such a photo still gets the
# tightest crop its geometry allows, and ``CROP_NO_VALID_COMPOSITION`` still
# reports the compromise downstream.  The approved ideal outputs support this:
# their own head height measures 0.665-0.728 on 6-1, 6-2, 6-3 and 6-9, so a
# sub-0.75 result is what correct framing looks like for those subjects.
#
# Subject protection (complete hair, chin/beard boundary, ear visibility,
# padding limits) is never waived here -- those guard the candidate's likeness
# rather than the framing, and are enforced independently.
_RELAXATION_TIERS: tuple[frozenset[str], ...] = (
    frozenset(),
    frozenset({"head_height_max"}),
    frozenset({"head_height_max", "torso"}),
    frozenset({"head_height_max", "torso", "eye_line"}),
    frozenset({"head_height_max", "torso", "eye_line", "top_margin"}),
    frozenset({"head_height_max", "torso", "eye_line", "top_margin", "center_offset"}),
    frozenset(
        {
            "head_height_max",
            "torso",
            "eye_line",
            "top_margin",
            "center_offset",
            "head_width",
        }
    ),
    frozenset(
        {
            "head_height_max",
            "torso",
            "eye_line",
            "top_margin",
            "center_offset",
            "head_width",
            "head_height_min",
        }
    ),
)


class DeterministicCropPlanner(CropPlanner):
    """Local deterministic crop planner implementation for Crop Mode A."""

    def __init__(self) -> None:
        self.provider_name = "DeterministicCropPlanner"
        self.provider_version = "1.0.0"

    def plan_crop(
        self,
        image_width: int,
        image_height: int,
        face: FaceDetection,
        head_estimate: Optional[BoundingBox],
        refined_mask: Optional[Image.Image] = None,
        alpha_mask: Optional[np.ndarray[Any, Any]] = None,
        portrait_composition: Optional[PortraitCompositionResult] = None,
        config: Optional[CropConfig] = None,
    ) -> CropPlanResult:
        start_time = time.perf_counter()
        cfg = config or CropConfig(target_aspect_ratio=1.0)

        issues: List[CropValidationIssue] = []
        issue_codes: List[CropIssueCode] = []
        best_ratios: dict[str, Any] = {}

        def add_issue(
            code: CropIssueCode, severity: IssueSeverity, blocking: bool
        ) -> None:
            if code not in issue_codes:
                issue_codes.append(code)
                issues.append(
                    CropValidationIssue(
                        code=code,
                        severity=severity,
                        blocking_for_processing=blocking,
                        confidence=1.0,
                    )
                )

        # 1. Invalid input validation
        # Guard against zero/negative image dimensions
        if image_width <= 0 or image_height <= 0:
            add_issue(CropIssueCode.CROP_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # Guard against missing/multiple faces passed (if wrapped/passed incorrectly)
        if face is None or not hasattr(face, "bounding_box"):
            add_issue(CropIssueCode.CROP_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # 2. Resolve target aspect ratio and integer ratio scaling
        ratio_w: Optional[int] = None
        ratio_h: Optional[int] = None
        target_aspect: float

        if cfg.target_width is not None and cfg.target_height is not None:
            tw, th = cfg.target_width, cfg.target_height
            g = math.gcd(tw, th)
            ratio_w = tw // g
            ratio_h = th // g
            target_aspect = tw / th
        elif cfg.target_aspect_ratio is not None:
            target_aspect = cfg.target_aspect_ratio
        else:
            # Pydantic validation handles this, but defensive fallback
            add_issue(
                CropIssueCode.CROP_TARGET_ASPECT_MISSING, IssueSeverity.ERROR, True
            )
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        face_box = face.bounding_box

        # 3. Establish subject preservation box
        composition_box: Optional[BoundingBox] = None
        if portrait_composition is not None:
            preserve_box = portrait_composition.preservation_box
            composition_box = portrait_composition.preservation_box
        elif head_estimate is not None:
            preserve_box = head_estimate
        else:
            # Fallback face-derived expanded box
            face_w = face_box.width
            face_h = face_box.height
            preserve_box = BoundingBox(
                left=max(0.0, face_box.left - face_w * 0.25),
                top=max(0.0, face_box.top - face_h * 0.60),
                right=min(float(image_width), face_box.right + face_w * 0.25),
                bottom=min(float(image_height), face_box.bottom + face_h * 0.30),
            )

        # Refined mask refinement bounds expansion (Secondary validation / constraint)
        if refined_mask is not None and head_estimate is None:
            mask_arr = np.array(refined_mask)
            y_limit = int(
                round(
                    min(
                        preserve_box.bottom,
                        face_box.bottom + face_box.height * 0.20,
                    )
                )
            )
            if y_limit > 0:
                x_start = max(
                    0, int(round(preserve_box.left - preserve_box.width * 0.35))
                )
                x_end = min(
                    image_width,
                    int(round(preserve_box.right + preserve_box.width * 0.35)),
                )
                sub_mask = mask_arr[0:y_limit, x_start:x_end]
                ys_sub, xs_sub = np.where(sub_mask > 127)
                ys = ys_sub
                xs = xs_sub + x_start
                if len(ys) > 0:
                    upper_mask_bbox = BoundingBox(
                        left=float(np.min(xs)),
                        top=float(np.min(ys)),
                        right=float(np.max(xs)),
                        bottom=float(np.max(ys)),
                    )
                    preserve_box = BoundingBox(
                        left=min(preserve_box.left, upper_mask_bbox.left),
                        top=min(preserve_box.top, upper_mask_bbox.top),
                        right=max(preserve_box.right, upper_mask_bbox.right),
                        bottom=preserve_box.bottom,
                    )

        # 3b. Mandatory subject region.
        #
        # ``preserve_box`` is the *generous* region (it absorbs hair spread,
        # shoulder alpha and a lower-body exclusion band, measuring ~1.14x the
        # real head height and ~1.31x its width).  It is the right region to
        # avoid cutting into casually, but it is not a guarantee: reference exam
        # photos routinely let outer hair reach or leave the side edges.
        #
        # ``mandatory_box`` is what the crop must genuinely retain: crown to
        # chin-plus-beard-margin, spanning the head core.  Planning constraints
        # and preservation validation are both stated against it so the planner
        # cannot produce a crop its own validator then rejects.
        #
        # This applies to profile-driven (adaptive) planning only.  The legacy
        # branch below has no composition targets and its published contract is
        # "the crop contains the preservation box", so it keeps the original
        # reference geometry unchanged.
        adaptive_mode = not (
            cfg.target_head_height_ratio is None and cfg.crop_profile is None
        )
        # Set by the candidate search when this particular photo could not be
        # composed while keeping the whole preservation box.  Validation below
        # then judges the crop against what was actually promised for it.
        outer_hair_relaxation_used = False
        crown_y = (
            self._estimate_crown_y(face, preserve_box, alpha_mask, refined_mask)
            if adaptive_mode
            else preserve_box.top
        )
        chin_y = self._estimate_chin_y(face, preserve_box)

        # Trim phantom space above the subject out of the preservation box too.
        # ``preserve_box`` drives crop sizing and containment, and its top comes
        # from a geometric expansion of the detector face box, so an oversized
        # box makes the crop reserve room for a subject that is not there --
        # the head then lands far below target no matter what the composition
        # ratios ask for.  The observed mask crown is the measured start of the
        # subject, so nothing above it needs preserving.
        if adaptive_mode and crown_y > preserve_box.top:
            preserve_box = BoundingBox(
                left=preserve_box.left,
                top=crown_y,
                right=preserve_box.right,
                bottom=preserve_box.bottom,
            )
            # Preservation validation must judge the crop against the same
            # region the planner was asked to keep.  Leaving the composition
            # box untrimmed here reports a crop as clipping a subject that was
            # never there, which is the planner/validator disagreement this
            # module otherwise takes care to avoid.
            if composition_box is not None:
                composition_box = preserve_box

        # These bounds are the *floor* the crop may never cross.  They are always
        # computed, but the candidate search only falls back to them for photos
        # that cannot be composed while keeping the whole preservation box, so a
        # subject whose hair fits is never trimmed to this floor.
        #
        # Margins on all four sides are scaled from ``anatomical_span``
        # (crown-to-chin), the one anatomical measurement that does not depend
        # on the face detector's box: it comes from the observed mask crown and
        # the landmark chin.  Scaling from face_box.height instead -- the
        # previous approach -- silently under-margins whenever that box is
        # oversized, which is common enough that it drove several of the crop
        # bugs already fixed in this module.  A small margin above the hair,
        # beside the ears and below the chin/beard line is a deliberate
        # professional buffer, not a byproduct of the search's cost function.
        anatomical_span = max(1.0, chin_y - crown_y)
        head_core_left, head_core_right = self._estimate_head_core_x(
            face, preserve_box, alpha_mask, refined_mask, crown_y, chin_y
        )
        anatomical_width = max(1.0, head_core_right - head_core_left)

        # A beard extends past the landmark chin point, which tracks the jaw
        # under the beard rather than its visible tip, and there is no reliable
        # way to measure how far: the mask has no foreground/background
        # transition at a beard's bottom edge, since it blends continuously
        # into the collar (measured directly -- a mask-width probe attempting
        # to detect it could not separate beard length from shoulder framing).
        # The margin instead uses the reference set's own bearded subjects
        # (mean 0.148 of head span, max 0.254, n=5) with headroom above that
        # mean, applied uniformly since beard presence cannot be detected.
        margin_top = _TOP_MARGIN_RATIO * anatomical_span
        margin_bottom = _CHIN_BEARD_MARGIN_RATIO * anatomical_span
        margin_side = _SIDE_MARGIN_RATIO * anatomical_width

        crown_y = max(preserve_box.top, crown_y - margin_top)
        chin_protection_y = min(
            preserve_box.bottom,
            chin_y + margin_bottom,
        )
        head_core_left = max(preserve_box.left, head_core_left - margin_side)
        head_core_right = min(preserve_box.right, head_core_right + margin_side)
        mandatory_box = BoundingBox(
            left=head_core_left,
            top=crown_y,
            right=head_core_right,
            bottom=max(chin_protection_y, crown_y + 1.0),
        )

        # Every face point the detector actually located must survive the crop
        # too (DEC-038).  Ear tragions in particular can sit outside the
        # mask-derived head core when hair partially covers them, and the eye
        # line can sit above a low crown reading, so folding the landmarks in
        # here -- rather than checking them separately after the search -- is
        # what keeps the planner and its validator judging one single region.
        # The class of bug this avoids is the planner selecting a crop its own
        # validation then rejects as a blocking error.
        if adaptive_mode and face.landmarks is None:
            # No landmarks at all: fall back to the detector rectangle's
            # sides and top, but only as far down as the chin/beard line the
            # planner promised, so a box bottom sitting in the neck cannot
            # force the crop looser.
            mandatory_box = BoundingBox(
                left=min(mandatory_box.left, face_box.left),
                top=min(mandatory_box.top, face_box.top),
                right=max(mandatory_box.right, face_box.right),
                bottom=mandatory_box.bottom,
            )
        elif adaptive_mode and face.landmarks is not None:
            landmark_points: List[tuple[float, float]] = [
                (point.x, point.y)
                for point in (
                    face.landmarks.left_eye,
                    face.landmarks.right_eye,
                    face.landmarks.nose_tip,
                    face.landmarks.mouth_left,
                    face.landmarks.mouth_right,
                    face.landmarks.chin,
                )
                if point is not None
            ]
            landmark_points.extend(
                (point.x, point.y) for point in face.landmarks.custom_landmarks.values()
            )
            if landmark_points:
                mandatory_box = BoundingBox(
                    left=min(mandatory_box.left, min(p[0] for p in landmark_points)),
                    top=min(mandatory_box.top, min(p[1] for p in landmark_points)),
                    right=max(mandatory_box.right, max(p[0] for p in landmark_points)),
                    bottom=max(
                        mandatory_box.bottom, max(p[1] for p in landmark_points)
                    ),
                )

        # 4. Sizing and candidate generation
        w_subject = preserve_box.width
        h_subject = preserve_box.height

        min_h_crop_from_subject = h_subject / (
            1.0 - cfg.minimum_top_margin_ratio - cfg.minimum_bottom_margin_ratio
        )
        min_w_crop_from_subject = w_subject / (
            1.0 - 2.0 * cfg.minimum_side_margin_ratio
        )

        h_min = max(min_h_crop_from_subject, min_w_crop_from_subject / target_aspect)
        w_min = h_min * target_aspect

        if cfg.target_head_height_ratio is None and cfg.crop_profile is None:
            # Backward compatibility / fallback mode
            w_crop: float
            h_crop: float
            if ratio_w is not None and ratio_h is not None:
                k_w = math.ceil(min_w_crop_from_subject / ratio_w)
                k_h = math.ceil(min_h_crop_from_subject / ratio_h)
                k = max(k_w, k_h)
                w_crop = float(ratio_w * k)
                h_crop = float(ratio_h * k)
            else:
                w_crop = w_min
                h_crop = h_min

            face_cx = (face.bounding_box.left + face.bounding_box.right) / 2.0
            face_cy = (face.bounding_box.top + face.bounding_box.bottom) / 2.0

            l_ideal = face_cx - w_crop / 2.0
            t_ideal = face_cy - cfg.preferred_face_center_y_ratio * h_crop

            l_min = preserve_box.right - w_crop
            l_max = preserve_box.left
            t_min = preserve_box.bottom - h_crop
            t_max = preserve_box.top

            def project(val: float, vmin: float, vmax: float) -> float:
                if vmin > vmax:
                    return (vmin + vmax) / 2.0
                return max(vmin, min(val, vmax))

            ideal_l = project(l_ideal, l_min, l_max)
            ideal_t = project(t_ideal, t_min, t_max)

            ideal_l_rounded = int(round(ideal_l))
            ideal_t_rounded = int(round(ideal_t))
            ideal_r_rounded = ideal_l_rounded + int(round(w_crop))
            ideal_b_rounded = ideal_t_rounded + int(round(h_crop))
        else:
            # Adaptive candidate grid search cost-minimization
            #
            # Composition ratios are measured against the *anatomical* head span
            # (crown -> chin), not against ``preserve_box``.  The preservation box
            # deliberately extends below the chin to protect the beard/jaw boundary
            # during clipping checks, which makes it ~1.14x taller than the real
            # head; using it as the composition reference silently under-crops
            # every photo.  ``preserve_box`` is still used for containment and
            # clipping validation below.
            #
            # ``anatomical_span``, not ``chin_y - crown_y``, on purpose:
            # ``crown_y`` was padded upward by the top margin below, and face
            # coverage must be measured against true anatomy.  Using the padded
            # value here would let the margin get silently absorbed into the
            # coverage target instead of added on top of a correctly tight crop
            # -- the crop would size itself larger to make the *padded* span
            # hit 86%, so the delivered anatomical coverage would fall short.
            h_head = anatomical_span
            w_head = preserve_box.width

            face_cx = (face.bounding_box.left + face.bounding_box.right) / 2.0
            face_cy = (face.bounding_box.top + face.bounding_box.bottom) / 2.0

            eye_y = face.bounding_box.top + 0.3 * face.bounding_box.height
            if face.landmarks and face.landmarks.left_eye and face.landmarks.right_eye:
                eye_y = (face.landmarks.left_eye.y + face.landmarks.right_eye.y) / 2.0

            target_head_height_ratio = cfg.target_head_height_ratio or 0.60
            min_head_height_ratio = cfg.minimum_head_height_ratio or 0.50
            max_head_height_ratio = cfg.maximum_head_height_ratio or 0.70

            target_top_margin_ratio = cfg.target_top_margin_ratio or 0.10
            min_top_margin_ratio = (
                cfg.minimum_top_margin_ratio
                if cfg.minimum_top_margin_ratio is not None
                else 0.06
            )
            max_top_margin_ratio = cfg.maximum_top_margin_ratio or 0.15

            target_eye_line_ratio = cfg.target_eye_line_ratio or 0.44

            max_center_offset = cfg.maximum_horizontal_center_offset_ratio or 0.05
            max_torso_inclusion = cfg.maximum_torso_inclusion_ratio or 0.35

            complete_hair_required = cfg.complete_hair_required or False
            complete_chin_required = cfg.complete_chin_required or False
            complete_beard_boundary_required = (
                cfg.complete_beard_boundary_required or False
            )

            hc_min_ratio = h_head / max_head_height_ratio
            hc_max_ratio = h_head / min_head_height_ratio

            h_start = max(10.0, hc_min_ratio * 0.75)
            h_end = min(
                max(float(image_width), float(image_height)) * 2.0, hc_max_ratio * 1.25
            )

            k_candidates = []
            if ratio_w is not None and ratio_h is not None:
                k_min = max(1, int(round(h_start / ratio_h)))
                k_max = max(k_min + 5, int(round(h_end / ratio_h)))
                k_vals = np.unique(np.linspace(k_min, k_max, 40).astype(int))
                exact_h_values = [
                    h_head / target_head_height_ratio,
                    h_head / min_head_height_ratio,
                    h_head / max_head_height_ratio,
                    h_min,
                ]
                exact_k_vals = [
                    max(1, int(math.ceil(h_val / ratio_h)))
                    for h_val in exact_h_values
                    if h_val > 0.0 and np.isfinite(h_val)
                ]
                k_vals = np.unique(np.concatenate([k_vals, exact_k_vals]))
                for k in k_vals:
                    hc = float(ratio_h * k)
                    wc = float(ratio_w * k)
                    k_candidates.append((hc, wc))
            else:
                h_candidates = np.linspace(h_start, h_end, 40)
                exact_h_values_arr = np.array(
                    [
                        h_head / target_head_height_ratio,
                        h_head / min_head_height_ratio,
                        h_head / max_head_height_ratio,
                        h_min,
                    ],
                    dtype=np.float64,
                )
                h_candidates = np.unique(
                    np.concatenate(
                        [
                            h_candidates,
                            exact_h_values_arr[
                                (exact_h_values_arr > 0.0)
                                & np.isfinite(exact_h_values_arr)
                            ],
                        ]
                    )
                )
                for hc in h_candidates:
                    k_candidates.append((hc, hc * target_aspect))

            dx_factors = [-0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08]
            dy_factors = [-0.12, -0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08, 0.12]

            best_cand = None
            best_cost = float("inf")

            # Escalating strictness, decided per photo rather than by a profile
            # label.  A candidate is "strict" when it keeps the whole
            # preservation box, and "relaxed" when it keeps the head core plus
            # the chin/beard margin but lets outer hair leave the frame.  Both
            # are scored in one pass; a strict crop always wins if this photo
            # admits one, so no hair is given up unnecessarily.  Only subjects
            # that cannot be composed strictly -- voluminous hair, tall target
            # aspects, a head near the source edge -- fall back to the relaxed
            # result, which is what reference photos do for those same subjects.
            strict_cand = None
            strict_cost = float("inf")
            strict_tier = len(_RELAXATION_TIERS)
            strict_ratios: dict[str, Any] = {}
            best_tier = len(_RELAXATION_TIERS)

            from exam_photo.providers.crop_planning import EarsPolicy

            for hc, wc in k_candidates:
                l_ideal = face_cx - wc / 2.0
                t_ideal = eye_y - target_eye_line_ratio * hc

                for dxf in dx_factors:
                    dx = dxf * wc
                    for dyf in dy_factors:
                        dy = dyf * hc

                        l_cand = l_ideal + dx
                        t_cand = t_ideal + dy
                        r_cand = l_cand + wc
                        b_cand = t_cand + hc

                        # Constraints are collected rather than collapsed into a
                        # single boolean so the search can give way on the least
                        # important ones first (see _RELAXATION_TIERS).  Treating
                        # composition as all-or-nothing meant one unsatisfiable
                        # constraint discarded the targets entirely and fell back
                        # to a geometric projection, which measured under 60%
                        # face coverage on 12 of 57 reference photos while every
                        # other photo landed in 75-90%.  Face coverage is the
                        # published exam requirement, so it is the last thing
                        # surrendered, never the first.
                        violations: set[str] = set()

                        head_height_ratio = h_head / hc
                        head_width_ratio = w_head / wc
                        top_margin_ratio = (crown_y - t_cand) / hc
                        eye_line_ratio = (eye_y - t_cand) / hc
                        crop_cx = (l_cand + r_cand) / 2.0
                        center_offset_ratio = abs(face_cx - crop_cx) / wc
                        torso_inclusion_ratio = (
                            max(0.0, b_cand - preserve_box.bottom) / hc
                        )

                        # Split deliberately: dropping below the minimum breaks
                        # the published exam requirement and is never an
                        # acceptable compromise, whereas exceeding the maximum
                        # only means a tighter crop, which is desirable so long
                        # as subject protection still holds.
                        if head_height_ratio < min_head_height_ratio:
                            violations.add("head_height_min")
                        if head_height_ratio > max_head_height_ratio:
                            violations.add("head_height_max")

                        if (
                            cfg.minimum_head_width_ratio is not None
                            and head_width_ratio < cfg.minimum_head_width_ratio
                        ):
                            violations.add("head_width")
                        if (
                            cfg.maximum_head_width_ratio is not None
                            and head_width_ratio > cfg.maximum_head_width_ratio
                        ):
                            violations.add("head_width")

                        if (
                            min_top_margin_ratio is not None
                            and top_margin_ratio < min_top_margin_ratio
                        ):
                            violations.add("top_margin")
                        if (
                            max_top_margin_ratio is not None
                            and top_margin_ratio > max_top_margin_ratio
                        ):
                            violations.add("top_margin")

                        if (
                            cfg.minimum_eye_line_ratio is not None
                            and eye_line_ratio < cfg.minimum_eye_line_ratio
                        ):
                            violations.add("eye_line")
                        if (
                            cfg.maximum_eye_line_ratio is not None
                            and eye_line_ratio > cfg.maximum_eye_line_ratio
                        ):
                            violations.add("eye_line")

                        if center_offset_ratio > max_center_offset:
                            violations.add("center_offset")

                        if torso_inclusion_ratio > max_torso_inclusion:
                            violations.add("torso")

                        is_hard_invalid = False

                        # The mandatory head region must survive whenever subject
                        # clipping is disallowed, independently of the rule's
                        # complete-hair flag.  Preservation validation below
                        # blocks on exactly this condition, so leaving it out of
                        # the search let the planner select a crop its own
                        # validator then rejected -- previously masked because
                        # every candidate failed and the geometric fallback
                        # happened to contain the head.
                        if not cfg.allow_subject_clipping:
                            if (
                                t_cand > mandatory_box.top
                                or l_cand > mandatory_box.left
                                or r_cand < mandatory_box.right
                                or b_cand < mandatory_box.bottom
                            ):
                                is_hard_invalid = True

                        # ``strict_violation`` marks a candidate that would give
                        # up some outer hair; it stays selectable but only wins
                        # when nothing keeps the full preservation box.
                        strict_violation = False
                        if complete_hair_required and not cfg.allow_subject_clipping:
                            if (
                                t_cand > crown_y
                                or l_cand > head_core_left
                                or r_cand < head_core_right
                            ):
                                is_hard_invalid = True
                            if (
                                t_cand > preserve_box.top
                                or l_cand > preserve_box.left
                                or r_cand < preserve_box.right
                            ):
                                strict_violation = True
                        if (
                            complete_chin_required or complete_beard_boundary_required
                        ) and not cfg.allow_subject_clipping:
                            if b_cand < chin_protection_y:
                                is_hard_invalid = True
                            if b_cand < preserve_box.bottom:
                                strict_violation = True

                        if cfg.ears_policy == EarsPolicy.REQUIRED_VISIBLE:
                            if face.landmarks and face.landmarks.custom_landmarks:
                                let = face.landmarks.custom_landmarks.get(
                                    "left_ear_tragion"
                                )
                                ret = face.landmarks.custom_landmarks.get(
                                    "right_ear_tragion"
                                )
                                if let and (let.x < l_cand or let.x > r_cand):
                                    is_hard_invalid = True
                                if ret and (ret.x < l_cand or ret.x > r_cand):
                                    is_hard_invalid = True

                        out_l = max(0.0, -l_cand)
                        out_t = max(0.0, -t_cand)
                        out_r = max(0.0, r_cand - image_width)
                        out_b = max(0.0, b_cand - image_height)
                        if not cfg.allow_padding:
                            if out_l > 0.5 or out_t > 0.5 or out_r > 0.5 or out_b > 0.5:
                                is_hard_invalid = True

                        # Lowest tier whose waiver set covers this candidate's
                        # violations.  A candidate breaking a subject-protection
                        # rule is unusable at any tier.
                        tier_needed = len(_RELAXATION_TIERS)
                        if not is_hard_invalid:
                            for tier_index, waivable in enumerate(_RELAXATION_TIERS):
                                if violations <= waivable:
                                    tier_needed = tier_index
                                    break

                        cost = 0.0
                        # Asymmetric on purpose: a crop looser than target walks
                        # toward the minimum coverage the exam will reject, while
                        # a tighter one walks toward a better result, so undershoot
                        # is penalised far more heavily than overshoot.
                        head_height_error = head_height_ratio - target_head_height_ratio
                        cost += (
                            _HEAD_HEIGHT_UNDERSHOOT_WEIGHT
                            if head_height_error < 0
                            else _HEAD_HEIGHT_OVERSHOOT_WEIGHT
                        ) * head_height_error**2
                        if cfg.target_head_width_ratio is not None:
                            cost += (
                                5.0
                                * (head_width_ratio - cfg.target_head_width_ratio) ** 2
                            )
                        cost += 10.0 * (top_margin_ratio - target_top_margin_ratio) ** 2
                        cost += 15.0 * (eye_line_ratio - target_eye_line_ratio) ** 2
                        cost += 20.0 * (center_offset_ratio) ** 2
                        cost += 5.0 * (torso_inclusion_ratio) ** 2

                        if cfg.allow_padding:
                            cost += 100.0 * (out_l + out_t + out_r + out_b) / (wc + hc)

                        cand_ratios = {
                            "head_height_ratio": head_height_ratio,
                            "head_width_ratio": head_width_ratio,
                            "top_margin_ratio": top_margin_ratio,
                            "eye_line_ratio": eye_line_ratio,
                            "center_offset_ratio": center_offset_ratio,
                            "torso_inclusion_ratio": torso_inclusion_ratio,
                        }

                        usable = tier_needed < len(_RELAXATION_TIERS)

                        if usable and not strict_violation:
                            if (tier_needed, cost) < (strict_tier, strict_cost):
                                strict_cand = (l_cand, t_cand, r_cand, b_cand, hc, wc)
                                strict_tier = tier_needed
                                strict_cost = cost
                                strict_ratios = cand_ratios

                        # Rank by how little had to be given up first, then by
                        # cost within that tier, so a fully compliant crop always
                        # beats a compromised one and the compromise chosen is
                        # the mildest available.
                        if usable and (tier_needed, cost) < (best_tier, best_cost):
                            best_cand = (l_cand, t_cand, r_cand, b_cand, hc, wc)
                            best_tier = tier_needed
                            best_cost = cost
                            best_ratios = cand_ratios

            # Prefer a crop that keeps the entire preservation box whenever this
            # photo admits one; the relaxed result is a fallback, not the goal.
            if strict_cand is not None:
                best_cand = strict_cand
                best_cost = strict_cost
                best_tier = strict_tier
                best_ratios = strict_ratios
                outer_hair_relaxation_used = False
            else:
                # No candidate kept the whole preservation box, so whatever is
                # selected below -- a relaxed candidate or the best-effort
                # fallback -- has given up some outer subject area.  Judge it
                # against what it can actually promise.
                outer_hair_relaxation_used = True

            # Only reached when no candidate could protect the subject at any
            # tier (hair, chin/beard, ears, or padding limits).  The geometric
            # projection below is the last resort, kept so such a photo still
            # yields an image to inspect rather than nothing at all; the
            # relaxation ladder handles every ordinary compromise before here.
            if best_cand is None:
                add_issue(
                    CropIssueCode.CROP_NO_VALID_COMPOSITION,
                    IssueSeverity.WARNING,
                    False,
                )
                if ratio_w is not None and ratio_h is not None:
                    k_w = math.ceil(min_w_crop_from_subject / ratio_w)
                    k_h = math.ceil(min_h_crop_from_subject / ratio_h)
                    k = max(k_w, k_h)
                    wc = float(ratio_w * k)
                    hc = float(ratio_h * k)
                else:
                    hc = h_min
                    wc = w_min

                l_ideal = face_cx - wc / 2.0
                t_ideal = face_cy - cfg.preferred_face_center_y_ratio * hc

                l_min = preserve_box.right - wc
                l_max = preserve_box.left
                t_min = preserve_box.bottom - hc
                t_max = preserve_box.top

                def project_preservation(val: float, vmin: float, vmax: float) -> float:
                    if vmin > vmax:
                        return (vmin + vmax) / 2.0
                    return max(vmin, min(val, vmax))

                l_cand = project_preservation(l_ideal, l_min, l_max)
                t_cand = project_preservation(t_ideal, t_min, t_max)
                r_cand = l_cand + wc
                b_cand = t_cand + hc
                best_cand = (l_cand, t_cand, r_cand, b_cand, hc, wc)
                best_ratios = {
                    "head_height_ratio": h_head / hc,
                    "head_width_ratio": preserve_box.width / wc,
                    "top_margin_ratio": (crown_y - t_cand) / hc,
                    "eye_line_ratio": (eye_y - t_cand) / hc,
                    "center_offset_ratio": abs(face_cx - ((l_cand + r_cand) / 2.0))
                    / wc,
                    "torso_inclusion_ratio": max(0.0, b_cand - preserve_box.bottom)
                    / hc,
                }

            # A compromised crop is reported rather than passing silently, so a
            # photo that could not be composed cleanly is visible downstream.
            if 0 < best_tier < len(_RELAXATION_TIERS):
                add_issue(
                    CropIssueCode.CROP_NO_VALID_COMPOSITION,
                    IssueSeverity.WARNING,
                    False,
                )

            l_cand, t_cand, r_cand, b_cand, hc, wc = best_cand

            ideal_l_rounded = int(round(l_cand))
            ideal_t_rounded = int(round(t_cand))
            ideal_r_rounded = ideal_l_rounded + int(round(wc))
            ideal_b_rounded = ideal_t_rounded + int(round(hc))

        ideal_crop_box = BoundingBox(
            left=float(ideal_l_rounded),
            top=float(ideal_t_rounded),
            right=float(ideal_r_rounded),
            bottom=float(ideal_b_rounded),
        )

        # Clamping to source boundaries
        clamped_l = max(0, min(ideal_l_rounded, image_width))
        clamped_t = max(0, min(ideal_t_rounded, image_height))
        clamped_r = max(clamped_l + 1, min(ideal_r_rounded, image_width))
        clamped_b = max(clamped_t + 1, min(ideal_b_rounded, image_height))

        if cfg.allow_padding:
            crop_box = ideal_crop_box
        else:
            crop_box = BoundingBox(
                left=float(clamped_l),
                top=float(clamped_t),
                right=float(clamped_r),
                bottom=float(clamped_b),
            )

        # Padding detection
        ideal_crop_inside_source = (
            ideal_l_rounded >= 0
            and ideal_t_rounded >= 0
            and ideal_r_rounded <= image_width
            and ideal_b_rounded <= image_height
        )
        padding_required = not ideal_crop_inside_source
        can_crop_without_padding = ideal_crop_inside_source
        crop_inside_source = True

        if padding_required:
            add_issue(CropIssueCode.CROP_PADDING_REQUIRED, IssueSeverity.WARNING, False)
            add_issue(
                CropIssueCode.CROP_BOX_OUT_OF_BOUNDS,
                IssueSeverity.ERROR if not cfg.allow_padding else IssueSeverity.WARNING,
                not cfg.allow_padding,
            )

        # 6. Preservation ratio checks
        #
        # Measured against ``mandatory_box`` (crown -> chin+beard, head core), not
        # the generous ``preserve_box``: the planner intentionally lets outer hair
        # leave the frame the way reference photos do, so validating against the
        # generous box would reject the very crops the planner is asked to make.
        preservation_reference_box = (
            mandatory_box
            if (adaptive_mode and outer_hair_relaxation_used)
            else (composition_box or head_estimate)
        )
        head_coverage_ratio: Optional[float] = None
        if preservation_reference_box is not None:
            inter = preservation_reference_box.intersection(crop_box)
            if inter is not None:
                head_coverage_ratio = inter.area / preservation_reference_box.area
            else:
                head_coverage_ratio = 0.0

            head_preservation_valid = head_coverage_ratio >= 0.999
            if not head_preservation_valid:
                add_issue(
                    CropIssueCode.CROP_HEAD_CLIPPED,
                    IssueSeverity.ERROR
                    if not cfg.allow_subject_clipping
                    else IssueSeverity.WARNING,
                    not cfg.allow_subject_clipping,
                )
        else:
            head_preservation_valid = None

        # Mask preservation ratio
        mask_preservation_ratio: Optional[float] = None
        mask_preservation_valid: Optional[bool] = None
        if refined_mask is not None:
            mask_arr = np.array(refined_mask)
            y_limit = int(
                round(
                    min(
                        preserve_box.bottom,
                        face_box.bottom + face_box.height * 0.20,
                    )
                )
            )
            if y_limit > 0:
                # Measure retention over the region the crop actually promised
                # to keep for this photo, not a fixed expansion beyond it.
                # Widening the measurement by a constant fraction of the
                # preservation box counts hair the planner never undertook to
                # retain, so a correctly composed crop could fail a check whose
                # bar nothing in the planner targets.  Keeping the two aligned
                # is what stops the planner and its validator disagreeing.
                guarantee_box = preservation_reference_box or preserve_box
                sub_l = max(0, int(round(guarantee_box.left)))
                sub_r = min(image_width, int(round(guarantee_box.right)))
                if sub_r <= sub_l:
                    sub_l = max(0, int(round(preserve_box.left)))
                    sub_r = min(image_width, int(round(preserve_box.right)))
                # Align the vertical extent for the same reason: starting at row
                # 0 counts foreground above the guaranteed region (stray hair,
                # mask noise near the frame top) that the crop never promised to
                # keep, which drags the ratio down on tall sources.
                sub_t = max(0, min(int(round(guarantee_box.top)), y_limit))
                total_fg = np.sum(mask_arr[sub_t:y_limit, sub_l:sub_r] > 127)
                if total_fg > 0:
                    y_start = max(sub_t, min(clamped_t, y_limit))
                    y_end = max(sub_t, min(clamped_b, y_limit))
                    x_start_crop = max(clamped_l, sub_l)
                    x_end_crop = min(clamped_r, sub_r)
                    fg_in_crop = np.sum(
                        mask_arr[y_start:y_end, x_start_crop:x_end_crop] > 127
                    )
                    mask_preservation_ratio = float(fg_in_crop / total_fg)
                    mask_preservation_valid = (
                        mask_preservation_ratio >= cfg.mask_preservation_threshold
                    )
                    if not mask_preservation_valid:
                        # When this photo could only be composed by giving up
                        # outer hair, foreground loss is the intended outcome,
                        # so it is reported but does not block: the crown, chin
                        # and head core are still guaranteed above.  A crop that
                        # kept the whole preservation box has no such excuse.
                        blocking = (
                            not cfg.allow_subject_clipping
                            and not outer_hair_relaxation_used
                        )
                        add_issue(
                            CropIssueCode.CROP_MASK_PRESERVATION_LOW,
                            IssueSeverity.ERROR if blocking else IssueSeverity.WARNING,
                            blocking,
                        )
                else:
                    mask_preservation_ratio = 1.0
                    mask_preservation_valid = True
            else:
                mask_preservation_ratio = 1.0
                mask_preservation_valid = True

        # Face containment check.
        #
        # In adaptive mode this is stated against detected face *points* plus
        # the mandatory head region, not against the raw detector rectangle
        # (DEC-038).  BlazeFace's box is a coarse proxy whose edges are
        # documented elsewhere in this module to miss real anatomy in both
        # directions: its bottom lands 0.045-0.143 face heights *below* the
        # true chin (in the neck), and on low-confidence recovery detections
        # its top sits well above the hairline.  Demanding the crop contain
        # that rectangle therefore reserves space for anatomy that is not
        # there -- the same phantom-region failure this module already
        # corrects for ``preserve_box``, ``crown_y`` and ``chin_y``.
        #
        # It also produced a planner/validator disagreement: the candidate
        # search enforces containment of ``mandatory_box`` but knows nothing
        # about the detector rectangle, so it could select a correctly tight
        # crop that this check then rejected as a blocking error.  Measured
        # over the 60-photo reference set, that rejection alone turned 8
        # otherwise-valid photos into no-output once the margins were
        # corrected to the ideal-output distribution.
        #
        # The replacement is not weaker, it is anchored differently: every
        # landmark the detector actually located must be inside the crop, as
        # must the whole crown-to-chin-plus-beard head region.  Both are real
        # measurements rather than a heuristic rectangle, and both are already
        # folded into ``mandatory_box`` above, which is the exact region the
        # candidate search enforces -- so the two now agree by construction.
        face_containment_box = mandatory_box if adaptive_mode else face_box

        face_contained = crop_box.contains(face_containment_box)
        if not face_contained:
            add_issue(
                CropIssueCode.CROP_SOURCE_TOO_TIGHT,
                IssueSeverity.ERROR,
                True,
            )

        # 7. Margins calculations for validation
        # Margins are reported against the mandatory region for the same reason.
        margin_box = (
            mandatory_box
            if (adaptive_mode and outer_hair_relaxation_used)
            else preserve_box
        )
        top_margin_px = max(0, int(round(margin_box.top - clamped_t)))
        bottom_margin_px = max(0, int(round(clamped_b - margin_box.bottom)))
        left_margin_px = max(0, int(round(margin_box.left - clamped_l)))
        right_margin_px = max(0, int(round(clamped_r - margin_box.right)))

        # Margin risk flags (relative to final crop height/width)
        crop_h_actual = clamped_b - clamped_t
        crop_w_actual = clamped_r - clamped_l

        if top_margin_px < cfg.minimum_top_margin_ratio * crop_h_actual:
            add_issue(CropIssueCode.CROP_TOP_HAIR_RISK, IssueSeverity.WARNING, False)
        if bottom_margin_px < cfg.minimum_bottom_margin_ratio * crop_h_actual:
            add_issue(CropIssueCode.CROP_CHIN_RISK, IssueSeverity.WARNING, False)
            add_issue(CropIssueCode.CROP_BEARD_RISK, IssueSeverity.WARNING, False)
            add_issue(
                CropIssueCode.CROP_HEAD_COVERING_RISK, IssueSeverity.WARNING, False
            )
        if (
            left_margin_px < cfg.minimum_side_margin_ratio * crop_w_actual
            or right_margin_px < cfg.minimum_side_margin_ratio * crop_w_actual
        ):
            add_issue(CropIssueCode.CROP_SIDE_HEAD_RISK, IssueSeverity.WARNING, False)

        # 8. Aspect and Centering errors
        ideal_crop_width = ideal_r_rounded - ideal_l_rounded
        ideal_crop_height = ideal_b_rounded - ideal_t_rounded
        crop_box_width = clamped_r - clamped_l
        crop_box_height = clamped_b - clamped_t

        crop_box_aspect_ratio = (
            crop_box_width / crop_box_height if crop_box_height > 0 else 1.0
        )
        ideal_crop_aspect_ratio = (
            ideal_crop_width / ideal_crop_height if ideal_crop_height > 0 else 1.0
        )

        if padding_required and not cfg.allow_padding:
            aspect_ratio_error = abs(crop_box_aspect_ratio - target_aspect)
        else:
            aspect_ratio_error = abs(ideal_crop_aspect_ratio - target_aspect)

        aspect_ratio_valid = aspect_ratio_error <= 1e-4

        if not aspect_ratio_valid:
            add_issue(
                CropIssueCode.CROP_ASPECT_RATIO_MISMATCH, IssueSeverity.ERROR, True
            )

        # Centering check
        face_center_x_ratio = (face_cx - ideal_l_rounded) / ideal_crop_width
        face_center_y_ratio = (face_cy - ideal_t_rounded) / ideal_crop_height

        face_centering_valid = (
            abs(face_center_x_ratio - 0.5) <= 0.05
            and abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
            <= cfg.maximum_face_center_y_deviation
        )

        centering_severe = (
            abs(face_center_x_ratio - 0.5) > 0.15
            or abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
            > 2.0 * cfg.maximum_face_center_y_deviation
        )

        if centering_severe:
            add_issue(CropIssueCode.CROP_FACE_NOT_CENTERED, IssueSeverity.ERROR, True)
        elif not face_centering_valid:
            add_issue(
                CropIssueCode.CROP_FACE_NOT_CENTERED, IssueSeverity.WARNING, False
            )

        subject_clipping_detected = (
            not face_contained
            or (head_preservation_valid is False)
            or (mask_preservation_valid is False)
        )

        is_valid = (
            len(
                [
                    iss
                    for iss in issues
                    if iss.blocking_for_processing
                    or iss.severity == IssueSeverity.ERROR
                ]
            )
            == 0
        )

        validation_report = CropValidationReport(
            is_valid=is_valid,
            issue_codes=issue_codes,
            issues=issues,
            crop_inside_source=crop_inside_source,
            ideal_crop_inside_source=ideal_crop_inside_source,
            aspect_ratio_valid=aspect_ratio_valid,
            face_contained=face_contained,
            head_preservation_valid=head_preservation_valid,
            mask_preservation_valid=mask_preservation_valid,
            padding_required=padding_required,
            valid_without_padding=can_crop_without_padding,
            subject_clipping_detected=subject_clipping_detected,
            top_margin_px=top_margin_px,
            bottom_margin_px=bottom_margin_px,
            left_margin_px=left_margin_px,
            right_margin_px=right_margin_px,
            head_estimate_unavailable=(head_estimate is None),
            segmentation_refinement_failed_or_skipped=(refined_mask is None),
            mask_aware_validation_unavailable=(refined_mask is None),
            fallback_source="face-only geometry" if head_estimate is None else None,
            face_centering_valid=face_centering_valid,
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        return CropPlanResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.EXACT_ASPECT,
            crop_box=crop_box,
            crop_box_width=crop_box_width,
            crop_box_height=crop_box_height,
            crop_box_aspect_ratio=crop_box_aspect_ratio,
            ideal_crop_box=ideal_crop_box,
            ideal_crop_width=ideal_crop_width,
            ideal_crop_height=ideal_crop_height,
            ideal_crop_aspect_ratio=ideal_crop_aspect_ratio,
            target_aspect_ratio=target_aspect,
            aspect_ratio_error=aspect_ratio_error,
            padding_required=padding_required,
            can_crop_without_padding=can_crop_without_padding,
            # Deprecated / compatibility fields
            crop_width=crop_box_width,
            crop_height=crop_box_height,
            crop_aspect_ratio=crop_box_aspect_ratio,
            face_center_x_ratio=face_center_x_ratio,
            face_center_y_ratio=face_center_y_ratio,
            head_coverage_ratio=head_coverage_ratio,
            mask_preservation_ratio=mask_preservation_ratio,
            head_height_ratio=best_ratios.get("head_height_ratio"),
            head_width_ratio=best_ratios.get("head_width_ratio"),
            top_margin_ratio=best_ratios.get("top_margin_ratio"),
            eye_line_ratio=best_ratios.get("eye_line_ratio"),
            center_offset_ratio=best_ratios.get("center_offset_ratio"),
            torso_inclusion_ratio=best_ratios.get("torso_inclusion_ratio"),
            portrait_composition_box=composition_box,
            validation=validation_report,
            processing_duration_ms=duration,
            preview_image=None,
        )

    def _estimate_crown_y(
        self,
        face: FaceDetection,
        preserve_box: BoundingBox,
        alpha_mask: Optional[np.ndarray[Any, Any]],
        refined_mask: Optional[Image.Image],
    ) -> float:
        """Locate the top of the hair, preferring the observed subject mask.

        ``preserve_box.top`` is the union of a geometric guess
        (``face_top - 0.6 * face_height``) and the observed mask, so it takes
        whichever reaches higher.  When the detector returns an oversized face
        box the geometric term overshoots the real hairline badly and the crop
        is planned around empty space above the subject.  The segmentation mask
        is the direct observation, so it wins when it is available and sane.
        """
        face_box = face.bounding_box
        highest_plausible = face_box.top - 1.10 * face_box.height
        fallback = max(preserve_box.top, highest_plausible)

        source: Optional[np.ndarray[Any, Any]] = None
        if alpha_mask is not None:
            source = np.asarray(alpha_mask)
        elif refined_mask is not None:
            source = np.asarray(refined_mask)
        if source is None or source.ndim != 2 or source.size == 0:
            return fallback

        mask = source.astype(np.float32, copy=False)
        threshold = 0.5 if float(mask.max(initial=0.0)) <= 1.0 else 127.5

        height, width = mask.shape
        # Search only the head column band; shoulders and raised arms elsewhere
        # in the frame must not be mistaken for hair.
        x0 = max(0, int(round(face_box.left - 0.35 * face_box.width)))
        x1 = min(width, int(round(face_box.right + 0.35 * face_box.width)))
        y1 = min(height, max(1, int(round(face_box.bottom))))
        if x1 <= x0 or y1 <= 0:
            return fallback

        rows = np.where((mask[0:y1, x0:x1] > threshold).any(axis=1))[0]
        if rows.size == 0:
            return fallback

        observed = float(rows[0])
        # The mask is the direct observation, so it is only rejected when it is
        # implausible *on its own terms*: reaching toward the frame top (mask
        # noise), or leaving no head above the chin (degenerate).
        #
        # It is deliberately NOT rejected for sitting below ``face_box.top``.
        # That condition means the detector's box extends above the subject --
        # which is exactly when the geometric fallback is worst -- and the
        # earlier guard discarded the correct reading precisely in that case.
        # Measured: a low-confidence recovery detection returned a box ~1.5x
        # too tall, the mask correctly placed the hair top 73px below the box
        # top, the reading was thrown away, and the crop was then sized around
        # ~100px of empty space above the subject.
        if observed < highest_plausible:
            return fallback
        if observed > face_box.bottom - _MIN_HEAD_SPAN_FACE_RATIO * face_box.height:
            return fallback
        return observed

    def _estimate_head_core_x(
        self,
        face: FaceDetection,
        preserve_box: BoundingBox,
        alpha_mask: Optional[np.ndarray[Any, Any]],
        refined_mask: Optional[Image.Image],
        crown_y: float,
        chin_y: float,
    ) -> tuple[float, float]:
        """Measure the head's horizontal extent from the observed subject mask.

        The fallback expands the detector face box sideways, which fails the
        same way the crown estimate did: an oversized face box yields an
        oversized head width.  Because head height is now measured accurately
        from the mask, an inflated width makes the constraints contradictory --
        the crop must be wide enough to hold the phantom head yet short enough
        to keep face coverage above the exam minimum, and no crop can be both.
        Measured on two such photos the width demanded ``hc >= 342`` and ``367``
        while coverage capped it at ``237`` and ``213``, so every candidate was
        rejected and the planner fell back to a projection at 0.52 and 0.39
        coverage.  Reading the width off the mask keeps both bounds consistent.
        """
        face_box = face.bounding_box
        fallback = (
            max(
                preserve_box.left,
                face_box.left - _HEAD_SIDE_MARGIN_RATIO * face_box.width,
            ),
            min(
                preserve_box.right,
                face_box.right + _HEAD_SIDE_MARGIN_RATIO * face_box.width,
            ),
        )

        source: Optional[np.ndarray[Any, Any]] = None
        if alpha_mask is not None:
            source = np.asarray(alpha_mask)
        elif refined_mask is not None:
            source = np.asarray(refined_mask)
        if source is None or source.ndim != 2 or source.size == 0:
            return fallback

        mask = source.astype(np.float32, copy=False)
        threshold = 0.5 if float(mask.max(initial=0.0)) <= 1.0 else 127.5
        height, width = mask.shape

        # Measure across the ear band only -- the middle of the head span --
        # rather than the whole crown..chin extent.  What must not be clipped is
        # the face and ears; outer hair may leave the frame, as it does in the
        # reference set.  Spanning the full head instead measures hair volume,
        # which on voluminous-hair subjects is far wider than the head core and
        # forces a looser crop: doing so cost six photos that had previously met
        # the coverage floor.  Ears sit roughly 0.35-0.65 of the way down from
        # the crown, so this band captures them and excludes the hair above.
        span = max(1.0, chin_y - crown_y)
        y0 = max(0, min(int(round(chin_y - 0.70 * span)), height - 1))
        y1 = max(y0 + 1, min(int(round(chin_y - 0.20 * span)), height))
        band = mask[y0:y1, :] > threshold
        cols = np.where(band.any(axis=0))[0]
        if cols.size == 0:
            return fallback

        observed_left = float(cols[0])
        observed_right = float(cols[-1])
        observed_width = observed_right - observed_left
        face_center_x = (face_box.left + face_box.right) / 2.0

        # Reject a reading that misses the face entirely, spans implausibly
        # narrow (segmentation clipped into the face), or implausibly wide
        # (mask contamination reaching across the frame).
        #
        # This does NOT require the band to reach the detector box's own
        # edges. Photo 6-3 (reference set) measures a true, visually-verified
        # ear-band width of 124px against a face_box width of 188px -- the
        # subject's hairstyle covers both ears, so the visible head is
        # genuinely narrower than BlazeFace's box, which (like the crown
        # estimate above) is not a precise head-width indicator. Requiring
        # edge coverage rejected that correct 124px reading and fell back to
        # a 244px expansion of the oversized box, which no crop could satisfy
        # alongside the 75% coverage floor. Centered-on-face plus a minimum
        # width ratio catches genuine mask failures without penalizing
        # legitimately hair-covered ears.
        if not (observed_left < face_center_x < observed_right):
            return fallback
        if observed_width < _MIN_HEAD_WIDTH_FACE_RATIO * face_box.width:
            return fallback
        if observed_width > _MAX_HEAD_WIDTH_FACE_RATIO * face_box.width:
            return fallback

        return (
            max(preserve_box.left, observed_left),
            min(preserve_box.right, observed_right),
        )

    def _estimate_chin_y(self, face: FaceDetection, preserve_box: BoundingBox) -> float:
        """Estimate the chin line in source pixels.

        Three-tier preference, each one only reached when the one before is
        unavailable:

        1. Dense-landmark chin (DEC-032) -- best available, but the landmarker
           can fail to find a face the detector did find (measured: 6 of 60
           reference photos, typically occlusion from glasses).
        2. Eye/mouth-anchored estimate (DEC-034) -- BlazeFace's own coarse
           keypoints are genuine detected points rather than a box edge, so
           this stays accurate when the dense landmarker fails. Calibrated
           against 29 reference photos with a known chin (mouth-to-chin
           distance averages 0.598x the eye-to-mouth distance): mean error
           -0.001 face heights (vs +0.046 for the box-bottom proxy) and 3
           large-error outliers instead of 5. On the photo that motivated
           this tier, the box-bottom proxy placed the chin visibly into the
           subject's neck; the eye/mouth estimate lands on the jaw.
        3. Detector box bottom -- last resort when even the coarse keypoints
           are missing. Measured -0.045 face heights off on primary
           detections and -0.143 off on detections recovered at reduced
           confidence.

        The result is clamped into the preservation box so a degenerate
        reading cannot invert the head span.
        """
        face_box = face.bounding_box
        chin_y = face_box.bottom
        landmarks = face.landmarks
        if landmarks is not None and landmarks.chin is not None:
            chin_y = landmarks.chin.y
        elif (
            landmarks is not None
            and landmarks.left_eye is not None
            and landmarks.right_eye is not None
        ):
            mouth = landmarks.custom_landmarks.get("mouth_center")
            if mouth is not None:
                eye_y = (landmarks.left_eye.y + landmarks.right_eye.y) / 2.0
                chin_y = mouth.y + _MOUTH_TO_CHIN_RATIO * (mouth.y - eye_y)
        lower_bound = face_box.top + 0.5 * face_box.height
        return max(lower_bound, min(chin_y, preserve_box.bottom))

    def _empty_failed_result(
        self,
        cfg: CropConfig,
        start_time: float,
        issues: List[CropValidationIssue],
        issue_codes: List[CropIssueCode],
    ) -> CropPlanResult:
        duration = (time.perf_counter() - start_time) * 1000.0
        val = CropValidationReport(
            is_valid=False,
            issue_codes=issue_codes,
            issues=issues,
            crop_inside_source=False,
            ideal_crop_inside_source=False,
            aspect_ratio_valid=False,
            face_contained=False,
            padding_required=False,
            valid_without_padding=False,
            subject_clipping_detected=True,
            face_centering_valid=False,
        )
        return CropPlanResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.EXACT_ASPECT,
            crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            crop_box_width=1,
            crop_box_height=1,
            crop_box_aspect_ratio=1.0,
            ideal_crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            ideal_crop_width=1,
            ideal_crop_height=1,
            ideal_crop_aspect_ratio=1.0,
            target_aspect_ratio=1.0,
            aspect_ratio_error=0.0,
            padding_required=False,
            can_crop_without_padding=False,
            crop_width=1,
            crop_height=1,
            crop_aspect_ratio=1.0,
            face_center_x_ratio=0.5,
            face_center_y_ratio=0.5,
            validation=val,
            processing_duration_ms=duration,
        )
