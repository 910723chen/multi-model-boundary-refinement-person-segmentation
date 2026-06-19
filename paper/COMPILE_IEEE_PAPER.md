# Compile Instructions

This folder contains an IEEE-style LaTeX paper for the final project.

Main file:

```text
IEEE_Final_Project_Paper.tex
```

Current source status:

```text
Final_Project_Paper.pdf is now the canonical final compiled paper artifact provided on June 19, 2026. The LaTeX source has been expanded from the previous 5-page draft toward a longer IEEE conference paper and synchronized with the final PDF's author block: Marco, Artificial Intelligence Applications Course Project, Course Final Report, YZU.
```

Required local files:

```text
figures/photo_progress_card.png
figures/final_version_bar_chart.png
figures/representative_case_comparison.jpg
figures/limitation_case_comparison.jpg
```

`references.bib` is kept as a backup/reference file, but the current `.tex` already includes the reference list directly with `thebibliography`.

Compile with a local LaTeX installation:

```powershell
pdflatex IEEE_Final_Project_Paper.tex
pdflatex IEEE_Final_Project_Paper.tex
```

The current checked machine did not expose `pdflatex`, `xelatex`, `lualatex`, `latexmk`, or `tectonic` in PowerShell, so the LaTeX source was prepared and checked, but not locally compiled into a new IEEE PDF.

Overleaf workflow:

1. Upload `IEEE_Final_Project_Paper.tex`.
2. Upload the whole `figures` folder.
3. Set the compiler to pdfLaTeX.
4. Compile.
