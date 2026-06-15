from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv
import shutil


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "progress_report_speaker_package"
TEXT_DIR = PACKAGE / "scripts"
IMG_DIR = PACKAGE / "display_images"
CODE_DIR = IMG_DIR / "code"
RESULT_DIR = IMG_DIR / "results"
DIFF_DIR = IMG_DIR / "comparisons"


def ensure_dirs():
    for folder in [TEXT_DIR, CODE_DIR, RESULT_DIR, DIFF_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
        Path("C:/Windows/Fonts/msjhbd.ttc" if bold else "C:/Windows/Fonts/msjh.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONT_TITLE = font(48, bold=True)
FONT_H2 = font(34, bold=True)
FONT_BODY = font(26)
FONT_SMALL = font(21)
FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 21) if Path("C:/Windows/Fonts/consola.ttf").exists() else font(21)


def wrap_text(draw, text, max_width, fnt):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if draw.textlength(candidate, font=fnt) <= max_width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines

def draw_wrapped(draw, xy, text, max_width, fnt, fill="#172033", line_gap=8):
    x, y = xy
    for line in wrap_text(draw, text, max_width, fnt):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def write_text_file(name, content):
    (TEXT_DIR / name).write_text(content.strip() + "\n", encoding="utf-8")


def copy_if_exists(source, dest):
    source = ROOT / source
    if source.exists():
        shutil.copy2(source, dest)


def read_metrics(folder):
    metrics_path = ROOT / folder / "metrics.txt"
    metrics = {}
    if not metrics_path.exists():
        return metrics
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.startswith("==="):
            continue
        key, value = line.split(":", 1)
        metrics[key.strip()] = value.strip()
    return metrics


def render_code_image(title, source_path, patterns, output_path):
    lines = source_path.read_text(encoding="utf-8").splitlines()
    selected = []
    for pattern, count in patterns:
        start = next((idx for idx, line in enumerate(lines) if pattern in line), None)
        if start is None:
            continue
        selected.extend(lines[start:start + count])
        selected.append("")

    if not selected:
        selected = ["# snippet not found"]

    width, height = 1600, 950
    img = Image.new("RGB", (width, height), "#0F172A")
    draw = ImageDraw.Draw(img)
    draw.text((56, 42), title, font=FONT_H2, fill="#FFFFFF")
    draw.rounded_rectangle((48, 108, width - 48, height - 48), radius=18, fill="#111827", outline="#334155", width=2)

    y = 138
    line_no = 1
    for raw in selected[:30]:
        if y > height - 90:
            draw.text((86, y), "...", font=FONT_CODE, fill="#94A3B8")
            break
        display = raw.replace("\t", "    ")
        if len(display) > 104:
            display = display[:101] + "..."
        draw.text((76, y), f"{line_no:02d}", font=FONT_CODE, fill="#64748B")
        color = "#D1FAE5" if raw.lstrip().startswith(("def ", "class ")) else "#E5E7EB"
        if raw.lstrip().startswith("#"):
            color = "#94A3B8"
        draw.text((130, y), display, font=FONT_CODE, fill=color)
        y += 26
        line_no += 1

    img.save(output_path)


def render_version_matrix(output_path):
    rows = [
        ("v1", "SAM auto + Canny score + GrabCut", "Midterm baseline"),
        ("v2", "SAM auto + Edge refine + GrabCut", "Test light boundary refinement"),
        ("v3", "Box/point + SAM + GrabCut", "Test explicit prompts"),
        ("v4", "Box/point + SAM + Edge refine", "Check whether GrabCut over-refines"),
        ("v5", "YOLO box + SAM + GrabCut", "Automatic localization version"),
        ("v6", "YOLO box + SAM + Edge refine + GrabCut", "Recommended full version"),
        ("v7", "YOLO-Seg + Edge refine", "Bonus direct segmentation"),
        ("v8", "YOLO-Seg + GrabCut", "Compare YOLO-Seg post-processing"),
    ]
    width, height = 1800, 1180
    img = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    draw.text((70, 48), "Multi-Version Module Differences", font=FONT_TITLE, fill="#172033")
    draw.text((70, 112), "Each version changes only a few modules, making localization, segmentation, and post-processing effects easier to compare.", font=FONT_BODY, fill="#5B6475")

    x0, y0 = 70, 190
    row_h = 105
    col_w = [150, 760, 710]
    headers = ["Version", "Module Combination", "Purpose"]
    x = x0
    for idx, header in enumerate(headers):
        draw.rectangle((x, y0, x + col_w[idx], y0 + 70), fill="#172033")
        draw.text((x + 22, y0 + 20), header, font=FONT_BODY, fill="#FFFFFF")
        x += col_w[idx]
    y = y0 + 70
    colors = ["#EFF6FF", "#ECFDF5"]
    for i, row in enumerate(rows):
        fill = colors[i % 2]
        x = x0
        for idx, value in enumerate(row):
            draw.rectangle((x, y, x + col_w[idx], y + row_h), fill=fill, outline="#D8DEE9")
            draw_wrapped(draw, (x + 22, y + 26), value, col_w[idx] - 44, FONT_SMALL if idx else FONT_H2, "#172033")
            x += col_w[idx]
        y += row_h
    img.save(output_path)


def render_metrics_summary(output_path):
    entries = [
        ("Baseline", "outputs_full", "SAM auto + GrabCut"),
        ("Prompt SAM only", "outputs_sam_only", "Box/point + SAM"),
        ("YOLO improved", "outputs_yolo", "YOLO box + SAM + GrabCut"),
        ("Experiment v1", "experiment_versions/v1_sam_auto_grabcut", "Runner baseline"),
    ]
    rows = []
    for label, folder, modules in entries:
        m = read_metrics(folder)
        rows.append([
            label,
            modules,
            m.get("Box source", "-"),
            m.get("SAM edge alignment", "-"),
            m.get("Refined edge alignment", "-"),
            m.get("SAM foreground pixels", "-"),
            m.get("Refined foreground pixels", "-"),
        ])

    width, height = 1900, 980
    img = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    draw.text((70, 48), "Current Demo Result Summary", font=FONT_TITLE, fill="#172033")
    draw.text((70, 112), "A full GT set is not ready yet, so we compare versions using edge alignment and foreground area first.", font=FONT_BODY, fill="#5B6475")

    headers = ["Version", "Modules", "Box", "SAM edge", "Refined edge", "SAM pixels", "Refined pixels"]
    col_w = [230, 430, 190, 190, 230, 250, 260]
    x0, y0 = 55, 200
    row_h = 92
    x = x0
    for idx, header in enumerate(headers):
        draw.rectangle((x, y0, x + col_w[idx], y0 + 70), fill="#172033")
        draw.text((x + 14, y0 + 21), header, font=FONT_SMALL, fill="#FFFFFF")
        x += col_w[idx]
    y = y0 + 70
    for i, row in enumerate(rows):
        fill = "#F8FAFC" if i % 2 == 0 else "#EEF6FF"
        x = x0
        for idx, value in enumerate(row):
            draw.rectangle((x, y, x + col_w[idx], y + row_h), fill=fill, outline="#D8DEE9")
            draw_wrapped(draw, (x + 14, y + 22), str(value), col_w[idx] - 28, FONT_SMALL, "#172033", line_gap=4)
            x += col_w[idx]
        y += row_h
    img.save(output_path)


def render_result_grid(output_path):
    items = [
        ("Baseline: SAM auto + GrabCut", ROOT / "outputs_full" / "overlay_comparison.png"),
        ("Prompt: box/point + SAM only", ROOT / "outputs_sam_only" / "overlay_comparison.png"),
        ("YOLO: detection + SAM + GrabCut", ROOT / "outputs_yolo" / "overlay_comparison.png"),
    ]
    width, height = 1920, 2140
    img = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(img)
    draw.text((60, 42), "Result Comparison", font=FONT_TITLE, fill="#172033")
    draw.text((60, 105), "Output differences from the same test image under different module combinations.", font=FONT_BODY, fill="#5B6475")

    y = 175
    box_w, box_h = 1760, 560
    for title, path in items:
        draw.text((80, y), title, font=FONT_H2, fill="#172033")
        if path.exists():
            src = Image.open(path).convert("RGB")
            src.thumbnail((box_w, box_h - 75))
            draw.rounded_rectangle((70, y + 52, 1850, y + box_h), radius=18, fill="#FFFFFF", outline="#D8DEE9", width=2)
            img.paste(src, (80, y + 64))
        y += box_h + 55
    img.save(output_path)


def write_text_assets():
    (PACKAGE / "README.txt").write_text(
        """
Progress Report Package Guide

Suggested presentation order:
1. Open SAM_progress_report_visual.pptx and explain the project goal, midterm pipeline, current problem, improved pipeline, and final target.
2. Use scripts/01_full_speech.txt as the main speaking script.
3. Use scripts/02_slide_by_slide_notes.txt for slide-level reminders.
4. Use scripts/03_demo_flow.txt for the live demonstration order.
5. Use scripts/04_version_differences.txt and display_images/comparisons when explaining the version matrix.
6. Use scripts/05_expected_questions.txt for likely professor questions.

Package contents:
- scripts: full speech, slide notes, demo flow, version differences, and expected questions.
- display_images/code: code screenshots for Edge refine, YOLO modules, and the multi-version runner.
- display_images/results: original image, baseline result, prompt result, YOLO result, and edge map.
- display_images/comparisons: version matrix, result comparison grid, and metric summary.

Main message:
- The project is no longer a single-model demo. It compares SAM, Edge Map, GrabCut, YOLO detection, and YOLO-Seg across multiple versions.
- The midterm issue is unstable target selection and boundary refinement, so the final focus is module comparison and measurable improvement.
- The scope stays appropriate for an undergraduate final project.
        """.strip() + "\n",
        encoding="utf-8",
    )
    write_text_file(
        "01_full_speech.txt",
        """
Good morning/afternoon Professor. This progress report is about improving boundary judgment in a visual recognition pipeline.

At the midterm stage, we completed the first version of the system. The pipeline used SAM to automatically generate segmentation masks, selected the best mask with rule-based filtering, and then applied GrabCut for boundary refinement. This version could produce the mask, refined mask, overlay comparison, and metrics. However, the result also showed a clear problem: SAM auto mode sometimes selected the face, the wall, or only a partial region instead of the complete target.

After that, we added a Canny edge map to inspect the image boundaries. The edge map captures the human outline reasonably well, which means the image itself already contains useful boundary information. The main problem is not that the boundary is missing. The real problem is that SAM does not know which target it should segment at the beginning. If the initial mask is wrong, GrabCut can only make the wrong result smoother. It cannot fix the target-selection problem from the root.

Therefore, the current improvement direction is to add clearer target prompts and run multi-version experiments. The code now supports manual boxes, positive and negative point prompts, YOLO automatic box detection, YOLO-Seg direct masks, Edge refine, and GrabCut safeguards. These modules are separated into different versions, such as the SAM auto baseline, box-prompt version, YOLO-box version, and YOLO-Seg bonus version.

The current demo results include the midterm baseline, the manual-prompt version, the YOLO-improved version, and the edge map. In the YOLO result, YOLO first localizes the person, so SAM receives a clearer region to segment. The output is closer to the complete person, and the refined edge alignment is also higher than the original baseline. This suggests that adding a localization model can reduce SAM selecting the wrong region.

For the final project, the next step is to prepare 10 to 20 test images, run all versions, and generate summary.csv and summary.md. If time allows, we will add ground-truth masks and use IoU and Dice as formal quantitative metrics. The final presentation will compare the original image, baseline result, improved result, edge map, and metric table to show that the system improved from single SAM auto segmentation into a multi-stage pipeline with YOLO localization, SAM segmentation, and Canny / GrabCut boundary refinement.
        """,
    )
    write_text_file(
        "02_slide_by_slide_notes.txt",
        """
Slide 1: Introduce the project topic and final direction: boundary refinement for visual recognition.
Slide 2: Review the midterm baseline. SAM auto + GrabCut can generate outputs, but target selection is unstable.
Slide 3: Explain the main issue. The edge map contains boundary information, but SAM lacks a clear target prompt.
Slide 4: Present the final pipeline: YOLO or manual box localization, SAM segmentation, and Canny / GrabCut boundary refinement.
Slide 5: Explain model roles: YOLO localizes, SAM segments, Canny provides boundary cues, and GrabCut refines locally.
Slide 6: Explain the multi-version test matrix from v1 to v8.
Slide 7: Explain the experiment design: compare baseline and improved versions, then add IoU / Dice.
Slide 8: Show the supported code features: box, positive/negative points, YOLO, edge_refine, and skip_grabcut.
Slide 9: Define the final scope: required items, bonus items, and out-of-scope items.
        """,
    )
    write_text_file(
        "03_demo_flow.txt",
        """
Suggested demo sequence:

1. Open the PPT and explain the project goal and midterm pipeline.
2. Show outputs_full/overlay_comparison.png and explain that SAM auto may select a partial region.
3. Show edge_map.png and explain that boundary information exists, but the model does not know the target.
4. Show outputs_sam_only/overlay_comparison.png and explain the effect of box/point prompts.
5. Show outputs_yolo/overlay_comparison.png and explain that YOLO localization makes the result closer to the full person.
6. Show version_differences.png to explain the multi-version comparison design.
7. Show metric_summary.png to explain the current use of edge alignment and foreground pixels.
8. End with the next step: add more test images, ground-truth masks, IoU, and Dice.

Command for the multi-version runner:

python run_experiment_versions.py --image_path test.JPG --checkpoint sam_vit_b_01ec64.pth --model_type vit_b --box 550 0 4050 3455 --pos_point 2500 1650 --neg_point 4300 1600 --yolo_model yolov8n.pt --output_root experiment_versions

Command for testing YOLO-Seg:

python run_experiment_versions.py --image_path test.JPG --checkpoint sam_vit_b_01ec64.pth --model_type vit_b --box 550 0 4050 3455 --pos_point 2500 1650 --neg_point 4300 1600 --yolo_model yolov8n.pt --yolo_seg_model yolov8n-seg.pt --output_root experiment_versions
        """,
    )
    write_text_file(
        "04_version_differences.txt",
        """
v1_sam_auto_grabcut:
Uses SAM automatic mask generation and GrabCut. This is the midterm baseline.

v2_sam_auto_edge_grabcut:
Adds Edge refine on top of SAM auto mode to test whether Canny boundary cues improve the mask.

v3_box_sam_grabcut:
Uses a manual box plus positive/negative point prompts for SAM, then applies GrabCut. This tests prompt stability.

v4_box_sam_edge_only:
Uses manual box/point prompts and Edge refine, but disables GrabCut. This checks whether GrabCut over-refines the result.

v5_yolo_box_sam_grabcut:
Uses YOLO to detect the person box, then sends it to SAM and GrabCut. This is the practical automatic version.

v6_yolo_box_sam_edge_grabcut:
Enables YOLO localization, SAM segmentation, Edge refine, and GrabCut. This is the recommended full version.

v7_yolo_seg_only:
Uses YOLO-Seg to generate a segmentation mask directly, then applies Edge refine. This is a bonus version.

v8_yolo_seg_grabcut:
Uses YOLO-Seg direct masks with GrabCut post-processing to compare direct segmentation and refinement.
        """,
    )
    write_text_file(
        "05_expected_questions.txt",
        """
Q1: Why add YOLO?
A: SAM auto mode does not always know which target to segment. YOLO first detects the person box, which gives SAM a clearer target region.

Q2: If Canny already finds edges, why still use SAM?
A: Canny only detects where edges exist. It does not know which edges belong to the target object. SAM provides the semantic mask, while Canny is used only as a boundary reference.

Q3: Why can GrabCut sometimes make the result worse?
A: GrabCut depends on the initial mask. If the initial mask is wrong, GrabCut may smooth the wrong result. This is why the current code includes skip_grabcut and area-ratio safeguards.

Q4: How will the final project prove improvement?
A: The final comparison will run baseline and improved versions on multiple test images, then compare IoU, Dice, edge alignment, and visualization results.

Q5: Why not train a custom model?
A: This is a course project. The goal is to integrate and compare existing models. Training a new model would require a larger dataset, more hardware, and a much wider project scope.
        """,
    )

def main():
    ensure_dirs()
    write_text_assets()

    copy_if_exists("outputs_full/overlay_comparison.png", RESULT_DIR / "01_baseline_sam_auto_grabcut.png")
    copy_if_exists("outputs_sam_only/overlay_comparison.png", RESULT_DIR / "02_prompt_sam_only.png")
    copy_if_exists("outputs_yolo/overlay_comparison.png", RESULT_DIR / "03_yolo_box_sam_grabcut.png")
    copy_if_exists("outputs_yolo/edge_map.png", RESULT_DIR / "04_edge_map.png")
    copy_if_exists("test.JPG", RESULT_DIR / "00_original_test_image.JPG")

    render_code_image(
        "Code Snippet: Edge Refine",
        ROOT / "sam_boundary_refinement.py",
        [("def refine_with_edge_candidates", 42)],
        CODE_DIR / "01_edge_refine_code.png",
    )
    render_code_image(
        "Code Snippet: YOLO / YOLO-Seg Modules",
        ROOT / "sam_boundary_refinement.py",
        [("def detect_box_with_yolo", 42), ("def detect_mask_with_yolo_seg", 44)],
        CODE_DIR / "02_yolo_modules_code.png",
    )
    render_code_image(
        "Code Snippet: Multi-Version Runner",
        ROOT / "run_experiment_versions.py",
        [("VERSION_DEFINITIONS", 58), ("def build_command", 42)],
        CODE_DIR / "03_experiment_runner_code.png",
    )

    render_version_matrix(DIFF_DIR / "01_version_differences.png")
    render_result_grid(DIFF_DIR / "02_result_comparison_grid.png")
    render_metrics_summary(DIFF_DIR / "03_metric_summary.png")

    print(PACKAGE)


if __name__ == "__main__":
    main()
