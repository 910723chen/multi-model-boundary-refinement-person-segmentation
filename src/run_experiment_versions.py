import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


VERSION_DEFINITIONS = [
    {
        "name": "v1_sam_auto_grabcut",
        "modules": "SAM auto + Canny score + GrabCut",
        "requires": [],
        "args": [],
    },
    {
        "name": "v2_sam_auto_edge_grabcut",
        "modules": "SAM auto + Canny score + Edge refine + GrabCut",
        "requires": [],
        "args": ["--edge_refine"],
    },
    {
        "name": "v3_box_sam_grabcut",
        "modules": "Manual box/points + SAM + Canny + GrabCut",
        "requires": ["box"],
        "args": [],
        "use_prompt": True,
    },
    {
        "name": "v4_box_sam_edge_only",
        "modules": "Manual box/points + SAM + Canny + Edge refine",
        "requires": ["box"],
        "args": ["--edge_refine", "--skip_grabcut"],
        "use_prompt": True,
    },
    {
        "name": "v5_yolo_box_sam_grabcut",
        "modules": "YOLO detection + SAM + Canny + GrabCut",
        "requires": ["yolo_model"],
        "args": [],
        "use_yolo": True,
    },
    {
        "name": "v6_yolo_box_sam_edge_grabcut",
        "modules": "YOLO detection + SAM + Canny + Edge refine + GrabCut",
        "requires": ["yolo_model"],
        "args": ["--edge_refine"],
        "use_yolo": True,
    },
    {
        "name": "v7_yolo_seg_only",
        "modules": "YOLO-Seg direct mask + Canny + Edge refine",
        "requires": ["yolo_seg_model"],
        "args": ["--edge_refine", "--skip_grabcut"],
        "use_yolo_seg": True,
    },
    {
        "name": "v8_yolo_seg_grabcut",
        "modules": "YOLO-Seg direct mask + Canny + GrabCut",
        "requires": ["yolo_seg_model"],
        "args": [],
        "use_yolo_seg": True,
    },
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--model_type", default="vit_b", choices=["vit_b", "vit_l", "vit_h"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output_root", default="experiment_versions")
    parser.add_argument("--gt_mask_path", default=None)

    parser.add_argument("--box", nargs=4, type=float, default=None)
    parser.add_argument("--pos_point", nargs=2, type=float, action="append", default=None)
    parser.add_argument("--neg_point", nargs=2, type=float, action="append", default=None)

    parser.add_argument("--yolo_model", default=None)
    parser.add_argument("--yolo_seg_model", default=None)
    parser.add_argument("--target_class", default="person")
    parser.add_argument("--min_confidence", type=float, default=0.15)
    parser.add_argument("--box_padding", type=float, default=0.10)

    parser.add_argument("--points_per_side", type=int, default=32)
    parser.add_argument("--grabcut_iter", type=int, default=5)
    parser.add_argument("--kernel_size", type=int, default=5)
    parser.add_argument("--canny_low", type=int, default=60)
    parser.add_argument("--canny_high", type=int, default=150)
    parser.add_argument("--max_refine_area_ratio", type=float, default=1.35)
    return parser.parse_args()


def is_missing_requirement(version, args):
    missing = []
    for requirement in version.get("requires", []):
        value = getattr(args, requirement)
        if value is None:
            missing.append(requirement)
    return missing


def add_repeated_points(command, flag, points):
    for point in points or []:
        command.extend([flag, str(point[0]), str(point[1])])


def build_command(version, args, output_dir):
    command = [
        sys.executable,
        str(SCRIPT_DIR / "sam_boundary_refinement.py"),
        "--image_path",
        args.image_path,
        "--checkpoint",
        args.checkpoint,
        "--model_type",
        args.model_type,
        "--device",
        args.device,
        "--output_dir",
        str(output_dir),
        "--points_per_side",
        str(args.points_per_side),
        "--grabcut_iter",
        str(args.grabcut_iter),
        "--kernel_size",
        str(args.kernel_size),
        "--canny_low",
        str(args.canny_low),
        "--canny_high",
        str(args.canny_high),
        "--max_refine_area_ratio",
        str(args.max_refine_area_ratio),
        "--target_class",
        args.target_class,
        "--min_confidence",
        str(args.min_confidence),
        "--box_padding",
        str(args.box_padding),
    ]

    if args.gt_mask_path:
        command.extend(["--gt_mask_path", args.gt_mask_path])

    if version.get("use_prompt"):
        command.extend(["--box", *[str(v) for v in args.box]])
        add_repeated_points(command, "--pos_point", args.pos_point)
        add_repeated_points(command, "--neg_point", args.neg_point)

    if version.get("use_yolo"):
        command.extend(["--yolo_model", args.yolo_model])

    if version.get("use_yolo_seg"):
        command.extend(["--yolo_seg_model", args.yolo_seg_model])

    command.extend(version.get("args", []))
    return command


def parse_metrics(metrics_path):
    metrics = {}
    if not metrics_path.exists():
        return metrics
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.startswith("==="):
            continue
        key, value = line.split(":", 1)
        metrics[key.strip()] = value.strip()
    return metrics


def write_summary_markdown(rows, output_root):
    lines = [
        "# Experiment Versions Summary",
        "",
        "| Version | Modules | Status | Mask source | Box source | Refined edge alignment | Refined IoU | Refined Dice |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {version} | {modules} | {status} | {mask_source} | {box_source} | {edge} | {iou} | {dice} |".format(
                version=row["version"],
                modules=row["modules"],
                status=row["status"],
                mask_source=row.get("Mask source", ""),
                box_source=row.get("Box source", ""),
                edge=row.get("Refined edge alignment", ""),
                iou=row.get("Refined IoU", ""),
                dice=row.get("Refined Dice", ""),
            )
        )
    (output_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for version in VERSION_DEFINITIONS:
        output_dir = output_root / version["name"]
        output_dir.mkdir(parents=True, exist_ok=True)
        missing = is_missing_requirement(version, args)
        row = {
            "version": version["name"],
            "modules": version["modules"],
            "output_dir": str(output_dir),
        }

        if missing:
            row["status"] = "skipped: " + "; ".join(missing)
            (output_dir / "SKIPPED.txt").write_text(
                "This version was skipped because the required input was not provided.\n\n"
                f"Missing requirement(s): {', '.join(missing)}\n\n"
                "For the new batch test images, v3 and v4 require a manual box or point prompt. "
                "They are kept as skipped until manual annotations are added.\n",
                encoding="utf-8",
            )
            rows.append(row)
            continue

        command = build_command(version, args, output_dir)
        (output_dir / "command.json").write_text(
            json.dumps(command, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        (output_dir / "run.log").write_text(
            "COMMAND:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + (result.stdout or "")
            + "\n\nSTDERR:\n"
            + (result.stderr or ""),
            encoding="utf-8",
        )

        row["status"] = "ok" if result.returncode == 0 else f"failed: {result.returncode}"
        row.update(parse_metrics(output_dir / "metrics.txt"))
        rows.append(row)

    fieldnames = [
        "version",
        "modules",
        "status",
        "output_dir",
        "Mask source",
        "Box source",
        "Input box",
        "YOLO model",
        "YOLO-Seg model",
        "SAM foreground pixels",
        "Refined foreground pixels",
        "SAM edge alignment",
        "Refined edge alignment",
        "SAM IoU",
        "SAM Dice",
        "Refined IoU",
        "Refined Dice",
    ]
    with (output_root / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    write_summary_markdown(rows, output_root)
    print(f"Saved experiment summary to: {output_root.resolve()}")


if __name__ == "__main__":
    main()
