# Download Model Weights

Model weights are intentionally excluded from this repository because they are large binary files.

Place these files in this folder before running the full experiment:

```text
model_weights/
  sam_vit_b_01ec64.pth
  yolov8n.pt
  yolov8n-seg.pt
```

## SAM ViT-B

The official Segment Anything repository provides checkpoint links for SAM model variants, including `vit_b`.

PowerShell download command:

```powershell
Invoke-WebRequest `
  -Uri "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth" `
  -OutFile "model_weights/sam_vit_b_01ec64.pth"
```

Official reference:

```text
https://github.com/facebookresearch/segment-anything
```

## YOLOv8n and YOLOv8n-Seg

Ultralytics documents `yolov8n.pt` for detection and `yolov8n-seg.pt` for instance segmentation. The Ultralytics package can download these pretrained models by filename.

From the repository root, run:

```powershell
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-seg.pt')"
Move-Item -Force yolov8n.pt model_weights/yolov8n.pt
Move-Item -Force yolov8n-seg.pt model_weights/yolov8n-seg.pt
```

Official reference:

```text
https://docs.ultralytics.com/models/yolov8/
```
