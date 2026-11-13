"""Strand-level alpha recovery (DEC-138): it may only move the matte toward the
photograph, and must leave it alone wherever the photograph cannot be trusted."""

from __future__ import annotations

import numpy as np

from exam_photo.providers.strand_matting import recover_strand_alpha


def _box_blur(a: np.ndarray, r: int) -> np.ndarray:
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = np.cumsum(np.cumsum(p, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def _scene(
    bg: tuple[float, float, float], hair: tuple[float, float, float], noise: float = 0.0
):
    """A head of hair below y=60 with thin strands rising above it, on a wall."""
    h, w = 120, 160
    truth = np.zeros((h, w), np.float32)
    truth[60:, :] = 1.0
    for x in range(10, w - 10, 9):  # one-pixel strands, 14 px tall
        truth[46:60, x] = 1.0
    rng = np.random.default_rng(7)
    img = np.empty((h, w, 3), np.float32)
    for c in range(3):
        img[..., c] = bg[c] * (1 - truth) + hair[c] * truth
    if noise:
        img += rng.normal(0, noise, img.shape).astype(np.float32)
    img = np.clip(img, 0, 1)
    # the model's view: a smooth hull that does not see the strands
    hull = np.zeros((h, w), np.float32)
    hull[57:, :] = 1.0
    prior = np.clip(_box_blur(hull, 5), 0, 1).astype(np.float32)
    return img, truth, prior


def test_plain_wall_moves_alpha_toward_the_strands() -> None:
    img, truth, prior = _scene((0.92, 0.82, 0.55), (0.12, 0.09, 0.07))
    res = recover_strand_alpha(img, prior, radius=10)
    assert res.applied
    band = (prior > 0.02) & (prior < 0.98)
    before = np.abs(prior - truth)[band].mean()
    after = np.abs(res.alpha - truth)[band].mean()
    assert after < before * 0.6


def test_hair_the_same_colour_as_the_wall_is_left_alone() -> None:
    img, _truth, prior = _scene((0.70, 0.55, 0.45), (0.66, 0.52, 0.43))
    res = recover_strand_alpha(img, prior, radius=10)
    assert np.allclose(res.alpha, prior, atol=1e-6)


def test_a_busy_background_is_left_alone() -> None:
    img, _truth, prior = _scene((0.6, 0.5, 0.4), (0.1, 0.08, 0.06), noise=0.2)
    res = recover_strand_alpha(img, prior, radius=10)
    assert np.abs(res.alpha - prior).mean() < 0.002


def test_a_highlight_on_shiny_hair_is_not_read_as_wall() -> None:
    # Photo 8 of the labelled set: blue-grey highlights on dark hair, as light
    # as the beige wall but off the wall-to-hair colour line.
    img, _truth, prior = _scene((0.85, 0.80, 0.70), (0.10, 0.11, 0.13))
    hl = np.zeros(prior.shape, bool)
    hl[58:66:2, 20:140:3] = True  # inside the soft band and just below it
    img[hl] = (0.62, 0.74, 0.86)
    res = recover_strand_alpha(img, prior, radius=10)
    assert np.all(res.alpha[hl] >= prior[hl] - 0.05)


def test_lone_specks_of_wall_grain_do_not_become_hair() -> None:
    # Photos 33 and 38: single dark pixels of grain or JPEG ringing beside the
    # hairline were added as "strands" and read as salt on the edge.
    img, _truth, prior = _scene((0.92, 0.88, 0.84), (0.25, 0.24, 0.24))
    hull = np.zeros(prior.shape, bool)
    hull[46:60, :] = True  # no real strands this time: only specks
    img[hull] = (0.92, 0.88, 0.84)
    specks = np.zeros(prior.shape, bool)
    specks[48:58:4, 13:150:11] = True
    img[specks] = (0.25, 0.24, 0.24)
    res = recover_strand_alpha(img, prior, radius=10)
    assert np.all(res.alpha[specks] - prior[specks] < 0.35)


def test_an_enlarged_source_keeps_the_model_matte() -> None:
    # Photos 33-38: a small face enlarged 1.4-2.5x turns per-pixel edges into
    # visible steps, so the correction stands down entirely.
    img, _truth, prior = _scene((0.92, 0.82, 0.55), (0.12, 0.09, 0.07))
    res = recover_strand_alpha(img, prior, radius=10, magnification=1.6)
    assert not res.applied
    assert np.array_equal(res.alpha, prior)


def test_pixels_far_from_the_band_are_untouched() -> None:
    img, _truth, prior = _scene((0.92, 0.82, 0.55), (0.12, 0.09, 0.07))
    res = recover_strand_alpha(img, prior, radius=10)
    far_bg = np.zeros_like(prior, bool)
    far_bg[:30, :] = True
    far_fg = np.zeros_like(prior, bool)
    far_fg[90:, :] = True
    assert np.array_equal(res.alpha[far_bg], prior[far_bg])
    assert np.array_equal(res.alpha[far_fg], prior[far_fg])


def test_no_soft_band_is_a_no_op() -> None:
    img, truth, _prior = _scene((0.92, 0.82, 0.55), (0.12, 0.09, 0.07))
    hard = (truth > 0.5).astype(np.float32)
    hard[46:60, :] = 0.0
    res = recover_strand_alpha(img, hard, radius=10)
    assert not res.applied
    assert np.array_equal(res.alpha, hard)
