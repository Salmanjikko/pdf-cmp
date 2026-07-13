import numpy as np
import pytest
from pdf_cmp import (
    binarize,
    dilate_ink,
    find_symmetric_difference,
    filter_small_blobs,
    get_diff_mask_from_arrays,
    INK_THRESHOLD,
    MIN_BLOB_SIZE,
)


def test_binarize_dark_pixel_is_ink():
    gray = np.array([[199]], dtype=np.uint8)
    assert binarize(gray)[0, 0] == True


def test_binarize_light_pixel_is_paper():
    gray = np.array([[201]], dtype=np.uint8)
    assert binarize(gray)[0, 0] == False


def test_binarize_exact_threshold_is_paper():
    gray = np.array([[INK_THRESHOLD]], dtype=np.uint8)
    assert binarize(gray)[0, 0] == False


def test_binarize_black_pixel_is_ink():
    gray = np.array([[0]], dtype=np.uint8)
    assert binarize(gray)[0, 0] == True


def test_binarize_white_pixel_is_paper():
    gray = np.array([[255]], dtype=np.uint8)
    assert binarize(gray)[0, 0] == False




def test_dilate_single_pixel_becomes_3x3():
    ink = np.zeros((5, 5), dtype=bool)
    ink[2, 2] = True
    result = dilate_ink(ink)
    assert result.sum() == 9


def test_dilate_preserves_original_ink():
    ink = np.zeros((10, 10), dtype=bool)
    ink[3:7, 3:7] = True
    result = dilate_ink(ink)
    assert result[5, 5] == True


def test_dilate_expands_by_one_pixel():
    ink = np.zeros((10, 10), dtype=bool)
    ink[4:6, 4:6] = True
    result = dilate_ink(ink)
    assert result[3, 3] == True
    assert result[6, 6] == True


def test_dilate_empty_image_stays_empty():
    ink = np.zeros((10, 10), dtype=bool)
    result = dilate_ink(ink)
    assert result.sum() == 0



def test_symmetric_difference_identical_masks():
    ink = np.zeros((10, 10), dtype=bool)
    ink[3:7, 3:7] = True
    result = find_symmetric_difference(ink, ink)
    assert not result.any()


def test_symmetric_difference_detects_insertion():
    ink1 = np.zeros((20, 20), dtype=bool)
    ink2 = np.zeros((20, 20), dtype=bool)
    ink2[5:15, 5:15] = True
    result = find_symmetric_difference(ink1, ink2)
    assert result.any()


def test_symmetric_difference_detects_removal():
    ink1 = np.zeros((20, 20), dtype=bool)
    ink1[5:15, 5:15] = True
    ink2 = np.zeros((20, 20), dtype=bool)
    result = find_symmetric_difference(ink1, ink2)
    assert result.any()


def test_symmetric_difference_ignores_one_pixel_shift():
    ink1 = np.zeros((30, 30), dtype=bool)
    ink1[10:20, 10:20] = True
    ink2 = np.zeros((30, 30), dtype=bool)
    ink2[10:20, 11:21] = True
    result = find_symmetric_difference(ink1, ink2)
    assert result.sum() < 50


def test_symmetric_difference_detects_large_move():
    ink1 = np.zeros((40, 40), dtype=bool)
    ink1[5:15, 5:15] = True
    ink2 = np.zeros((40, 40), dtype=bool)
    ink2[25:35, 25:35] = True
    result = find_symmetric_difference(ink1, ink2)
    assert result.sum() > 100



def test_filter_removes_tiny_blob():
    mask = np.zeros((20, 20), dtype=bool)
    mask[5:8, 5:8] = True
    result = filter_small_blobs(mask)
    assert not result.any()


def test_filter_keeps_large_blob():
    mask = np.zeros((20, 20), dtype=bool)
    mask[3:13, 3:13] = True
    result = filter_small_blobs(mask)
    assert result.any()


def test_filter_keeps_diagonal_blob():
    mask = np.zeros((20, 20), dtype=bool)
    for i in range(16):
        mask[i, i] = True
    result = filter_small_blobs(mask)
    assert result.any()


def test_filter_empty_mask_stays_empty():
    mask = np.zeros((20, 20), dtype=bool)
    result = filter_small_blobs(mask)
    assert not result.any()


def test_filter_exactly_at_threshold():
    mask = np.zeros((20, 20), dtype=bool)
    mask[5:8, 5:10] = True
    assert mask.sum() == MIN_BLOB_SIZE
    result = filter_small_blobs(mask)
    assert result.any()


def test_filter_one_below_threshold():
    mask = np.zeros((20, 20), dtype=bool)
    mask[5:8, 5:10] = True
    mask[5, 5] = False
    assert mask.sum() == MIN_BLOB_SIZE - 1
    result = filter_small_blobs(mask)
    assert not result.any()



def test_pipeline_identical_images():
    gray = np.full((50, 50), 255, dtype=np.uint8)
    result = get_diff_mask_from_arrays(gray, gray)
    assert not result.any()


def test_pipeline_detects_inserted_block():
    gray1 = np.full((50, 50), 255, dtype=np.uint8)
    gray2 = np.full((50, 50), 255, dtype=np.uint8)
    gray2[15:30, 15:30] = 0
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert result.any()


def test_pipeline_detects_removed_block():
    gray1 = np.full((50, 50), 255, dtype=np.uint8)
    gray1[15:30, 15:30] = 0
    gray2 = np.full((50, 50), 255, dtype=np.uint8)
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert result.any()


def test_pipeline_ignores_one_pixel_shift():
    gray1 = np.full((60, 60), 255, dtype=np.uint8)
    gray1[20:40, 20:40] = 0
    gray2 = np.full((60, 60), 255, dtype=np.uint8)
    gray2[20:40, 21:41] = 0
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert result.sum() < MIN_BLOB_SIZE


def test_pipeline_filters_tiny_noise():
    gray1 = np.full((50, 50), 255, dtype=np.uint8)
    gray2 = np.full((50, 50), 255, dtype=np.uint8)
    gray2[25:28, 25:28] = 0
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert not result.any()


def test_pipeline_ignores_gray_shades():
    gray1 = np.full((50, 50), 255, dtype=np.uint8)
    gray2 = np.full((50, 50), 220, dtype=np.uint8)
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert not result.any()


def test_pipeline_detects_real_text_change():
    gray1 = np.full((100, 100), 255, dtype=np.uint8)
    gray1[30:70, 20:80] = 0
    gray2 = np.full((100, 100), 255, dtype=np.uint8)
    gray2[30:70, 20:80] = 0
    gray2[75:85, 20:80] = 0
    result = get_diff_mask_from_arrays(gray1, gray2)
    assert result.any()
