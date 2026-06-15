import fs from "fs";

const outputPath = "paper/Current_Paper_Preview.pdf";

const lines = [
  "Multi-Model Boundary Refinement for Person Segmentation",
  "",
  "Current Paper Preview",
  "",
  "This PDF is a lightweight preview generated from the latest strict paper content.",
  "The official editable paper source is paper/IEEE_Final_Project_Paper.tex.",
  "",
  "Abstract",
  "Person segmentation is useful in image editing, human-centered vision, and background removal tasks, but final mask boundaries are often unstable around hair, clothing, shadows, and complex backgrounds. This project studies a practical multi-model pipeline for improving person boundary segmentation without training a new neural network. The workflow combines YOLO-based person localization, SAM-based mask generation, Canny edge detection, edge-based morphological refinement, and GrabCut foreground refinement.",
  "",
  "Method Summary",
  "Baseline v1: automatic SAM mask generation with Canny edge scoring and GrabCut.",
  "Proposed v6: YOLO person detection creates an automatic SAM box prompt. The resulting mask is refined by Canny-guided edge refinement and GrabCut.",
  "",
  "Experimental Setup",
  "The formal test set contains 12 selected person images from 34 uploaded photos. Six automatic versions were batch-tested. Manual box or point prompt versions were prepared but skipped in the formal batch because manual prompt annotations were not included.",
  "",
  "Main Quantitative Result",
  "v1 SAM auto + Canny score + GrabCut: mean edge alignment = 0.8708.",
  "v6 YOLO detection + SAM + Canny + edge refine + GrabCut: mean edge alignment = 0.8855.",
  "Absolute improvement over v1: 0.0147. Relative improvement: about 1.7 percent.",
  "",
  "Interpretation",
  "The result supports a modest preliminary improvement in edge alignment. YOLO helps reduce target ambiguity by providing an automatic person box prompt for SAM. Edge refinement and GrabCut improve boundary stability in the selected test set.",
  "",
  "Strict Limitations",
  "This project does not report IoU or Dice score because manually annotated ground-truth masks are not included. Edge alignment is a proxy metric and should not be interpreted as complete segmentation accuracy. The dataset is small, so the result should not be claimed as a universal improvement over SAM, YOLO-Seg, or supervised segmentation models.",
  "",
  "References Used",
  "[1] Segment Anything, ICCV 2023.",
  "[2] A Comprehensive Review of YOLO Architectures in Computer Vision, 2023.",
  "[3] SAM prompt evaluation studies.",
  "[4] Canny edge detection.",
  "[5] GrabCut foreground extraction.",
];

function escapePdfText(text) {
  return text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function wrapLine(line, maxChars = 92) {
  if (line.length <= maxChars) {
    return [line];
  }
  const words = line.split(/\s+/);
  const wrapped = [];
  let current = "";
  for (const word of words) {
    if ((current + " " + word).trim().length > maxChars) {
      if (current) {
        wrapped.push(current);
      }
      current = word;
    } else {
      current = (current + " " + word).trim();
    }
  }
  if (current) {
    wrapped.push(current);
  }
  return wrapped;
}

const pageWidth = 612;
const pageHeight = 792;
const marginX = 54;
const startY = 740;
const lineHeight = 14;
const bottomY = 60;
const pages = [];
let currentPage = [];
let y = startY;

for (const line of lines) {
  const wrapped = line === "" ? [""] : wrapLine(line);
  for (const part of wrapped) {
    if (y < bottomY) {
      pages.push(currentPage);
      currentPage = [];
      y = startY;
    }
    currentPage.push({ text: part, y });
    y -= lineHeight;
  }
}
if (currentPage.length > 0) {
  pages.push(currentPage);
}

const objects = [];
function addObject(body) {
  objects.push(body);
  return objects.length;
}

const fontObj = addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
const pageRefs = [];
const contentRefs = [];

for (const pageLines of pages) {
  const commands = ["BT", "/F1 10 Tf", "14 TL"];
  for (const item of pageLines) {
    const size = item.y === startY && item.text.includes("Multi-Model") ? 16 : 10;
    commands.push(`/F1 ${size} Tf`);
    commands.push(`1 0 0 1 ${marginX} ${item.y} Tm`);
    commands.push(`(${escapePdfText(item.text)}) Tj`);
  }
  commands.push("ET");
  const stream = commands.join("\n");
  const contentObj = addObject(`<< /Length ${Buffer.byteLength(stream, "utf8")} >>\nstream\n${stream}\nendstream`);
  contentRefs.push(contentObj);
}

const pagesObjPlaceholder = objects.length + pages.length + 1;
for (const contentRef of contentRefs) {
  const pageObj = addObject(`<< /Type /Page /Parent ${pagesObjPlaceholder} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 ${fontObj} 0 R >> >> /Contents ${contentRef} 0 R >>`);
  pageRefs.push(pageObj);
}

const pagesObj = addObject(`<< /Type /Pages /Kids [${pageRefs.map((ref) => `${ref} 0 R`).join(" ")}] /Count ${pageRefs.length} >>`);
const catalogObj = addObject(`<< /Type /Catalog /Pages ${pagesObj} 0 R >>`);

let pdf = "%PDF-1.4\n";
const offsets = [0];
for (let i = 0; i < objects.length; i++) {
  offsets.push(Buffer.byteLength(pdf, "utf8"));
  pdf += `${i + 1} 0 obj\n${objects[i]}\nendobj\n`;
}
const xrefOffset = Buffer.byteLength(pdf, "utf8");
pdf += `xref\n0 ${objects.length + 1}\n`;
pdf += "0000000000 65535 f \n";
for (let i = 1; i < offsets.length; i++) {
  pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
}
pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogObj} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;

fs.writeFileSync(outputPath, Buffer.from(pdf, "utf8"));
console.log(`Wrote ${outputPath}`);
