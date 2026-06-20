# Multi-Model Boundary Refinement for Person Segmentation

This repository contains the final course-project release for **Multi-Model Boundary Refinement for Person Segmentation**.

The project studies a practical person-segmentation pipeline that combines:

- YOLOv8n for person localization
- Segment Anything Model (SAM ViT-B) for prompt-based segmentation
- Canny edge detection for boundary scoring
- morphological edge refinement for candidate-mask selection
- GrabCut for foreground refinement
- YOLOv8n-Seg as a direct segmentation comparison

The goal is not to train a new neural network. Instead, the project compares multiple existing modules and studies whether a multi-model pipeline can improve the boundary quality of person segmentation.

## Main Result

The formal batch test used 12 selected person images from 34 uploaded photos.

| Version | Method | Mean Edge Alignment |
|---|---|---:|
| v1 | SAM auto + Canny score + GrabCut | 0.8708 |
| v6 | YOLO detection + SAM + Canny + Edge refine + GrabCut | 0.8855 |
| v7 | YOLO-Seg direct mask + Canny + Edge refine | 0.5768 |
| v8 | YOLO-Seg direct mask + Canny + GrabCut | 0.7918 |

The best tested version was **v6**, which achieved a mean edge alignment score of **0.8855**. The improvement over the v1 baseline was modest: **+0.0147 absolute**, or about **1.7% relative**.

This result should be interpreted as a preliminary boundary-alignment improvement, not a full segmentation-accuracy claim. The project does not yet include manually annotated ground-truth masks, so IoU and Dice score are not reported.

## Repository Structure

```text
repository root/
  README.md
  requirements.txt
  .gitignore
  docs/
    PROJECT_WORKFLOW.md
    EVALUATION_NOTES.md
    REPRODUCIBILITY.md
  src/
    sam_boundary_refinement.py
    run_experiment_versions.py
    run_batch_test_images.py
    prepare_test_images.py
  model_weights/
    README.md
    DOWNLOAD_MODEL_WEIGHTS.md
  test_images/
    final_selected/
  results/
    summary_tables/
    visual_assets/
  paper/
    Final_Project_Paper.pdf
    IEEE_Final_Project_Paper.tex
    figures/
    paper_used_images/
  presentation/
    人工智慧應用presentation.pdf
  references/
```

For the complete project story, method explanation, conclusion, and future work, see:

```text
docs/PROJECT_WORKFLOW.md
```

For the edge-alignment metric, the reason v7 is weak, and the current single-person limitation, see:

```text
docs/EVALUATION_NOTES.md
```

For exact reproduction steps and expected generated files, see:

```text
docs/REPRODUCIBILITY.md
```

## Model Weights

Large model files are intentionally not included in this GitHub release.

Place the following files in `model_weights/` before running the full experiments:

```text
sam_vit_b_01ec64.pth
yolov8n.pt
yolov8n-seg.pt
```

The SAM checkpoint is larger than GitHub's normal file limit, so it should not be committed directly.

Download instructions and official references are provided in:

```text
model_weights/DOWNLOAD_MODEL_WEIGHTS.md
```

## Setup

Create a Python 3.10 or 3.11 environment and install dependencies:

```powershell
pip install -r requirements.txt
```

Expected major libraries:

- Python
- OpenCV
- NumPy
- PyTorch
- Segment Anything, installed from the official GitHub repository
- Ultralytics YOLO
- pillow-heif, only needed when converting HEIC/HEIF photos with `prepare_test_images.py`

Quick code sanity check:

```powershell
python -m compileall src
python src/run_experiment_versions.py --help
python src/run_batch_test_images.py --help
```

## Example Usage

Run one image with the proposed YOLO-guided SAM pipeline:

```powershell
python src/sam_boundary_refinement.py `
  --image_path test_images/final_selected/final_01_11_IMG_1359.jpg `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --edge_refine `
  --output_dir outputs/example_v6
```

Run the version-comparison script on one selected image:

```powershell
python src/run_experiment_versions.py `
  --image_path test_images/final_selected/final_01_11_IMG_1359.jpg `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --yolo_seg_model model_weights/yolov8n-seg.pt `
  --output_root outputs/experiment_versions_example
```

Run the selected-image batch script on the 12 included test images:

```powershell
python src/run_batch_test_images.py `
  --image_dir test_images/final_selected `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --yolo_seg_model model_weights/yolov8n-seg.pt `
  --output_root outputs/batch_test
```

The commands assume they are run from the repository root after the required model weights have been placed in `model_weights/`.

Generated experiment outputs are intentionally ignored by Git and should appear under `outputs/` or the chosen `--output_root` path.

## Paper and Presentation

The project paper source is located at:

```text
paper/IEEE_Final_Project_Paper.tex
```

A directly viewable final paper PDF is located at:

```text
paper/Final_Project_Paper.pdf
```

The final submitted PDF is treated as the canonical final paper artifact. The editable IEEE source is kept in `paper/IEEE_Final_Project_Paper.tex`; to regenerate the PDF, compile that file with the files in `paper/figures/`, for example by using Overleaf or a local LaTeX installation.

The presentation PDF is located at:

```text
presentation/人工智慧應用presentation.pdf
```

## Limitations

- The test set is small: 12 selected formal test images.
- Edge alignment is a proxy metric, not a replacement for IoU or Dice score.
- No manually annotated ground-truth masks are included.
- The result should not be claimed as a universal improvement over SAM, YOLO-Seg, or supervised segmentation models.
- The current implementation is single-target person segmentation. Multi-person images are reduced to the best detected person box.

## References

Core references are listed in:

```text
references/supporting_papers_summary.md
references/references.bib
```

## Future Work

- Add manually labeled ground-truth masks.
- Report IoU and Dice score.
- Expand testing to more poses, backgrounds, occlusion cases, and lighting conditions.
- Compare stronger segmentation baselines if project scope allows.
