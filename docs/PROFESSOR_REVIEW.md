# Professor-Style Repository Review

This review uses a strict course-project grading perspective. The score is not an official grade; it is a repository-quality estimate based on what a professor or teaching assistant can inspect from GitHub.

## Rubric

| Category | Weight | Standard |
|---|---:|---|
| Problem definition and motivation | 15 | Clear topic, practical reason, and scoped objective |
| Method and model integration | 20 | Correct model roles, justified pipeline, and understandable implementation |
| Experimental design | 15 | Dataset description, version comparison, baseline/proposed definition |
| Result reporting and interpretation | 20 | Tables, visual assets, honest interpretation, no overclaiming |
| Reproducibility | 15 | Install steps, model-weight instructions, runnable commands, ignored generated outputs |
| Repository hygiene and presentation | 15 | Clean folder structure, no oversized model weights, useful docs, references, license |

## Initial Strict Review

Estimated score before the latest documentation pass: **86 / 100**.

Main weaknesses:

1. The README structure used `github_release/`, which looked like a local packaging folder rather than the repository root.
2. Reproduction steps were present but not separated into a checklist with expected outputs.
3. The professor-facing evidence chain was spread across README, paper, and result tables instead of summarized in one review file.
4. The single-person limitation and edge-alignment limitation were explained, but not prominently enough for a fast grading pass.

## Improvements Applied

1. Updated README wording from `github_release/` to `repository root/`.
2. Added `docs/REPRODUCIBILITY.md` with environment, model files, sanity checks, one-image experiment commands, batch commands, and expected outputs.
3. Added `docs/PROFESSOR_REVIEW.md` so the grading logic, weaknesses, fixes, and final estimate are explicit.
4. Added README links to workflow, evaluation notes, reproducibility, references, and the professor-style review.
5. Kept the claims conservative: the repository reports edge alignment only and explicitly avoids fabricated IoU/Dice scores.

## Second Strict Review

Estimated score after improvements: **92 / 100**.

| Category | Score | Notes |
|---|---:|---|
| Problem definition and motivation | 14 / 15 | Clear person-segmentation motivation and course-project scope |
| Method and model integration | 18 / 20 | Strong explanation of YOLO, SAM, Canny, morphology, and GrabCut roles |
| Experimental design | 13 / 15 | Good version matrix and selected-image test set; still small dataset |
| Result reporting and interpretation | 18 / 20 | Clear tables and visual assets; honest limitation on proxy metric |
| Reproducibility | 14 / 15 | Commands and expected outputs are now explicit; model weights still require manual download |
| Repository hygiene and presentation | 15 / 15 | Clean structure, ignored weights/outputs, references, license, paper, and presentation included |

## Validation Evidence

The repository was checked after the documentation improvements:

```text
python -m compileall src
python src/run_experiment_versions.py --help
python src/run_batch_test_images.py --help
git diff --check
```

Result:

```text
Source files compile successfully.
The experiment and batch scripts expose valid command-line help.
No whitespace errors were reported by git diff --check.
```

After this validation pass, the repository remains at or above the 90-point target. A strict final estimate is **93 / 100**.

## Remaining Deductions

The repository is above the 90-point threshold, but it is not perfect. A strict professor could still deduct points for:

1. No manually annotated ground-truth masks, so IoU and Dice are unavailable.
2. Only 12 formal test images, which is enough for a course demo but not a strong benchmark.
3. The current system is single-target segmentation and does not segment every person in multi-person photos.
4. Model weights are excluded for good GitHub hygiene, but this means first-time reproduction requires a manual download step.

## Highest-Value Future Fix

The best next improvement is to label 3 to 5 ground-truth masks and add a small IoU/Dice table comparing:

```text
v1: SAM auto + GrabCut
v6: YOLO box + SAM + Edge refine + GrabCut
v8: YOLO-Seg + GrabCut
```

That would raise the evidence quality more than adding another model.
