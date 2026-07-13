import sys
import os
import fitz
import numpy as np
from PIL import Image
from scipy import ndimage
import io

WHITE_THRESHOLD = 240
DPI_FINAL = 150
CMP_DIR = "cmp"
DIFF_COLOR = (255, 0, 0)
IMAGE_FORMAT = "PNG"
COLORSPACE = "RGB"

INK_THRESHOLD = 200
EDGE_TOLERANCE = 1
MIN_BLOB_SIZE = 15
TEST_DPIS = [72, 100, 150]


def binarize(gray):
    return gray < INK_THRESHOLD


def dilate_ink(ink):
    struct = ndimage.generate_binary_structure(2, 2)
    return ndimage.binary_dilation(ink, structure=struct, iterations=EDGE_TOLERANCE)


def find_symmetric_difference(ink1, ink2):
    ink1_dilated = dilate_ink(ink1)
    ink2_dilated = dilate_ink(ink2)
    added_ink = ink2 & ~ink1_dilated
    removed_ink = ink1 & ~ink2_dilated
    return added_ink | removed_ink


def filter_small_blobs(diff_mask):
    struct = ndimage.generate_binary_structure(2, 2)
    labeled, num_features = ndimage.label(diff_mask, structure=struct)
    if num_features == 0:
        return diff_mask
    sizes = ndimage.sum(diff_mask, labeled, range(1, num_features + 1))
    keep_labels = np.where(sizes >= MIN_BLOB_SIZE)[0] + 1
    return np.isin(labeled, keep_labels)


def get_diff_mask_from_arrays(gray1, gray2):
    ink1 = binarize(gray1)
    ink2 = binarize(gray2)
    diff_mask = find_symmetric_difference(ink1, ink2)
    return filter_small_blobs(diff_mask)


def generate_output_filename(pdf1_path, pdf2_path):
    pdf1_name = os.path.splitext(os.path.basename(pdf1_path))[0]
    pdf2_name = os.path.splitext(os.path.basename(pdf2_path))[0]
    os.makedirs(CMP_DIR, exist_ok=True)
    return os.path.join(CMP_DIR, f"{pdf1_name}_{pdf2_name}_cmp.pdf")


def get_diff_mask(pix1, pix2):
    img1 = Image.frombytes(COLORSPACE, (pix1.width, pix1.height), pix1.samples)
    img2 = Image.frombytes(COLORSPACE, (pix2.width, pix2.height), pix2.samples)

    if img1.size != img2.size:
        print("Warning: page size mismatch! Page is Resized!")
        img1 = img1.resize(img2.size, Image.BILINEAR)

    gray1 = np.array(img1.convert("L"), dtype=np.uint8)
    gray2 = np.array(img2.convert("L"), dtype=np.uint8)

    diff_mask = get_diff_mask_from_arrays(gray1, gray2)

    return diff_mask, img2


def check_page_for_differences(pix1, pix2):
    diff_mask, _ = get_diff_mask(pix1, pix2)
    return diff_mask.any()


def find_divergence_dpi(doc1, doc2):
    num_pages = min(len(doc1), len(doc2))
    print("\n--- DPI Divergence Analysis ---")
    for dpi in TEST_DPIS:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        differs = any(check_page_for_differences(doc1[i].get_pixmap(colorspace=fitz.csRGB, matrix=mat),
                                                 doc2[i].get_pixmap(colorspace=fitz.csRGB, matrix=mat))
                      for i in range(num_pages))
        print(f"DPI {dpi:3d}: {'DIFFERENCES FOUND' if differs else 'Identical'}")
        if differs:
            return dpi
    return None


def create_diff_image(pix1, pix2, page_num):
    diff_mask, img2 = get_diff_mask(pix1, pix2)
    output = img2.copy()
    pixels_out = output.load()
    diff_count = int(diff_mask.sum())
    for x, y in zip(np.where(diff_mask)[1].tolist(), np.where(diff_mask)[0].tolist()):
        pixels_out[x, y] = DIFF_COLOR
    print(f"{'Has differences' if diff_count else 'No differences'} in page {page_num + 1}")
    return output


def process_page(doc1, doc2, page_num, output_doc):
    zoom = DPI_FINAL / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix1 = doc1[page_num].get_pixmap(colorspace=fitz.csRGB, matrix=mat)
    pix2 = doc2[page_num].get_pixmap(colorspace=fitz.csRGB, matrix=mat)
    output_img = create_diff_image(pix1, pix2, page_num)
    png_buffer = io.BytesIO()
    output_img.save(png_buffer, format=IMAGE_FORMAT)
    page = output_doc.new_page(width=doc2[page_num].rect.width, height=doc2[page_num].rect.height)
    page.insert_image(page.rect, stream=png_buffer.getvalue())


def compare_pdfs(doc1, doc2, output_doc):
    num_pages = min(len(doc1), len(doc2))
    if len(doc1) != len(doc2):
        print(f"Page count differs. Comparing first {num_pages} pages only")
    for i in range(num_pages):
        process_page(doc1, doc2, i, output_doc)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pdf1> <pdf2>")
        sys.exit(1)

    pdf1_path, pdf2_path = sys.argv[1], sys.argv[2]
    output_path = generate_output_filename(pdf1_path, pdf2_path)

    doc1, doc2 = fitz.open(pdf1_path), fitz.open(pdf2_path)

    div_dpi = find_divergence_dpi(doc1, doc2)
    print(f"\nResult: PDFs start to differ at DPI {div_dpi}." if div_dpi else "\nResult: Visually identical.")

    output_doc = fitz.open()
    compare_pdfs(doc1, doc2, output_doc)
    output_doc.save(output_path)
    output_doc.close()
    doc1.close()
    doc2.close()


if __name__ == "__main__":
    main()
