import argparse
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener


SUPPORTED_INPUTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip_path", default="raw_test_photos.zip")
    parser.add_argument("--raw_dir", default="test_images/raw")
    parser.add_argument("--processed_dir", default="test_images/final_selected")
    parser.add_argument("--max_side", type=int, default=1600)
    return parser.parse_args()


def safe_extract_zip(zip_path: Path, raw_dir: Path):
    raw_dir.mkdir(parents=True, exist_ok=True)
    root = raw_dir.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = (raw_dir / member.filename).resolve()
            if not str(target).startswith(str(root)):
                raise ValueError(f"Unsafe zip member path: {member.filename}")
        zf.extractall(raw_dir)


def iter_images(raw_dir: Path):
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUTS:
            yield path


def convert_to_jpg(source: Path, destination: Path, max_side: int):
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        img.save(destination, "JPEG", quality=94, optimize=True)


def main():
    args = parse_args()
    register_heif_opener()

    zip_path = Path(args.zip_path)
    raw_dir = Path(args.raw_dir)
    processed_dir = Path(args.processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if zip_path.exists():
        safe_extract_zip(zip_path, raw_dir)

    rows = []
    for index, image_path in enumerate(iter_images(raw_dir), start=1):
        output_name = f"test_{index:02d}_{image_path.stem}.jpg"
        output_path = processed_dir / output_name
        convert_to_jpg(image_path, output_path, args.max_side)
        rows.append((image_path, output_path))

    manifest = processed_dir / "manifest.csv"
    manifest.write_text(
        "source,processed\n"
        + "\n".join(f"{src.as_posix()},{dst.as_posix()}" for src, dst in rows)
        + "\n",
        encoding="utf-8",
    )

    print(f"Prepared {len(rows)} images in {processed_dir.resolve()}")
    for _, output_path in rows:
        print(output_path)


if __name__ == "__main__":
    main()
