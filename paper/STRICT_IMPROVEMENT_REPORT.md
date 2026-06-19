# Strict Improvement Report

Target file:

```text
IEEE_Final_Project_Paper.tex
```

## Completed Improvements

0. Expanded the IEEE LaTeX source toward an approximately six-page paper.
   - Added multi-model design rationale.
   - Added version-design and execution-flow explanation.
   - Added dataset selection detail, per-version result interpretation, failure-mode analysis, and a concrete next-step evaluation plan.
   - Kept all claims tied to the existing 12-image edge-alignment experiment.

0a. Added roughly two more pages of IEEE-style content after the six-page expansion.
   - Added research-question framing in the introduction.
   - Added implementation details and an output-artifact table.
   - Added an evaluation protocol section and ablation-oriented interpretation.
   - Added threats to validity and practical implications sections.
   - Continued to avoid unsupported IoU, Dice, or broad generalization claims.

0b. Synchronized the paper package with the final compiled PDF supplied on June 19, 2026.
   - Treated `Final_Project_Paper.pdf` as the canonical final paper artifact.
   - Updated the IEEE author block to `Marco` and `YZU`, matching the final PDF.
   - Copied the final compiled PDF into the paper package.

1. Added an explicit system block diagram directly in LaTeX.
   - Separates the main proposed path from the baseline and evaluation path.
   - No external image conversion dependency is required.

2. Added a baseline/proposed method definition table.
   - Baseline: v1, SAM auto + Canny score + GrabCut.
   - Proposed final method: v6, YOLO detection + SAM + Canny + edge refinement + GrabCut.

3. Tightened the abstract and conclusion.
   - Now states the exact baseline score: 0.8708.
   - Now states the exact proposed score: 0.8855.
   - Now describes the gain as a modest 0.0147 absolute improvement.

4. Added a ground-truth evaluation gap section.
   - Explicitly states that IoU and Dice are not reported.
   - Explains that using model-generated masks as pseudo-ground truth would overstate reliability.

5. Reduced misleading author placeholders.
   - Replaced generic department placeholder with course-final-report wording.

## Not Fabricated

No IoU or Dice scores were added because the project does not currently include manually labeled ground-truth masks. Adding those numbers without annotation would make the paper less rigorous, not more rigorous.

## Remaining Real Improvement

The strongest next improvement is to manually label 3 to 5 ground-truth person masks, then compute IoU and Dice for v1 and v6.
