import time
from typing import Optional, Tuple

from PIL import Image, ImageEnhance

from ..output_preparation import (
    EnhancementMode,
    OutputPreparationConfig,
    OutputPreparationIssueCode,
    OutputPreparationResult,
    OutputPreparationValidationReport,
    OutputPreparer,
    ResampleMethod,
    ResizeMode,
)


class DeterministicOutputPreparer(OutputPreparer):
    provider_name = "DeterministicOutputPreparer"
    provider_version = "1.0.0"

    def prepare_output(
        self, image: Image.Image, config: OutputPreparationConfig
    ) -> OutputPreparationResult:
        start_time = time.perf_counter()
        issue_codes = []

        if not isinstance(image, Image.Image):
            return self._build_fail_result(
                config, image, [OutputPreparationIssueCode.OUTPUT_INPUT_INVALID]
            )

        if image.width <= 0 or image.height <= 0:
            return self._build_fail_result(
                config, image, [OutputPreparationIssueCode.OUTPUT_INPUT_INVALID]
            )

        # 1. Resolve Target Dimensions
        source_width, source_height = image.size
        source_aspect = source_width / source_height
        target_w, target_h = None, None
        aspect_preserved = True

        if config.resize_mode == ResizeMode.EXACT:
            if not config.target_width or not config.target_height:
                issue_codes.append(
                    OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_MISSING
                )
            elif config.target_width <= 0 or config.target_height <= 0:
                issue_codes.append(
                    OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_INVALID
                )
            else:
                target_w = config.target_width
                target_h = config.target_height

                target_aspect = target_w / target_h
                # Check aspect match with 1% tolerance
                if abs(source_aspect - target_aspect) > 0.01:
                    issue_codes.append(
                        OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH
                    )

        elif config.resize_mode == ResizeMode.RANGE_SELECT:
            if (
                not config.min_width
                or not config.max_width
                or not config.min_height
                or not config.max_height
            ):
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_RANGE_INVALID)
            elif (
                config.min_width > config.max_width
                or config.min_height > config.max_height
            ):
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_RANGE_INVALID)
            elif config.min_width <= 0 or config.min_height <= 0:
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_RANGE_INVALID)
            else:
                target_w, target_h, aspect_preserved = self._resolve_range_dimensions(
                    source_width,
                    source_height,
                    config.min_width,
                    config.max_width,
                    config.min_height,
                    config.max_height,
                    config.preferred_width,
                    config.preferred_height,
                )
                if not target_w or not target_h:
                    issue_codes.append(OutputPreparationIssueCode.OUTPUT_RANGE_INVALID)
                elif not aspect_preserved:
                    issue_codes.append(
                        OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH
                    )

        if (
            not target_w
            or not target_h
            or OutputPreparationIssueCode.OUTPUT_RANGE_INVALID in issue_codes
            or OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_MISSING
            in issue_codes
            or OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_INVALID
            in issue_codes
            or OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH in issue_codes
        ):
            return self._build_fail_result(
                config,
                image,
                issue_codes,
                target_w=target_w or 0,
                target_h=target_h or 0,
            )

        # 2. Check scaling logic
        scale_x = target_w / source_width
        scale_y = target_h / source_height
        scale = max(scale_x, scale_y)

        # Scaling validation
        if not config.allow_upscale and scale > 1.00001:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_UPSCALE_LIMIT_EXCEEDED)
        elif scale > config.max_upscale_factor:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_UPSCALE_LIMIT_EXCEEDED)
        elif scale > 3.0:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_UPSCALE_LIMIT_EXCEEDED)
        elif scale > 2.0:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_UPSCALE_STRONG_WARNING)
        elif scale > 1.5:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_UPSCALE_WARNING)

        downscale = min(scale_x, scale_y)
        if downscale < config.min_downscale_factor:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_DOWNSCALE_TOO_SEVERE)
        elif downscale < 0.05:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_DOWNSCALE_TOO_SEVERE)
        elif downscale <= 0.10:
            issue_codes.append(
                OutputPreparationIssueCode.OUTPUT_DOWNSCALE_SEVERE_WARNING
            )
        elif downscale <= 0.20:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_DOWNSCALE_WARNING)

        # 5. Enhancement Validation
        b_adj = config.brightness_adjustment
        c_adj = config.contrast_adjustment
        s_adj = config.sharpness_adjustment

        if config.enhancement_mode == EnhancementMode.NONE:
            if b_adj != 1.0 or c_adj != 1.0 or s_adj != 1.0:
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE)
        elif config.enhancement_mode == EnhancementMode.CONSERVATIVE:
            if (
                not (0.88 <= b_adj <= 1.12)
                or not (0.88 <= c_adj <= 1.12)
                or not (0.80 <= s_adj <= 1.20)
            ):
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE)
            elif (
                abs(b_adj - 1.0) > config.max_brightness_adjustment_delta
                or abs(c_adj - 1.0) > config.max_contrast_adjustment_delta
                or abs(s_adj - 1.0) > config.max_sharpness_adjustment_delta
            ):
                issue_codes.append(OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE)
        else:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE)

        # 3. Resize
        resample_mapping = {
            ResampleMethod.LANCZOS: Image.Resampling.LANCZOS,
            ResampleMethod.BICUBIC: Image.Resampling.BICUBIC,
            ResampleMethod.BILINEAR: Image.Resampling.BILINEAR,
        }
        resample = resample_mapping.get(
            config.resample_method, Image.Resampling.LANCZOS
        )
        try:
            out_img = image.resize((target_w, target_h), resample=resample)
        except Exception:
            issue_codes.append(OutputPreparationIssueCode.OUTPUT_RESIZE_FAILED)
            return self._build_fail_result(
                config, image, issue_codes, target_w, target_h, scale_x, scale_y
            )

        # 4. Mode and Metadata
        if out_img.mode != config.output_colour_mode:
            try:
                # E.g. RGBA -> RGB
                if config.output_colour_mode == "RGB" and out_img.mode == "RGBA":
                    bg = Image.new("RGB", out_img.size, (255, 255, 255))
                    bg.paste(out_img, mask=out_img.split()[3])
                    out_img = bg
                else:
                    out_img = out_img.convert(config.output_colour_mode)
            except Exception:
                issue_codes.append(
                    OutputPreparationIssueCode.OUTPUT_UNSUPPORTED_COLOUR_MODE
                )

        if config.strip_metadata:
            out_img.info.clear()

        # Apply Enhancement if safe
        if (
            config.enhancement_mode == EnhancementMode.CONSERVATIVE
            and OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE not in issue_codes
        ):
            if b_adj != 1.0:
                out_img = ImageEnhance.Brightness(out_img).enhance(b_adj)
            if c_adj != 1.0:
                out_img = ImageEnhance.Contrast(out_img).enhance(c_adj)
            if s_adj != 1.0:
                out_img = ImageEnhance.Sharpness(out_img).enhance(s_adj)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        blocking_issues = {
            OutputPreparationIssueCode.OUTPUT_INPUT_INVALID,
            OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_MISSING,
            OutputPreparationIssueCode.OUTPUT_TARGET_DIMENSIONS_INVALID,
            OutputPreparationIssueCode.OUTPUT_RANGE_INVALID,
            OutputPreparationIssueCode.OUTPUT_ASPECT_MISMATCH,
            OutputPreparationIssueCode.OUTPUT_UPSCALE_LIMIT_EXCEEDED,
            OutputPreparationIssueCode.OUTPUT_DOWNSCALE_TOO_SEVERE,
            OutputPreparationIssueCode.OUTPUT_UNSUPPORTED_COLOUR_MODE,
            OutputPreparationIssueCode.OUTPUT_ENHANCEMENT_UNSAFE,
            OutputPreparationIssueCode.OUTPUT_IDENTITY_RISK,
            OutputPreparationIssueCode.OUTPUT_RESIZE_FAILED,
            OutputPreparationIssueCode.OUTPUT_PROVIDER_FAILED,
        }

        has_blocking = any(code in blocking_issues for code in issue_codes)

        return OutputPreparationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            resize_mode=config.resize_mode,
            source_width=source_width,
            source_height=source_height,
            output_width=target_w,
            output_height=target_h,
            scale_x=scale_x,
            scale_y=scale_y,
            aspect_ratio_error=abs(source_aspect - (target_w / target_h)),
            output_colour_mode=out_img.mode,
            metadata_stripped=config.strip_metadata,
            enhancement_mode=config.enhancement_mode,
            brightness_adjustment=b_adj,
            contrast_adjustment=c_adj,
            sharpness_adjustment=s_adj,
            validation=OutputPreparationValidationReport(
                is_valid=not has_blocking,
                issue_codes=[code.value for code in issue_codes],
            ),
            processing_duration_ms=duration_ms,
            output_image=out_img if config.generate_preview else None,
        )

    def _resolve_range_dimensions(
        self,
        source_width: int,
        source_height: int,
        min_w: int,
        max_w: int,
        min_h: int,
        max_h: int,
        pref_w: Optional[int],
        pref_h: Optional[int],
    ) -> Tuple[Optional[int], Optional[int], bool]:
        source_aspect = source_width / source_height

        # 1. Use preferred width/height if both are supplied, within range, and aspect matches
        if pref_w is not None and pref_h is not None:
            if min_w <= pref_w <= max_w and min_h <= pref_h <= max_h:
                pref_aspect = pref_w / pref_h
                if abs(pref_aspect - source_aspect) <= 0.01:
                    return pref_w, pref_h, True

        # 2. Choose the largest size inside range preserving aspect
        candidates = []
        # Test max_w
        test_h_for_max_w = round(max_w / source_aspect)
        if min_h <= test_h_for_max_w <= max_h:
            candidates.append((max_w, test_h_for_max_w))
        # Test max_h
        test_w_for_max_h = round(max_h * source_aspect)
        if min_w <= test_w_for_max_h <= max_w:
            candidates.append((test_w_for_max_h, max_h))

        if candidates:
            best_w, best_h = max(candidates, key=lambda x: x[0] * x[1])
            return best_w, best_h, True

        # 3. Otherwise choose closest valid size and report aspect warning/failure
        if pref_w is not None and pref_h is not None:
            clamped_w = max(min_w, min(pref_w, max_w))
            clamped_h = max(min_h, min(pref_h, max_h))
            return clamped_w, clamped_h, False

        clamped_w = max(min_w, min(source_width, max_w))
        clamped_h = max(min_h, min(source_height, max_h))
        return clamped_w, clamped_h, False

    def _build_fail_result(
        self,
        config: OutputPreparationConfig,
        image: Image.Image,
        issue_codes: list[OutputPreparationIssueCode],
        target_w: int = 0,
        target_h: int = 0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> OutputPreparationResult:
        return OutputPreparationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            resize_mode=config.resize_mode,
            source_width=image.width if isinstance(image, Image.Image) else 0,
            source_height=image.height if isinstance(image, Image.Image) else 0,
            output_width=target_w,
            output_height=target_h,
            scale_x=scale_x,
            scale_y=scale_y,
            aspect_ratio_error=0.0,
            output_colour_mode="unknown",
            metadata_stripped=False,
            enhancement_mode=config.enhancement_mode,
            brightness_adjustment=1.0,
            contrast_adjustment=1.0,
            sharpness_adjustment=1.0,
            validation=OutputPreparationValidationReport(
                is_valid=False, issue_codes=[code.value for code in issue_codes]
            ),
            processing_duration_ms=0.0,
            output_image=None,
        )
