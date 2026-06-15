# Final Test Result Summary

## Photo Progress

- Raw photos added: 34
- Converted images: 34
- Selected formal test images: 12
- Completed batch-tested images: 12

## Main Quantitative Result

- Baseline: `v1_sam_auto_grabcut` mean edge alignment = `0.8708`
- Best final version: `v6_yolo_box_sam_edge_grabcut` mean edge alignment = `0.8855`
- Absolute improvement over baseline: `0.0147`
- Relative improvement over baseline: `1.7%`

## Interpretation

The final selected test set supports a refined conclusion: YOLO-guided SAM becomes most stable when edge refinement and GrabCut are included. Direct YOLO-Seg output is weaker, but GrabCut improves it substantially.

## Limitations

Edge alignment is a proxy metric. For a stronger final paper, add several ground-truth masks and report IoU/Dice.
