"""OCR benchmark runner stub that will execute against manifest-listed PNG samples."""
from __future__ import annotations

import json
from pathlib import Path

from app.ocr import ocr_drink

MANIFEST = Path("data/benchmarks/manifest.json")


def run_benchmark() -> None:
    samples = json.loads(MANIFEST.read_text())
    results = []
    for sample in samples:
        image_path = Path(sample["path"])
        ground_truth = sample["truth"]
        text = ocr_drink(image_path)
        results.append({
            "file": str(image_path),
            "matched": text == ground_truth,
        })
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_benchmark()
