import argparse
import csv
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_dir", default="test_images/final_selected")
    parser.add_argument("--checkpoint", default="model_weights/sam_vit_b_01ec64.pth")
    parser.add_argument("--model_type", default="vit_b")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output_root", default="experiment_versions_test_images")
    parser.add_argument("--yolo_model", default="model_weights/yolov8n.pt")
    parser.add_argument("--yolo_seg_model", default="model_weights/yolov8n-seg.pt")
    parser.add_argument("--points_per_side", type=int, default=16)
    parser.add_argument("--target_class", default="person")
    return parser.parse_args()


def parse_summary(summary_path: Path):
    if not summary_path.exists():
        return []
    with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    args = parse_args()
    image_dir = Path(args.image_dir)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not images:
        raise SystemExit(f"No images found in {image_dir}")

    all_rows = []
    for image_path in images:
        image_output = output_root / image_path.stem
        command = [
            sys.executable,
            str(SCRIPT_DIR / "run_experiment_versions.py"),
            "--image_path",
            str(image_path),
            "--checkpoint",
            args.checkpoint,
            "--model_type",
            args.model_type,
            "--device",
            args.device,
            "--output_root",
            str(image_output),
            "--points_per_side",
            str(args.points_per_side),
            "--target_class",
            args.target_class,
        ]
        if args.yolo_model:
            command.extend(["--yolo_model", args.yolo_model])
        if args.yolo_seg_model:
            command.extend(["--yolo_seg_model", args.yolo_seg_model])

        print(f"Running {image_path.name}")
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        (image_output / "batch_command.log").write_text(
            "COMMAND:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\n\nSTDERR:\n"
            + result.stderr,
            encoding="utf-8",
        )
        status = "ok" if result.returncode == 0 else f"failed: {result.returncode}"
        print(f"  {status}")

        for row in parse_summary(image_output / "summary.csv"):
            row["image"] = image_path.name
            all_rows.append(row)

    if all_rows:
        fieldnames = ["image"] + [name for name in all_rows[0].keys() if name != "image"]
        with (output_root / "batch_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)

        lines = [
            "# Batch Test Images Summary",
            "",
            "| Image | Version | Modules | Status | Mask source | Box source | Refined edge alignment |",
            "|---|---|---|---|---|---|---:|",
        ]
        for row in all_rows:
            lines.append(
                "| {image} | {version} | {modules} | {status} | {mask_source} | {box_source} | {edge} |".format(
                    image=row.get("image", ""),
                    version=row.get("version", ""),
                    modules=row.get("modules", ""),
                    status=row.get("status", ""),
                    mask_source=row.get("Mask source", ""),
                    box_source=row.get("Box source", ""),
                    edge=row.get("Refined edge alignment", ""),
                )
            )
        (output_root / "batch_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saved batch output to: {output_root.resolve()}")


if __name__ == "__main__":
    main()
