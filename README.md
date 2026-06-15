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
github_release/
  README.md
  release_manifest.csv
  requirements.txt
  .gitignore
  src/
    sam_boundary_refinement.py
    run_experiment_versions.py
    run_batch_test_images.py
    prepare_test_images.py
    build_progress_report_assets.py
  model_weights/
    README.md
  test_images/
    final_selected/
  results/
    summary_tables/
    visual_assets/
  paper/
    IEEE_Final_Project_Paper.tex
    figures/
    paper_used_images/
  presentation/
    Final_Project_Presentation_FIXED_IMAGES.pptx
    Final_Project_Presentation_ROUGH_FIXED_IMAGES.pptx
    previews/
  references/
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

## Setup

Create a Python environment and install dependencies:

```powershell
pip install -r requirements.txt
```

Expected major libraries:

- Python
- OpenCV
- NumPy
- PyTorch
- Segment Anything
- Ultralytics YOLO

## Example Usage

Run one image with the proposed YOLO-guided SAM pipeline:

```powershell
python src/sam_boundary_refinement.py `
  --image_path test_images/final_selected/final_01_11_IMG_1359.jpg `
  --checkpoint model_weights/sam_vit_b_01ec64.pth `
  --yolo_model model_weights/yolov8n.pt `
  --use_yolo_box `
  --edge_refine `
  --output_dir outputs/example_v6
```

Run the version-comparison batch script:

```powershell
python src/run_experiment_versions.py
```

Run the selected-image batch script:

```powershell
python src/run_batch_test_images.py
```

Depending on local paths, script arguments may need to be adjusted.

## Paper and Presentation

The project paper source is located at:

```text
paper/IEEE_Final_Project_Paper.tex
```

The latest strict paper source is the `.tex` file. A compiled PDF is intentionally not included in this GitHub release because the previously generated PDF was older than the final strict source. To generate the final PDF, compile `paper/IEEE_Final_Project_Paper.tex` with the files in `paper/figures/`, for example by using Overleaf or a local LaTeX installation.

The presentation files are located in:

```text
presentation/
```

## Limitations

- The test set is small: 12 selected formal test images.
- Edge alignment is a proxy metric, not a replacement for IoU or Dice score.
- No manually annotated ground-truth masks are included.
- The result should not be claimed as a universal improvement over SAM, YOLO-Seg, or supervised segmentation models.

## Future Work

- Add manually labeled ground-truth masks.
- Report IoU and Dice score.
- Expand testing to more poses, backgrounds, occlusion cases, and lighting conditions.
- Compare stronger segmentation baselines if project scope allows.
