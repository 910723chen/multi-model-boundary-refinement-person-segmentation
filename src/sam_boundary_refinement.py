import argparse
from pathlib import Path
import numpy as np
import cv2
import matplotlib.pyplot as plt

try:
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
except ImportError as e:
    raise SystemExit(
        "Please install segment-anything first: pip install segment-anything\n"
        f"Original error: {e}"
    )


def load_image_rgb(image_path: str) -> np.ndarray:
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def build_sam(model_type: str, checkpoint: str, device: str):
    sam = sam_model_registry[model_type](checkpoint=checkpoint)
    sam.to(device=device)
    return sam


def preprocess_for_sam(image_rgb: np.ndarray) -> np.ndarray:
    """
    Slightly enhance contrast so SAM can identify the main object more easily.
    """
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    out = cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)
    return out


def mask_bbox(mask: np.ndarray):
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return None
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()
    return x1, y1, x2, y2


def clamp_box(box, image_shape):
    h, w = image_shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in box]
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid box after clipping: {(x1, y1, x2, y2)}")
    return np.array([x1, y1, x2, y2], dtype=np.float32)


def expand_box(box, image_shape, padding_ratio=0.05):
    x1, y1, x2, y2 = [float(v) for v in box]
    bw = x2 - x1
    bh = y2 - y1
    pad_x = bw * padding_ratio
    pad_y = bh * padding_ratio
    return clamp_box([x1 - pad_x, y1 - pad_y, x2 + pad_x, y2 + pad_y], image_shape)


def build_point_prompts(positive_points=None, negative_points=None):
    coords = []
    labels = []

    for point in positive_points or []:
        coords.append([float(point[0]), float(point[1])])
        labels.append(1)

    for point in negative_points or []:
        coords.append([float(point[0]), float(point[1])])
        labels.append(0)

    if not coords:
        return None, None

    return np.array(coords, dtype=np.float32), np.array(labels, dtype=np.int32)


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    if num_labels <= 1:
        return mask.astype(np.uint8)
    largest_idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    return (labels == largest_idx).astype(np.uint8)


def morphological_clean(mask: np.ndarray, kernel_size=5) -> np.ndarray:
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    out = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=1)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, kernel, iterations=1)
    out = keep_largest_component(out)
    return (out > 0).astype(np.uint8)


def build_edge_map(image_rgb: np.ndarray, canny_low=60, canny_high=150) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, canny_low, canny_high)
    return (edges > 0).astype(np.uint8)


def mask_boundary(mask: np.ndarray, kernel_size=3) -> np.ndarray:
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    dilated = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)
    eroded = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
    return ((dilated - eroded) > 0).astype(np.uint8)


def compute_edge_alignment_score(mask: np.ndarray, edge_map: np.ndarray) -> float:
    boundary = mask_boundary(mask, kernel_size=3)
    boundary_pixels = int(boundary.sum())
    if boundary_pixels == 0:
        return 0.0

    # Allow a small distance tolerance so 1-2 px offsets are not treated as failures.
    edge_nearby = cv2.dilate(edge_map.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1)
    matched = np.logical_and(boundary > 0, edge_nearby > 0).sum()
    return float(matched / boundary_pixels)


def refine_with_edge_candidates(
    mask: np.ndarray,
    edge_map: np.ndarray,
    kernel_size=3,
    min_area_ratio=0.80,
    max_area_ratio=1.25
) -> np.ndarray:
    kernel_size = max(1, int(kernel_size))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    base = mask.astype(np.uint8)
    base_area = max(int(base.sum()), 1)

    candidates = [
        ("base", base),
        ("open", cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel, iterations=1)),
        ("close", cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel, iterations=1)),
        ("erode", cv2.erode(base, kernel, iterations=1)),
        ("dilate", cv2.dilate(base, kernel, iterations=1)),
    ]

    best_mask = base
    best_score = compute_edge_alignment_score(base, edge_map)

    for _, candidate in candidates:
        candidate = keep_largest_component((candidate > 0).astype(np.uint8))
        area_ratio = candidate.sum() / base_area
        if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
            continue
        score = compute_edge_alignment_score(candidate, edge_map)
        if score > best_score:
            best_score = score
            best_mask = candidate

    return morphological_clean(best_mask, kernel_size=kernel_size)


def compute_mask_score(
    mask: np.ndarray,
    image_shape,
    target_aspect=0.75,
    border_margin_ratio=0.03,
    edge_map=None
):
    """
    Scoring goals:
    - Avoid masks touching the image border.
    - Prefer reasonable area.
    - Prefer a roughly rectangular region.
    - Prefer masks near the center.
    - Prefer an aspect ratio similar to the input photo.
    """
    h, w = image_shape[:2]
    img_area = h * w
    area = float(mask.sum())
    area_ratio = area / img_area

    # Reject masks that are clearly too small or too large.
    if area_ratio < 0.03 or area_ratio > 0.60:
        return -1e9

    bbox = mask_bbox(mask)
    if bbox is None:
        return -1e9

    x1, y1, x2, y2 = bbox
    bw = max(1, x2 - x1 + 1)
    bh = max(1, y2 - y1 + 1)
    bbox_area = bw * bh

    # 1. Reject objects touching the image border.
    margin_x = int(w * border_margin_ratio)
    margin_y = int(h * border_margin_ratio)
    touches_border = (
        x1 <= margin_x or
        y1 <= margin_y or
        x2 >= w - 1 - margin_x or
        y2 >= h - 1 - margin_y
    )
    if touches_border:
        return -1e8

    # 2. Rectangularity.
    rectangularity = area / bbox_area  # Photos are usually close to rectangular.
    if rectangularity < 0.45:
        return -1e7

    # 3. Aspect ratio.
    aspect = bw / bh
    aspect_diff = abs(aspect - target_aspect)
    aspect_score = max(0.0, 1.0 - aspect_diff / 1.2)

    # 4. Distance from center.
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    img_cx = w / 2.0
    img_cy = h / 2.0
    dist = np.sqrt((cx - img_cx) ** 2 + (cy - img_cy) ** 2)
    max_dist = np.sqrt(img_cx ** 2 + img_cy ** 2)
    center_score = 1.0 - dist / max_dist

    # 5. Area score: prefer medium-sized masks.
    # For this sample image, the photo region is usually around 5%-20%.
    if area_ratio < 0.05:
        area_score = area_ratio / 0.05
    elif area_ratio <= 0.20:
        area_score = 1.0
    else:
        area_score = max(0.0, 1.0 - (area_ratio - 0.20) / 0.40)

    score = (
        0.35 * rectangularity +
        0.25 * center_score +
        0.20 * aspect_score +
        0.20 * area_score
    )
    if edge_map is not None:
        edge_score = compute_edge_alignment_score(mask, edge_map)
        score = 0.80 * score + 0.20 * edge_score
    return score


def get_best_mask_from_sam(
    image_rgb: np.ndarray,
    sam,
    points_per_side=32,
    target_aspect=0.75,
    edge_map=None,
    morph_kernel=5
) -> np.ndarray:
    generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=points_per_side,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.90,
        min_mask_region_area=500
    )
    masks = generator.generate(image_rgb)
    if not masks:
        raise RuntimeError("SAM did not generate any mask.")

    best_score = -1e9
    best_mask = None

    for m in masks:
        seg = m["segmentation"].astype(np.uint8)
        seg = keep_largest_component(seg)
        score = compute_mask_score(
            seg,
            image_rgb.shape,
            target_aspect=target_aspect,
            edge_map=edge_map
        )
        if score > best_score:
            best_score = score
            best_mask = seg

    if best_mask is None:
        # Fallback: choose a larger mask that is closest to the center.
        h, w = image_rgb.shape[:2]
        img_cx, img_cy = w / 2.0, h / 2.0
        fallback_best = None
        fallback_score = -1e9
        for m in masks:
            seg = keep_largest_component(m["segmentation"].astype(np.uint8))
            bbox = mask_bbox(seg)
            if bbox is None:
                continue
            x1, y1, x2, y2 = bbox
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            dist = np.sqrt((cx - img_cx) ** 2 + (cy - img_cy) ** 2)
            score = float(seg.sum()) - 2.0 * dist
            if score > fallback_score:
                fallback_score = score
                fallback_best = seg
        if fallback_best is None:
            raise RuntimeError("Failed to select a valid SAM mask.")
        best_mask = fallback_best

    return morphological_clean(best_mask, kernel_size=morph_kernel)


def get_best_mask_from_prompt(
    image_rgb: np.ndarray,
    sam,
    box=None,
    positive_points=None,
    negative_points=None,
    edge_map=None,
    morph_kernel=5
) -> np.ndarray:
    predictor = SamPredictor(sam)
    predictor.set_image(image_rgb)

    input_box = clamp_box(box, image_rgb.shape) if box is not None else None
    point_coords, point_labels = build_point_prompts(positive_points, negative_points)

    masks, scores, _ = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        box=input_box,
        multimask_output=True
    )

    best_score = -1e9
    best_mask = None

    for mask, sam_score in zip(masks, scores):
        seg = keep_largest_component(mask.astype(np.uint8))
        edge_score = compute_edge_alignment_score(seg, edge_map) if edge_map is not None else 0.0
        # The box prompt already gives the target location, so SAM confidence is primary.
        # The edge score is only a supporting signal here.
        score = 0.85 * float(sam_score) + 0.15 * edge_score
        if score > best_score:
            best_score = score
            best_mask = seg

    if best_mask is None:
        raise RuntimeError("SAM prompt did not generate any mask.")

    return morphological_clean(best_mask, kernel_size=morph_kernel)


def detect_box_with_yolo(
    image_rgb: np.ndarray,
    yolo_model_path: str,
    target_class="person",
    min_confidence=0.25,
    padding_ratio=0.05
):
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(
            "YOLO auto box needs ultralytics. Install it with: pip install ultralytics\n"
            f"Original error: {e}"
        )

    model = YOLO(yolo_model_path)
    results = model.predict(source=image_rgb, conf=min_confidence, verbose=False)
    if not results:
        raise RuntimeError("YOLO did not return any result.")

    result = results[0]
    names = result.names
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        raise RuntimeError("YOLO did not detect any object.")

    best_box = None
    best_score = -1.0
    target_class = target_class.lower() if target_class else None

    for box_data in boxes:
        xyxy = box_data.xyxy[0].detach().cpu().numpy()
        conf = float(box_data.conf[0].detach().cpu().item())
        cls_id = int(box_data.cls[0].detach().cpu().item())
        cls_name = str(names.get(cls_id, cls_id)).lower()

        if target_class and cls_name != target_class:
            continue

        x1, y1, x2, y2 = xyxy
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        score = conf * np.sqrt(area)
        if score > best_score:
            best_score = score
            best_box = xyxy

    if best_box is None:
        raise RuntimeError(f"YOLO did not detect target class: {target_class}")

    return expand_box(best_box, image_rgb.shape, padding_ratio=padding_ratio)


def detect_mask_with_yolo_seg(
    image_rgb: np.ndarray,
    yolo_seg_model_path: str,
    target_class="person",
    min_confidence=0.25
) -> np.ndarray:
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(
            "YOLO-Seg needs ultralytics. Install it with: pip install ultralytics\n"
            f"Original error: {e}"
        )

    model = YOLO(yolo_seg_model_path)
    results = model.predict(source=image_rgb, conf=min_confidence, verbose=False)
    if not results:
        raise RuntimeError("YOLO-Seg did not return any result.")

    result = results[0]
    if result.masks is None or result.boxes is None:
        raise RuntimeError("YOLO-Seg model did not produce segmentation masks.")

    names = result.names
    masks = result.masks.data.detach().cpu().numpy()
    boxes = result.boxes
    h, w = image_rgb.shape[:2]

    best_mask = None
    best_score = -1.0
    target_class = target_class.lower() if target_class else None

    for idx, box_data in enumerate(boxes):
        conf = float(box_data.conf[0].detach().cpu().item())
        cls_id = int(box_data.cls[0].detach().cpu().item())
        cls_name = str(names.get(cls_id, cls_id)).lower()
        if target_class and cls_name != target_class:
            continue

        mask = masks[idx]
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
        binary = (mask > 0.5).astype(np.uint8)
        area = float(binary.sum())
        score = conf * np.sqrt(max(area, 1.0))
        if score > best_score:
            best_score = score
            best_mask = binary

    if best_mask is None:
        raise RuntimeError(f"YOLO-Seg did not detect target class: {target_class}")

    return morphological_clean(best_mask, kernel_size=5)


def refine_with_grabcut(
    image_rgb: np.ndarray,
    init_mask: np.ndarray,
    grabcut_iter=5,
    edge_map=None,
    max_area_ratio=1.35
) -> np.ndarray:
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    gc_mask = np.full(init_mask.shape, cv2.GC_PR_BGD, dtype=np.uint8)

    # Initial foreground.
    gc_mask[init_mask > 0] = cv2.GC_PR_FGD

    # High-confidence foreground.
    kernel = np.ones((7, 7), np.uint8)
    sure_fg = cv2.erode(init_mask.astype(np.uint8), kernel, iterations=1)
    gc_mask[sure_fg > 0] = cv2.GC_FGD

    # Set background around the bounding box.
    bbox = mask_bbox(init_mask)
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        h, w = init_mask.shape
        pad = 25
        xx1 = max(0, x1 - pad)
        yy1 = max(0, y1 - pad)
        xx2 = min(w - 1, x2 + pad)
        yy2 = min(h - 1, y2 + pad)

        bg_mask = np.ones_like(init_mask, dtype=np.uint8)
        bg_mask[yy1:yy2 + 1, xx1:xx2 + 1] = 0
        gc_mask[bg_mask > 0] = cv2.GC_BGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(
        image_bgr,
        gc_mask,
        None,
        bgd_model,
        fgd_model,
        grabcut_iter,
        cv2.GC_INIT_WITH_MASK
    )

    refined = np.where(
        (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
        1, 0
    ).astype(np.uint8)

    refined = morphological_clean(refined, kernel_size=5)

    # If the refined area is abnormal, fall back to the original SAM mask.
    init_area = int(init_mask.sum())
    ref_area = int(refined.sum())
    if ref_area == 0:
        return init_mask.copy()

    ratio = ref_area / max(init_area, 1)
    if ratio < 0.5 or ratio > max_area_ratio:
        return init_mask.copy()

    if edge_map is not None:
        init_edge_score = compute_edge_alignment_score(init_mask, edge_map)
        refined_edge_score = compute_edge_alignment_score(refined, edge_map)

        if init_edge_score > 0.01 and refined_edge_score < init_edge_score * 0.70:
            return init_mask.copy()

        if ratio > 1.20 and refined_edge_score < 0.02:
            return init_mask.copy()

    return refined


def compute_iou(pred: np.ndarray, gt: np.ndarray) -> float:
    inter = np.logical_and(pred > 0, gt > 0).sum()
    union = np.logical_or(pred > 0, gt > 0).sum()
    return float(inter / union) if union > 0 else 0.0


def compute_dice(pred: np.ndarray, gt: np.ndarray) -> float:
    inter = np.logical_and(pred > 0, gt > 0).sum()
    denom = (pred > 0).sum() + (gt > 0).sum()
    return float((2 * inter) / denom) if denom > 0 else 0.0


def overlay_mask(image_rgb: np.ndarray, mask: np.ndarray, color=(255, 0, 0), alpha=0.35) -> np.ndarray:
    out = image_rgb.copy().astype(np.float32)
    color_arr = np.array(color, dtype=np.float32)
    out[mask > 0] = out[mask > 0] * (1 - alpha) + color_arr * alpha
    return out.astype(np.uint8)


def save_visualizations(
    image_rgb,
    sam_mask,
    refined_mask,
    output_dir: Path,
    edge_map=None,
    input_box=None,
    positive_points=None,
    negative_points=None,
    initial_label="Initial Mask"
):
    output_dir.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(output_dir / "sam_mask.png"), (sam_mask * 255).astype(np.uint8))
    cv2.imwrite(str(output_dir / "refined_mask.png"), (refined_mask * 255).astype(np.uint8))
    if edge_map is not None:
        cv2.imwrite(str(output_dir / "edge_map.png"), (edge_map * 255).astype(np.uint8))

    overlay_sam = overlay_mask(image_rgb, sam_mask, color=(255, 0, 0))
    overlay_refined = overlay_mask(image_rgb, refined_mask, color=(0, 255, 0))

    original_vis = image_rgb.copy()
    if input_box is not None:
        x1, y1, x2, y2 = input_box.astype(int)
        original_vis = cv2.rectangle(original_vis, (x1, y1), (x2, y2), (255, 220, 0), 4)
    for point in positive_points or []:
        x, y = [int(round(v)) for v in point]
        cv2.circle(original_vis, (x, y), 18, (0, 255, 0), -1)
        cv2.circle(original_vis, (x, y), 24, (255, 255, 255), 3)
    for point in negative_points or []:
        x, y = [int(round(v)) for v in point]
        cv2.circle(original_vis, (x, y), 18, (255, 0, 0), -1)
        cv2.circle(original_vis, (x, y), 24, (255, 255, 255), 3)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].imshow(original_vis)
    axes[0].set_title("Original")
    axes[1].imshow(overlay_sam)
    axes[1].set_title(initial_label)
    axes[2].imshow(overlay_refined)
    axes[2].set_title("Refined Mask")

    for ax in axes:
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(output_dir / "overlay_comparison.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--model_type", type=str, default="vit_b", choices=["vit_b", "vit_l", "vit_h"])
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--output_dir", type=str, default="outputs_corrected")
    parser.add_argument("--gt_mask_path", type=str, default=None)

    parser.add_argument("--points_per_side", type=int, default=32)
    parser.add_argument("--grabcut_iter", type=int, default=5)
    parser.add_argument("--target_aspect", type=float, default=0.75)
    parser.add_argument("--kernel_size", type=int, default=5)

    parser.add_argument("--box", nargs=4, type=float, metavar=("X1", "Y1", "X2", "Y2"), default=None)
    parser.add_argument("--pos_point", nargs=2, type=float, action="append", metavar=("X", "Y"), default=None)
    parser.add_argument("--neg_point", nargs=2, type=float, action="append", metavar=("X", "Y"), default=None)
    parser.add_argument("--yolo_model", type=str, default=None)
    parser.add_argument("--yolo_seg_model", type=str, default=None)
    parser.add_argument("--target_class", type=str, default="person")
    parser.add_argument("--min_confidence", type=float, default=0.25)
    parser.add_argument("--box_padding", type=float, default=0.05)

    parser.add_argument("--canny_low", type=int, default=60)
    parser.add_argument("--canny_high", type=int, default=150)
    parser.add_argument("--edge_refine", action="store_true")
    parser.add_argument("--edge_refine_kernel", type=int, default=3)
    parser.add_argument("--skip_grabcut", action="store_true")
    parser.add_argument("--max_refine_area_ratio", type=float, default=1.35)

    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)

    image_rgb = load_image_rgb(args.image_path)
    image_for_sam = preprocess_for_sam(image_rgb)
    edge_map = build_edge_map(image_rgb, canny_low=args.canny_low, canny_high=args.canny_high)

    input_box = None
    box_source = "none"
    mask_source = "sam_auto"
    if args.box is not None:
        input_box = clamp_box(args.box, image_rgb.shape)
        box_source = "manual"
    elif args.yolo_model is not None and args.yolo_seg_model is None:
        input_box = detect_box_with_yolo(
            image_rgb=image_rgb,
            yolo_model_path=args.yolo_model,
            target_class=args.target_class,
            min_confidence=args.min_confidence,
            padding_ratio=args.box_padding
        )
        box_source = "yolo"

    positive_points = args.pos_point or []
    negative_points = args.neg_point or []
    has_prompt = input_box is not None or positive_points or negative_points

    if args.yolo_seg_model is not None:
        sam_mask = detect_mask_with_yolo_seg(
            image_rgb=image_rgb,
            yolo_seg_model_path=args.yolo_seg_model,
            target_class=args.target_class,
            min_confidence=args.min_confidence
        )
        mask_source = "yolo_seg"
        bbox = mask_bbox(sam_mask)
        if bbox is not None:
            input_box = np.array(bbox, dtype=np.float32)
            box_source = "yolo_seg_mask"
    else:
        sam = build_sam(args.model_type, args.checkpoint, args.device)

    if args.yolo_seg_model is None and has_prompt:
        mask_source = "sam_prompt"
        sam_mask = get_best_mask_from_prompt(
            image_rgb=image_for_sam,
            sam=sam,
            box=input_box,
            positive_points=positive_points,
            negative_points=negative_points,
            edge_map=edge_map,
            morph_kernel=args.kernel_size
        )
    elif args.yolo_seg_model is None:
        mask_source = "sam_auto"
        sam_mask = get_best_mask_from_sam(
            image_rgb=image_for_sam,
            sam=sam,
            points_per_side=args.points_per_side,
            target_aspect=args.target_aspect,
            edge_map=edge_map,
            morph_kernel=args.kernel_size
        )

    if args.edge_refine:
        sam_mask = refine_with_edge_candidates(
            sam_mask,
            edge_map,
            kernel_size=args.edge_refine_kernel
        )

    if args.skip_grabcut:
        refined_mask = sam_mask.copy()
    else:
        refined_mask = refine_with_grabcut(
            image_rgb=image_rgb,
            init_mask=sam_mask,
            grabcut_iter=args.grabcut_iter,
            edge_map=edge_map,
            max_area_ratio=args.max_refine_area_ratio
        )

    save_visualizations(
        image_rgb,
        sam_mask,
        refined_mask,
        output_dir,
        edge_map=edge_map,
        input_box=input_box,
        positive_points=positive_points,
        negative_points=negative_points,
        initial_label="Initial Mask" if mask_source == "yolo_seg" else "SAM Mask"
    )

    report_lines = []
    report_lines.append("=== SAM Boundary Refinement Report ===")
    report_lines.append(f"Image: {args.image_path}")
    report_lines.append(f"Image size: {image_rgb.shape[1]} x {image_rgb.shape[0]}")
    report_lines.append(f"Model type: {args.model_type}")
    report_lines.append(f"Device: {args.device}")
    report_lines.append(f"Mask source: {mask_source}")
    report_lines.append(f"Box source: {box_source}")
    if input_box is not None:
        report_lines.append(f"Input box: {[int(v) for v in input_box.tolist()]}")
    if positive_points:
        report_lines.append(f"Positive points: {[[int(v) for v in p] for p in positive_points]}")
    if negative_points:
        report_lines.append(f"Negative points: {[[int(v) for v in p] for p in negative_points]}")
    if args.yolo_model is not None:
        report_lines.append(f"YOLO model: {args.yolo_model}")
        report_lines.append(f"Target class: {args.target_class}")
        report_lines.append(f"Min confidence: {args.min_confidence}")
        report_lines.append(f"Box padding: {args.box_padding}")
    if args.yolo_seg_model is not None:
        report_lines.append(f"YOLO-Seg model: {args.yolo_seg_model}")
    report_lines.append(f"points_per_side: {args.points_per_side}")
    report_lines.append(f"grabcut_iter: {args.grabcut_iter}")
    report_lines.append(f"edge_refine: {args.edge_refine}")
    report_lines.append(f"edge_refine_kernel: {args.edge_refine_kernel}")
    report_lines.append(f"skip_grabcut: {args.skip_grabcut}")
    report_lines.append(f"max_refine_area_ratio: {args.max_refine_area_ratio}")
    report_lines.append(f"target_aspect: {args.target_aspect}")
    report_lines.append(f"kernel_size: {args.kernel_size}")
    report_lines.append(f"canny_low: {args.canny_low}")
    report_lines.append(f"canny_high: {args.canny_high}")
    report_lines.append(f"SAM foreground pixels: {int(sam_mask.sum())}")
    report_lines.append(f"Refined foreground pixels: {int(refined_mask.sum())}")
    report_lines.append(f"SAM edge alignment: {compute_edge_alignment_score(sam_mask, edge_map):.4f}")
    report_lines.append(f"Refined edge alignment: {compute_edge_alignment_score(refined_mask, edge_map):.4f}")

    if args.gt_mask_path is not None:
        gt = cv2.imread(args.gt_mask_path, cv2.IMREAD_GRAYSCALE)
        if gt is None:
            raise FileNotFoundError(f"Cannot read mask: {args.gt_mask_path}")
        if gt.shape != sam_mask.shape:
            gt = cv2.resize(gt, (sam_mask.shape[1], sam_mask.shape[0]), interpolation=cv2.INTER_NEAREST)
        gt = (gt > 127).astype(np.uint8)

        sam_iou = compute_iou(sam_mask, gt)
        sam_dice = compute_dice(sam_mask, gt)
        ref_iou = compute_iou(refined_mask, gt)
        ref_dice = compute_dice(refined_mask, gt)

        report_lines.append("")
        report_lines.append("With Ground Truth:")
        report_lines.append(f"SAM IoU: {sam_iou:.4f}")
        report_lines.append(f"SAM Dice: {sam_dice:.4f}")
        report_lines.append(f"Refined IoU: {ref_iou:.4f}")
        report_lines.append(f"Refined Dice: {ref_dice:.4f}")

    report_path = output_dir / "metrics.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n".join(report_lines))
    print(f"\nSaved outputs to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
