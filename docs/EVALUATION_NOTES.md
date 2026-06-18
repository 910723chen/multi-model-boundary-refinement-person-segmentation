# Evaluation Notes

This document explains the evaluation metric and the main version-level observations.

## Edge Alignment

The project uses refined edge alignment as the main quantitative metric. It estimates how much of a segmentation mask boundary is close to visible image edges detected by Canny.

The implementation is in `src/sam_boundary_refinement.py`:

```python
boundary = mask_boundary(mask, kernel_size=3)
edge_nearby = cv2.dilate(edge_map.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1)
matched = np.logical_and(boundary > 0, edge_nearby > 0).sum()
score = matched / boundary_pixels
```

The process is:

1. Build a Canny edge map from the input image.
2. Extract the mask boundary using dilation minus erosion.
3. Dilate the Canny edge map with a 5x5 kernel to allow a small pixel-level tolerance.
4. Count how many boundary pixels overlap with nearby image edges.
5. Divide the matched boundary pixels by all boundary pixels.

Formula:

```text
edge alignment = matched mask-boundary pixels / total mask-boundary pixels
```

For example, an edge-alignment score of `0.8855` means that about `88.55%` of the refined mask boundary lies near detected image edges.

## Why Edge Alignment Is Only a Proxy Metric

Edge alignment is useful for checking boundary quality, but it is not equivalent to full segmentation accuracy.

It has several limitations:

- It only checks whether the boundary is close to Canny edges.
- It does not verify whether the whole person region is correct.
- Background edges may increase the score if the mask boundary happens to align with them.
- Weak or noisy Canny edges can affect the score.

For stronger evaluation, future versions should add manually labeled ground-truth masks and report IoU and Dice score.

## Why v7 Is Weak

Version `v7_yolo_seg_only` is:

```text
YOLO-Seg direct mask + Canny + Edge refine
```

It performed much weaker than the other final versions:

```text
v7 mean edge alignment = 0.5768
v8 mean edge alignment = 0.7918
v6 mean edge alignment = 0.8855
```

The main reasons are:

1. `v7` does not use SAM. The final mask depends only on YOLO-Seg.
2. `yolov8n-seg.pt` is a lightweight instance-segmentation model, so its masks can be coarse around hair, arms, legs, clothing, and complex backgrounds.
3. `v7` skips GrabCut, so it cannot recover local foreground-background boundaries.
4. The edge-refinement step only tests small morphology changes such as open, close, erode, and dilate. It cannot rebuild missing body parts or correct a poorly shaped mask.

This explains why `v8` improves over `v7`: `v8` uses the same YOLO-Seg initial mask, but adds GrabCut refinement.

## Why Multi-Person Photos Only Produce One Person

The current pipeline is designed for single-target person segmentation. YOLO may detect multiple people, but the code selects one best person box using:

```text
score = confidence * sqrt(box area)
```

Then only that box is sent to SAM. After that, mask cleanup keeps the largest connected component. As a result, multi-person photos usually produce one segmented person.

To support multi-person segmentation, the pipeline should iterate through every detected YOLO person box, run SAM on each box, and export either one combined mask or one instance mask per person.
