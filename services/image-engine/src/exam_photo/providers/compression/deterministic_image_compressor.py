import io
import time
from typing import List, Optional

from PIL import Image

from exam_photo.suitability.issue_codes import IssueSeverity

from ..output_compression import (
    CompressionFormat,
    CompressionSearchMode,
    OutputCompressionConfig,
    OutputCompressionIssueCode,
    OutputCompressionResult,
    OutputCompressionValidationIssue,
    OutputCompressionValidationReport,
    OutputCompressor,
)


class DeterministicJpegCompressor(OutputCompressor):
    provider_name = "DeterministicJpegCompressor"
    provider_version = "1.0.0"

    def compress_output(
        self,
        image: Image.Image,
        config: OutputCompressionConfig,
    ) -> OutputCompressionResult:
        start_time = time.perf_counter()
        issues: List[OutputCompressionValidationIssue] = []
        issue_codes: List[OutputCompressionIssueCode] = []

        def add_issue(
            code: OutputCompressionIssueCode,
            severity: IssueSeverity,
            blocking: bool,
        ) -> None:
            if code not in issue_codes:
                issue_codes.append(code)
                issues.append(
                    OutputCompressionValidationIssue(
                        code=code,
                        severity=severity,
                        blocking_for_processing=blocking,
                        confidence=1.0,
                    )
                )

        # Step 1: Validate input image
        if not isinstance(image, Image.Image):
            add_issue(
                OutputCompressionIssueCode.COMPRESSION_INPUT_INVALID,
                IssueSeverity.ERROR,
                True,
            )
            return self._build_fail_result(
                image, config, issues, issue_codes, start_time
            )

        if image.width <= 0 or image.height <= 0:
            add_issue(
                OutputCompressionIssueCode.COMPRESSION_INPUT_INVALID,
                IssueSeverity.ERROR,
                True,
            )
            return self._build_fail_result(
                image, config, issues, issue_codes, start_time
            )

        # Check format support
        if config.target_format != CompressionFormat.JPEG:
            add_issue(
                OutputCompressionIssueCode.COMPRESSION_FORMAT_UNSUPPORTED,
                IssueSeverity.ERROR,
                True,
            )
            return self._build_fail_result(
                image, config, issues, issue_codes, start_time
            )

        # Convert transparent/RGBA image to RGB using solid white background composition
        img_to_encode = image
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            bg = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                bg.paste(image, mask=image.split()[3])
            else:
                bg.paste(
                    image.convert("RGBA"),
                    mask=image.convert("RGBA").split()[3],
                )
            img_to_encode = bg
        else:
            if image.mode != "RGB":
                img_to_encode = image.convert("RGB")

        # Step 2: Resolve target bytes
        target_bytes = min(
            config.maximum_bytes - config.safety_margin_bytes,
            int(config.maximum_bytes * config.target_ceiling_ratio),
        )

        if target_bytes <= 0:
            add_issue(
                OutputCompressionIssueCode.COMPRESSION_TARGET_TOO_SMALL,
                IssueSeverity.ERROR,
                True,
            )
            return self._build_fail_result(
                image, config, issues, issue_codes, start_time
            )

        # Step 3 & 4: Search quality
        best_q: Optional[int] = None
        best_bytes: Optional[bytes] = None
        iterations = 0

        def encode_jpeg(q: int) -> bytes:
            buf = io.BytesIO()
            if config.target_dpi is not None:
                img_to_encode.save(
                    buf,
                    format="JPEG",
                    quality=q,
                    optimize=config.optimize,
                    progressive=config.progressive,
                    dpi=(config.target_dpi, config.target_dpi),
                )
            else:
                img_to_encode.save(
                    buf,
                    format="JPEG",
                    quality=q,
                    optimize=config.optimize,
                    progressive=config.progressive,
                )
            return buf.getvalue()

        # Binary Search Mode
        if config.search_mode == CompressionSearchMode.BINARY_SEARCH:
            low = config.min_quality
            high = config.max_quality
            while low <= high and iterations < config.max_iterations:
                iterations += 1
                mid = (low + high) // 2
                encoded = encode_jpeg(mid)
                size = len(encoded)
                if size <= target_bytes:
                    best_q = mid
                    best_bytes = encoded
                    low = mid + 1
                else:
                    high = mid - 1

            # If allow_quality_below_minimum is True, try to search below min_quality
            if best_q is None and config.allow_quality_below_minimum:
                low = 1
                high = config.min_quality - 1
                while low <= high and iterations < config.max_iterations:
                    iterations += 1
                    mid = (low + high) // 2
                    encoded = encode_jpeg(mid)
                    size = len(encoded)
                    if size <= target_bytes:
                        best_q = mid
                        best_bytes = encoded
                        low = mid + 1
                    else:
                        high = mid - 1

        # Linear Search Mode (fallback/alternative)
        else:
            q = config.initial_quality
            # Search down
            while q >= config.min_quality and iterations < config.max_iterations:
                iterations += 1
                encoded = encode_jpeg(q)
                if len(encoded) <= target_bytes:
                    best_q = q
                    best_bytes = encoded
                    break
                q -= 2

            # Fallback search below minimum if allowed
            if best_q is None and config.allow_quality_below_minimum:
                q = config.min_quality - 1
                while q >= 1 and iterations < config.max_iterations:
                    iterations += 1
                    encoded = encode_jpeg(q)
                    if len(encoded) <= target_bytes:
                        best_q = q
                        best_bytes = encoded
                        break
                    q -= 2

        # Step 5: Fallback if target not met
        final_bytes: Optional[bytes] = None
        final_q: Optional[int] = None

        if best_bytes is not None:
            final_bytes = best_bytes
            final_q = best_q
        else:
            # We failed to stay under target_bytes within allowed quality limits
            # Encode at min_quality to see if we can at least stay under maximum_bytes
            fallback_q = (
                1
                if (config.allow_quality_below_minimum and config.min_quality > 1)
                else config.min_quality
            )
            fallback_bytes = encode_jpeg(fallback_q)
            fallback_size = len(fallback_bytes)

            final_bytes = fallback_bytes
            final_q = fallback_q

            if fallback_size <= config.maximum_bytes:
                # Exceeds target but stays under maximum
                add_issue(
                    OutputCompressionIssueCode.COMPRESSION_SEARCH_FAILED,
                    IssueSeverity.WARNING,
                    False,
                )
            else:
                # Exceeds both target and maximum
                if config.allow_oversize_output:
                    add_issue(
                        OutputCompressionIssueCode.COMPRESSION_SEARCH_FAILED,
                        IssueSeverity.WARNING,
                        False,
                    )
                    add_issue(
                        OutputCompressionIssueCode.COMPRESSION_MAX_SIZE_EXCEEDED,
                        IssueSeverity.WARNING,
                        False,
                    )
                else:
                    add_issue(
                        OutputCompressionIssueCode.COMPRESSION_SEARCH_FAILED,
                        IssueSeverity.ERROR,
                        True,
                    )
                    add_issue(
                        OutputCompressionIssueCode.COMPRESSION_MAX_SIZE_EXCEEDED,
                        IssueSeverity.ERROR,
                        True,
                    )

        # Minimum bytes check
        actual_size = len(final_bytes)
        minimum_size_satisfied = None
        if config.minimum_bytes is not None:
            if actual_size < config.minimum_bytes:
                minimum_size_satisfied = False
                add_issue(
                    OutputCompressionIssueCode.COMPRESSION_MIN_SIZE_NOT_REACHED,
                    IssueSeverity.WARNING,
                    False,
                )
            else:
                minimum_size_satisfied = True

        # Quality floor check
        if final_q is not None:
            if final_q <= config.min_quality:
                # Warning if size satisfies constraints, error if it falls below or failed size
                blocking = any(issue.blocking_for_processing for issue in issues) or (
                    final_q < config.min_quality
                )
                add_issue(
                    OutputCompressionIssueCode.COMPRESSION_QUALITY_TOO_LOW,
                    IssueSeverity.ERROR if blocking else IssueSeverity.WARNING,
                    blocking,
                )

        # Step 7: Decode-after-encode validation
        decode_valid = False
        decoded_image = None
        try:
            buf = io.BytesIO(final_bytes)
            decoded_image = Image.open(buf)
            decoded_image.load()
            decode_valid = (
                decoded_image.width == image.width
                and decoded_image.height == image.height
            )
        except Exception:
            decode_valid = False

        if not decode_valid:
            add_issue(
                OutputCompressionIssueCode.COMPRESSION_DECODE_FAILED,
                IssueSeverity.ERROR,
                True,
            )

        # Step 8: Metadata check
        metadata_stripped = True
        actual_dpi: Optional[int] = None
        dpi_satisfied: bool | None = None
        if decode_valid and decoded_image is not None:
            if "exif" in decoded_image.info:
                metadata_stripped = False
                add_issue(
                    OutputCompressionIssueCode.COMPRESSION_METADATA_STRIP_FAILED,
                    IssueSeverity.ERROR,
                    True,
                )
            actual_dpi = self._extract_square_dpi(decoded_image)
            if config.target_dpi is not None:
                dpi_satisfied = actual_dpi == config.target_dpi

        # Determine if final result is valid (no blocking issues)
        is_valid = not any(issue.blocking_for_processing for issue in issues)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        ratio = actual_size / config.maximum_bytes

        report = OutputCompressionValidationReport(
            is_valid=is_valid,
            issue_codes=issue_codes,
            issues=issues,
            format_supported=True,
            maximum_size_satisfied=(actual_size <= config.maximum_bytes),
            minimum_size_satisfied=minimum_size_satisfied,
            quality_within_bounds=(
                final_q is not None and final_q >= config.min_quality
            ),
            decode_after_encode_valid=decode_valid,
            metadata_stripped=metadata_stripped,
            dpi_satisfied=dpi_satisfied,
            target_bytes=target_bytes,
            actual_bytes=actual_size,
            actual_dpi=actual_dpi,
            byte_size_ratio_to_max=ratio,
            final_quality=final_q,
            iterations_used=iterations,
        )

        return OutputCompressionResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            target_format=config.target_format,
            source_width=image.width,
            source_height=image.height,
            maximum_bytes=config.maximum_bytes,
            target_bytes=target_bytes,
            actual_bytes=actual_size,
            final_quality=final_q,
            min_quality=config.min_quality,
            max_quality=config.max_quality,
            iterations_used=iterations,
            search_mode=config.search_mode,
            optimize=config.optimize,
            progressive=config.progressive,
            metadata_stripped=metadata_stripped,
            target_dpi=config.target_dpi,
            actual_dpi=actual_dpi,
            validation=report,
            processing_duration_ms=duration_ms,
            encoded_bytes=final_bytes,
        )

    def _extract_square_dpi(self, image: Image.Image) -> Optional[int]:
        dpi_value = image.info.get("dpi")
        if not isinstance(dpi_value, tuple) or len(dpi_value) < 2:
            return None
        x_dpi, y_dpi = dpi_value[:2]
        try:
            x_int = int(round(float(x_dpi)))
            y_int = int(round(float(y_dpi)))
        except (TypeError, ValueError):
            return None
        if x_int != y_int:
            return None
        return x_int

    def _build_fail_result(
        self,
        image: Image.Image,
        config: OutputCompressionConfig,
        issues: List[OutputCompressionValidationIssue],
        issue_codes: List[OutputCompressionIssueCode],
        start_time: float,
    ) -> OutputCompressionResult:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        w = image.width if hasattr(image, "width") else 0
        h = image.height if hasattr(image, "height") else 0
        target_bytes = min(
            config.maximum_bytes - config.safety_margin_bytes,
            int(config.maximum_bytes * config.target_ceiling_ratio),
        )

        report = OutputCompressionValidationReport(
            is_valid=False,
            issue_codes=issue_codes,
            issues=issues,
            format_supported=(config.target_format == CompressionFormat.JPEG),
            maximum_size_satisfied=False,
            minimum_size_satisfied=None,
            quality_within_bounds=False,
            decode_after_encode_valid=False,
            metadata_stripped=False,
            dpi_satisfied=False if config.target_dpi is not None else None,
            target_bytes=target_bytes,
            actual_bytes=None,
            actual_dpi=None,
            byte_size_ratio_to_max=None,
            final_quality=None,
            iterations_used=0,
        )

        return OutputCompressionResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            target_format=config.target_format,
            source_width=w,
            source_height=h,
            maximum_bytes=config.maximum_bytes,
            target_bytes=target_bytes,
            actual_bytes=0,
            final_quality=None,
            min_quality=config.min_quality,
            max_quality=config.max_quality,
            iterations_used=0,
            search_mode=config.search_mode,
            optimize=config.optimize,
            progressive=config.progressive,
            metadata_stripped=False,
            target_dpi=config.target_dpi,
            actual_dpi=None,
            validation=report,
            processing_duration_ms=duration_ms,
            encoded_bytes=None,
        )
