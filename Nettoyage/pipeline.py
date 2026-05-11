from steps.step_01_encoding import fix_encoding
from steps.step_02_unicode import fix_unicode
from steps.step_03_ocr_repair import fix_ocr
from steps.step_04_typography import fix_typography
from steps.step_05_structure import fix_structure
from steps.step_06_casing import fix_casing
from steps.step_06_2_sections import fix_segmentation
from steps.step_07_final import fix_final


PIPELINE = [
    fix_encoding,
    fix_unicode,
    fix_ocr,
    fix_typography,
    fix_structure,
    fix_casing,
    fix_segmentation,
    fix_final,
]


def run_pipeline(text: str) -> str:
    for step in PIPELINE:
        result = step(text)
        text = result["text"]

    return text