# 支持用學術論文重點與使用標註

專題標題：

**Multi-Model Boundary Refinement for Person Segmentation**

這份文件的用途是幫助你在期末報告中說清楚：每一篇論文支持了專題的哪一個部分，而不是只把論文列在 references。

## 使用方式總覽

| 論文 | 支持專題中的哪一段 | 使用強度 |
|---|---|---|
| Kirillov et al. (2023), Segment Anything | SAM 作為主要 segmentation backbone | 必引用 |
| Terven & Cordova-Esparza (2023), YOLO Review | YOLO 作為 person localization 模組 | 建議引用 |
| Gaus et al. (2024), SAM Variational Prompting | 使用 bounding box prompt 的合理性 | 建議引用 |
| Mazurowski et al. (2023), SAM Medical Image Analysis | SAM prompt 類型會影響結果，box prompt 較穩 | 輔助引用 |
| Rother et al. (2004), GrabCut | GrabCut 作為 foreground refinement | 必引用 |
| Canny (1986), Edge Detection | Canny edge map 作為邊界評估與輔助資訊 | 必引用 |

---

## 1. Kirillov et al. (2023) - Segment Anything

**論文完整名稱**

*Segment Anything*

**論文重點**

這篇是 SAM 的原始論文。它提出 Segment Anything Model，目標是做一個可以被 prompt 控制的通用影像分割模型。SAM 可以使用 bounding box、point、mask 等提示來產生 segmentation mask，並且具備 zero-shot transfer 能力，也就是不一定要針對每個新任務重新訓練模型。

**本專題使用到的部分**

本專題把 SAM 當作主要的人物遮罩產生模型。也就是說，YOLO 先找人，再把 YOLO box 當作 prompt 給 SAM，讓 SAM 產生人物 mask。

**對應到專題流程**

```text
Input Image -> YOLO Detection -> SAM Mask Generation
```

**可以放在報告的位置**

- Related Work：介紹 SAM 是什麼。
- Methodology：說明為什麼選 SAM 當 segmentation module。
- System Design：說明 SAM 是 promptable segmentation model。

**英文報告可用句**

> SAM is used as the main segmentation backbone because it supports promptable mask generation and can produce object masks from prompts such as bounding boxes or points.

**使用這篇時要避免的誤用**

不要寫成「SAM 一定可以在所有資料上產生最佳分割結果」。比較正確的說法是：SAM 是一個強大的 promptable segmentation backbone，但實際效果仍受 prompt quality 和影像內容影響。

**Link**

https://openaccess.thecvf.com/content/ICCV2023/html/Kirillov_Segment_Anything_ICCV_2023_paper.html

---

## 2. Terven & Cordova-Esparza (2023) - YOLO Architecture Review

**論文完整名稱**

*A Comprehensive Review of YOLO Architectures in Computer Vision: From YOLOv1 to YOLOv8 and YOLO-NAS*

**論文重點**

這篇是 YOLO 系列架構的綜述論文，說明 YOLO 從早期版本到 YOLOv8 的發展。它的重點是 YOLO 系列在 real-time object detection 中被廣泛使用，並且適合用來快速定位影像中的物件。

**本專題使用到的部分**

本專題不是拿 YOLO 直接做最後分割，而是用 YOLO 做 person localization。YOLO 的 bounding box 用來縮小 SAM 的搜尋範圍，減少 SAM 自動選錯區域的問題。

**對應到專題流程**

```text
Input Image -> YOLO detects person bounding box -> box prompt for SAM
```

**可以放在報告的位置**

- Related Work：介紹 YOLO 是即時物件偵測方法。
- Methodology：說明為什麼加入 YOLO detection。
- Experiment Versions：說明 v5 / v6 是 YOLO-guided SAM。

**英文報告可用句**

> YOLO is adopted as the localization module because YOLO-based detectors are widely used for real-time object detection and can provide bounding boxes for the target person.

**使用這篇時要避免的誤用**

不要寫成「YOLO 提高了分割精度」。YOLO 本身在本專題中主要負責 detection，不是最後的 mask refinement。比較正確的說法是：YOLO improves target localization, which helps SAM receive a clearer prompt.

**Link**

https://arxiv.org/abs/2304.00501

---

## 3. Gaus et al. (2024) - SAM with Variational Prompting

**論文完整名稱**

*Performance Evaluation of Segment Anything Model with Variational Prompting for Application to Non-Visible Spectrum Imagery*

**論文重點**

這篇論文評估 SAM 在不同 prompt 類型下的表現，例如 bounding box、centroid point、random point。它的重點是 SAM 的結果會受到 prompt 類型影響，bounding box prompt 在部分情況下能提供較好的 segmentation result。

**本專題使用到的部分**

本專題使用 YOLO 產生 bounding box，再把 bounding box 當作 SAM 的 prompt。這篇論文可以支持「box prompt 是合理的 prompt strategy」，也支持「prompt quality 會影響 SAM 結果」這個說法。

**對應到專題流程**

```text
YOLO person box -> SAM box prompt -> person mask
```

**可以放在報告的位置**

- Related Work：SAM prompt strategy。
- Methodology：說明為什麼不用完全自動 SAM，而加入 YOLO box。
- Discussion：解釋為什麼 prompt 設計會影響結果。

**英文報告可用句**

> Since SAM performance depends on the type and quality of the prompt, this project uses YOLO-generated bounding boxes as automatic box prompts to reduce target ambiguity.

**使用這篇時要避免的誤用**

這篇不是人物分割專用論文，也不是 YOLO + SAM 的完整 pipeline 論文。因此不要寫成「這篇證明 YOLO + SAM 一定最好」。應該寫成：它支持 prompt type matters, and box prompts can be effective.

**Link**

https://arxiv.org/abs/2404.12285

---

## 4. Mazurowski et al. (2023) - SAM for Medical Image Analysis

**論文完整名稱**

*Segment Anything Model for Medical Image Analysis: An Experimental Study*

**論文重點**

這篇論文在多個醫學影像資料集上測試 SAM，並比較不同 prompt 方式。它的重要觀察是 SAM 的表現會依資料集與任務而變化，而且 box prompts 通常比 point prompts 更穩定。

**本專題使用到的部分**

本專題可以引用這篇作為輔助證據，說明 SAM 不是「丟進圖片就一定完美」，而是需要好的 prompt。這支持本專題加入 YOLO box guidance 的設計。

**對應到專題流程**

```text
Avoid pure automatic SAM -> add YOLO box prompt -> reduce prompt ambiguity
```

**可以放在報告的位置**

- Related Work：SAM 在不同 domain 的表現差異。
- Methodology：說明本專題使用 box prompt 的原因。
- Limitation：說明 SAM 結果仍可能受影像內容與 prompt 影響。

**英文報告可用句**

> Previous evaluations of SAM show that segmentation performance can vary across tasks and that less ambiguous prompts, especially box prompts, can improve the quality of the generated masks.

**使用這篇時要避免的誤用**

這篇是醫學影像，不是一般人物照片。因此不要把它當作直接證明人物分割結果的論文。它比較適合當作「SAM prompt 設計重要」的輔助引用。

**Link**

https://arxiv.org/abs/2304.10517

---

## 5. Rother et al. (2004) - GrabCut

**論文完整名稱**

*GrabCut: Interactive Foreground Extraction Using Iterated Graph Cuts*

**論文重點**

這篇論文提出 GrabCut，用 graph cut 的方式做前景與背景分離。它結合區域資訊與邊界資訊，適合用在 foreground extraction 和 object boundary cleanup。

**本專題使用到的部分**

本專題使用 GrabCut 作為 mask refinement 的後處理步驟。SAM 或 YOLO-Seg 產生初始 mask 後，GrabCut 用來嘗試清理背景雜訊並改善前景邊界。

**對應到專題流程**

```text
Initial mask -> GrabCut refinement -> refined mask
```

**可以放在報告的位置**

- Related Work：介紹傳統 foreground extraction。
- Methodology：說明 GrabCut refinement step。
- Experiment Versions：說明 v1、v2、v5、v6、v8 有使用 GrabCut。

**英文報告可用句**

> GrabCut is used as a lightweight post-processing step to refine the initial segmentation mask by improving foreground-background separation.

**使用這篇時要避免的誤用**

不要寫成 GrabCut 是 deep learning 模型。它是傳統影像處理 / graph-cut 方法。也不要說 GrabCut 一定能修好所有錯誤；它主要適合修前景背景邊界，但如果初始 mask 很差，效果也會有限。

**Link**

https://research-explorer.ista.ac.at/record/3179

---

## 6. Canny (1986) - Edge Detection

**論文完整名稱**

*A Computational Approach to Edge Detection*

**論文重點**

這篇是 Canny edge detector 的經典論文。它提出一套用來偵測影像邊緣的方法，目標是保留影像中重要的結構資訊，例如物體邊界。

**本專題使用到的部分**

本專題使用 Canny edge map 作為邊界檢查與量化評估的基礎。因為目前沒有人工標註 ground-truth mask，所以使用 edge alignment 作為 preliminary metric，檢查模型邊界是否接近影像中的可見邊緣。

**對應到專題流程**

```text
Image -> Canny edge map -> compare mask boundary with edge map -> edge alignment score
```

**可以放在報告的位置**

- Methodology：說明 edge map 怎麼產生。
- Evaluation Metric：說明 edge alignment 的基礎。
- Limitation：說明 edge alignment 只是 proxy metric，不等於 IoU 或 Dice。

**英文報告可用句**

> Canny edge detection is used to generate an edge map, which provides a preliminary signal for evaluating whether the predicted mask boundary follows visible image edges.

**使用這篇時要避免的誤用**

不要把 edge alignment 寫成正式 segmentation accuracy。Canny 只能提供影像邊緣資訊，不能取代人工標註的 ground truth。報告中應該明確說明 IoU 和 Dice 需要 ground-truth masks。

**Link**

https://www.cs.princeton.edu/courses/archive/fall13/cos429/papers/Canny86.pdf

---

## 7. Ultralytics YOLOv8 Documentation - Implementation Reference

**文件性質**

這不是學術論文，而是實作文件。

**文件重點**

Ultralytics YOLOv8 文件說明 YOLOv8 支援 object detection 和 instance segmentation，並列出 detection model 與 segmentation model，例如 `yolov8n.pt` 和 `yolov8n-seg.pt`。

**本專題使用到的部分**

本專題實際使用：

- `yolov8n.pt`：person detection / bounding box。
- `yolov8n-seg.pt`：YOLO-Seg direct mask comparison。

**可以放在報告的位置**

- Implementation Details
- Experimental Setup

**英文報告可用句**

> In implementation, `yolov8n.pt` is used for person detection and `yolov8n-seg.pt` is used as the YOLO-Seg comparison model.

**使用這份文件時要避免的誤用**

不要把它放在「Academic Related Work」當主要論文引用。它適合放在 implementation reference 或 footnote。

**Link**

https://docs.ultralytics.com/models/yolov8/

---

## 建議在報告中怎麼安排引用

### Related Work

可以放：

- SAM 原始論文
- YOLO review
- SAM prompt evaluation papers
- GrabCut
- Canny

### Methodology

可以對應：

- SAM：segmentation backbone
- YOLO：person localization
- Canny：edge map and boundary score
- GrabCut：mask refinement

### Experimental Setup

可以寫：

- v1：SAM auto + Canny + GrabCut
- v6：YOLO detection + SAM + Canny + edge refinement + GrabCut
- v7 / v8：YOLO-Seg direct mask and YOLO-Seg + GrabCut comparison

### Discussion / Limitation

一定要寫：

- Current result is preliminary.
- Edge alignment is only a proxy metric.
- Ground-truth masks are needed for IoU and Dice.
- The dataset is still small.

## 最安全的總結句

> The reviewed literature supports the design of a hybrid segmentation pipeline: YOLO is used for target localization, SAM is used for promptable mask generation, Canny edge detection is used for boundary-based evaluation, and GrabCut is used for foreground refinement. The current results should be interpreted as preliminary because ground-truth masks are not yet available.
