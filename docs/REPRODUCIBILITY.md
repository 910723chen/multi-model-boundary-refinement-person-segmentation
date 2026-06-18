# Reproducibility Checklist

This document describes what another student, teaching assistant, or professor should be able to reproduce from this repository.

## Environment

Recommended environment:

```text
Python 3.10 or 3.11
Windows PowerShell, macOS Terminal, or Linux shell
CPU is supported; GPU is optional
```

Install dependencies from the repository root:

```powershell
pip install -r requirements.txt
```

If `python` is not available on PATH in Windows, use the Python launcher instead:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m compileall src
```

The project depends on the official Segment Anything repository through:

```text
git+https://github.com/facebookresearch/segment-anything.git
```

## Required Model Files

Model weights are intentionally excluded from Git because they are large binary files. Before running the full experiments, place these files under `model_weights/`:

```text
model_weights/sam_vit_b_01ec64.pth
model_weights/yolov8n.pt
model_weights/yolov8n-seg.pt
```

Download instructions are provided in:

```text
model_weights/DOWNLOAD_MODEL_WEIGHTS.md
```

## Sanity Checks Without Running Full Models

These commands check whether the Python files parse and whether the command-line interfaces are available:

```powershell
python -m compileall src
python src/run_experiment_versions.py --help
python src/run_batch_test_images.py --help
```

Expected result:

```text
No syntax errors.
Both scripts print argument help text.
```

Validation performed during repository review:

```text
python -m compileall src: passed
python src/run_experiment_versions.py --help: passed
python src/run_batch_test_images.py --help: passed
```

## Reproduce One-Image Version Comparison

After placing model weights in `model_weights/`, run:

```powershell
python src/run_experiment_versions.py `
  --image_path test_images/final_selected/final_01_11_IMG_1359.jpg `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --yolo_seg_model model_weights/yolov8n-seg.pt `
  --output_root outputs/experiment_versions_example
```

Expected output files:

```text
outputs/experiment_versions_example/summary.csv
outputs/experiment_versions_example/summary.md
outputs/experiment_versions_example/<version>/metrics.txt
outputs/experiment_versions_example/<version>/overlay_comparison.png
```

Manual prompt versions `v3` and `v4` are expected to be skipped unless `--box` or point prompts are provided.

## Reproduce Batch Test

Run all selected test images:

```powershell
python src/run_batch_test_images.py `
  --image_dir test_images/final_selected `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --yolo_seg_model model_weights/yolov8n-seg.pt `
  --output_root outputs/batch_test
```

Expected output files:

```text
outputs/batch_test/batch_summary.csv
outputs/batch_test/batch_summary.md
outputs/batch_test/<image_name>/<version>/metrics.txt
outputs/batch_test/<image_name>/<version>/overlay_comparison.png
```

The already reported final summary tables are kept under:

```text
results/summary_tables/
```

## What Is Not Fully Reproducible Yet

The project does not include manually annotated ground-truth masks. Therefore, IoU and Dice score cannot be reproduced from this release. The current quantitative result is based on edge alignment, which is a boundary-quality proxy metric.

For a stronger future release, add a `ground_truth_masks/` directory and run the scripts with `--gt_mask_path` for selected images.
