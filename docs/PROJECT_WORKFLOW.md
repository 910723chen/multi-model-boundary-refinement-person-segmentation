# Project Workflow

This document summarizes the full workflow of the project, from topic selection to final conclusions.

## 1. Motivation

Person segmentation is useful in image editing, background replacement, and many visual recognition tasks. However, real-world photos often contain complex backgrounds, multiple people, clothing with similar colors to the environment, or unclear object boundaries. These conditions make the boundary of a segmentation mask unstable.

The midterm version used SAM automatic mask generation followed by rule-based mask selection and GrabCut refinement. The main limitation was that SAM automatic mode sometimes selected a face, a wall, or another local region instead of the target person. Since post-processing can only refine the initial mask, a wrong initial mask usually leads to a wrong final result.

The final project therefore studies a multi-model pipeline. YOLO is used to localize the person first, SAM is used to generate the person mask from the prompt, Canny edges provide boundary cues, and GrabCut performs local foreground-background refinement.

## 2. Experiment Design

The test set was built from 34 newly added photos. After conversion and normalization, 12 images were selected as the formal test set. The selection considered person-detection confidence, person area ratio, image diversity, and whether the image was suitable for comparing segmentation boundaries.

The project compares multiple versions instead of only reporting one final pipeline:

| Version | Module Combination | Purpose |
|---|---|---|
| v1 | SAM auto + Canny score + GrabCut | Baseline |
| v2 | SAM auto + Canny score + Edge refine + GrabCut | Tests whether edge refinement helps SAM auto |
| v3 | Manual box/points + SAM + Canny + GrabCut | Manual prompt version, skipped in batch tests without annotations |
| v4 | Manual box/points + SAM + Canny + Edge refine | Manual prompt version, skipped in batch tests without annotations |
| v5 | YOLO detection + SAM + Canny + GrabCut | Tests YOLO localization as a SAM prompt |
| v6 | YOLO detection + SAM + Canny + Edge refine + GrabCut | Final full pipeline |
| v7 | YOLO-Seg direct mask + Canny + Edge refine | Direct YOLO-Seg comparison without SAM or GrabCut |
| v8 | YOLO-Seg direct mask + Canny + GrabCut | Tests whether GrabCut improves YOLO-Seg output |

## 3. Model Cooperation

The final pipeline is:

```text
Input image
-> CLAHE contrast enhancement
-> Canny edge map
-> YOLO person localization
-> SAM box-prompt segmentation
-> morphological cleanup
-> optional edge refinement
-> GrabCut foreground refinement
-> masks, visual comparison, and metrics
```

Each module has a clear role:

| Module | Role | Reason |
|---|---|---|
| YOLOv8n | Finds the target person box | Reduces target ambiguity before SAM |
| SAM ViT-B | Generates the segmentation mask | Produces prompt-based object masks |
| Canny | Provides edge information | Supports boundary scoring and edge-aware refinement |
| Morphology | Cleans the mask | Removes noise and keeps the largest connected component |
| GrabCut | Refines foreground/background separation | Improves local boundaries when the initial mask is reasonable |
| YOLOv8n-Seg | Direct segmentation baseline | Tests whether direct instance segmentation can replace YOLO-guided SAM |

The main design idea is that YOLO answers "where is the person?", SAM answers "what is the person shape?", Canny provides boundary evidence, and GrabCut adjusts the local foreground-background separation.

## 4. Output Review

Each experiment version produces:

| File | Description |
|---|---|
| `sam_mask.png` | Initial SAM or YOLO-Seg mask |
| `refined_mask.png` | Final mask after edge refinement or GrabCut |
| `edge_map.png` | Canny edge map |
| `overlay_comparison.png` | Original image, initial mask, and refined mask comparison |
| `metrics.txt` | Parameters, mask source, box source, foreground area, and edge alignment |
| `summary.csv` / `summary.md` | Per-image version comparison |
| `batch_summary.csv` / `batch_summary.md` | Batch result over all selected images |

The final release keeps the summary tables in `results/summary_tables/` and representative visual assets in `results/visual_assets/`.

## 5. Main Result

The selected 12-image test set produced the following mean edge-alignment results:

| Version | Mean Edge Alignment |
|---|---:|
| v1 SAM auto + GrabCut | 0.8708 |
| v2 SAM auto + Edge refine + GrabCut | 0.8666 |
| v5 YOLO box + SAM + GrabCut | 0.8422 |
| v6 YOLO box + SAM + Edge refine + GrabCut | 0.8855 |
| v7 YOLO-Seg + Edge refine | 0.5768 |
| v8 YOLO-Seg + GrabCut | 0.7918 |

The best version was `v6_yolo_box_sam_edge_grabcut`, with a mean edge-alignment score of `0.8855`. Compared with the baseline `v1_sam_auto_grabcut` score of `0.8708`, this is an absolute improvement of `0.0147`, or about `1.7%` relative.

## 6. Conclusion

This project shows that a multi-model workflow can make person boundary segmentation more stable than relying only on SAM automatic mask generation. SAM automatic mode can generate masks, but in complex or multi-person images it may choose the wrong target. YOLO localization helps SAM focus on the target person, while edge refinement and GrabCut can further improve local boundary alignment.

The final result supports the conclusion that YOLO-guided SAM with edge refinement and GrabCut is the most stable version among the tested pipelines. However, the improvement should be interpreted carefully because edge alignment is a proxy metric, not a full segmentation accuracy metric.

## 7. Future Work

Future work should add manually labeled ground-truth masks so IoU and Dice score can be reported. The system could also be extended from single-person segmentation to multi-person segmentation by processing every YOLO person box, generating one mask per person, and then combining or separately exporting the instance masks.

The test set should also be expanded to include more diverse cases such as crowded scenes, low-light photos, occlusions, and complex backgrounds. This would help determine whether the YOLO-guided SAM workflow remains stable under more challenging real-world conditions.
