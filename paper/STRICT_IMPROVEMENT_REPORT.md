# Strict Improvement Report

Target file:

```text
IEEE_Final_Project_Paper.tex
```

## Completed Improvements

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
