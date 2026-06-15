# Supporting Papers for the Final Report

Project title used for search:

**Multi-Model Boundary Refinement for Person Segmentation**

Search focus:

- "Segment Anything" and promptable segmentation
- "YOLOv8" and object detection / instance segmentation
- "SAM box prompt" and prompt strategy evaluation
- "GrabCut" foreground extraction
- "Canny" edge detection

## Recommended Core References

### 1. Segment Anything

**Citation**

Kirillov, A., Mintun, E., Ravi, N., Mao, H., Rolland, C., Gustafson, L., Xiao, T., Whitehead, S., Berg, A. C., Lo, W. Y., Dollar, P., & Girshick, R. (2023). *Segment Anything*. ICCV 2023.

**Why it supports this project**

This is the main reference for using SAM as the segmentation backbone. The paper introduces SAM as a promptable segmentation model that can transfer to new image distributions and tasks. This supports the project decision to use SAM without training a new segmentation model.

**Useful report sentence**

SAM is used as the main promptable segmentation module because it can generate masks from prompts such as boxes or points and can generalize to new segmentation tasks.

Link: https://openaccess.thecvf.com/content/ICCV2023/html/Kirillov_Segment_Anything_ICCV_2023_paper.html

### 2. A Comprehensive Review of YOLO Architectures in Computer Vision

**Citation**

Terven, J., & Cordova-Esparza, D. (2023). *A Comprehensive Review of YOLO Architectures in Computer Vision: From YOLOv1 to YOLOv8 and YOLO-NAS*. Machine Learning and Knowledge Extraction, 5, 1680-1716.

**Why it supports this project**

This paper supports the use of YOLO as the object localization module. The project uses YOLO to detect the person region before sending a bounding box prompt to SAM.

**Useful report sentence**

YOLO is selected as the localization module because YOLO-based models are widely used for real-time object detection and provide bounding boxes that can be converted into SAM prompts.

Link: https://arxiv.org/abs/2304.00501

### 3. Performance Evaluation of Segment Anything Model with Variational Prompting

**Citation**

Gaus, Y. F. A., Bhowmik, N., Isaac-Medina, B. K. S., & Breckon, T. P. (2024). *Performance Evaluation of Segment Anything Model with Variational Prompting for Application to Non-Visible Spectrum Imagery*. arXiv:2404.12285.

**Why it supports this project**

This paper directly supports the idea that prompt type matters for SAM. It compares prompt strategies such as bounding boxes, centroids, and random points, and reports that box prompts can provide strong segmentation results in some settings.

**Useful report sentence**

Because SAM performance depends on the prompt quality, this project uses YOLO-detected bounding boxes as automatic box prompts to reduce target ambiguity.

Link: https://arxiv.org/abs/2404.12285

### 4. Segment Anything Model for Medical Image Analysis: An Experimental Study

**Citation**

Mazurowski, M. A., Dong, H., Gu, H., Yang, J., Konz, N., & Zhang, Y. (2023). *Segment Anything Model for Medical Image Analysis: An Experimental Study*. Medical Image Analysis, 102918.

**Why it supports this project**

Although this paper is about medical images, it is useful because it evaluates SAM under different prompting modes and reports that box prompts are notably better than point prompts. This supports the project logic of using bounding boxes as guidance.

**Useful report sentence**

Prior SAM evaluation studies show that less ambiguous prompts, especially box prompts, can improve SAM segmentation performance, which motivates the YOLO-guided SAM design.

Link: https://arxiv.org/abs/2304.10517

### 5. GrabCut: Interactive Foreground Extraction Using Iterated Graph Cuts

**Citation**

Rother, C., Kolmogorov, V., & Blake, A. (2004). *GrabCut: Interactive Foreground Extraction Using Iterated Graph Cuts*. ACM SIGGRAPH, 23(3), 309-314.

**Why it supports this project**

GrabCut is used as the foreground refinement module. The paper supports the idea of combining color/texture information and edge/contrast information to improve foreground-background separation.

**Useful report sentence**

GrabCut is added as a lightweight refinement step because graph-cut foreground extraction can combine region and boundary information to improve object separation.

Link: https://research-explorer.ista.ac.at/record/3179

### 6. A Computational Approach to Edge Detection

**Citation**

Canny, J. (1986). *A Computational Approach to Edge Detection*. IEEE Transactions on Pattern Analysis and Machine Intelligence, PAMI-8(6), 679-698.

**Why it supports this project**

Canny edge detection is used for edge-map generation and boundary alignment scoring. It supports the idea that edge detection preserves useful structural information about object boundaries.

**Useful report sentence**

Canny edge detection is used as a boundary-based evaluation signal because it reduces image content while preserving structural boundary information.

Link: https://www.cs.princeton.edu/courses/archive/fall13/cos429/papers/Canny86.pdf

## Implementation Reference

### Ultralytics YOLOv8 Documentation

This is not a paper, but it is useful for explaining the actual YOLOv8 model files used in the project. The documentation confirms YOLOv8 support for detection models such as `yolov8n.pt` and segmentation models such as `yolov8n-seg.pt`.

Link: https://docs.ultralytics.com/models/yolov8/

## Recommended Paper Framing

The safest academic framing is:

> This project does not propose a new neural network architecture. Instead, it studies a practical multi-model pipeline that combines YOLO-based localization, SAM-based promptable segmentation, Canny edge-based boundary checking, and GrabCut-based foreground refinement for person boundary segmentation.

Recommended claim level:

> In the selected 12-image preliminary test set, YOLO-guided SAM with edge refinement and GrabCut achieved the highest mean edge alignment score among the tested versions.

Avoid overclaiming:

> Do not claim that this method is universally better than SAM, YOLO-Seg, or supervised segmentation models. The current experiment does not include ground-truth masks, IoU, or Dice scores yet.
