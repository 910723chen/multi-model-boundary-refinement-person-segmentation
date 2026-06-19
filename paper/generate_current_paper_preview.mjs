import fs from "fs";

const finalPath = "paper/Final_Project_Paper.pdf";
const previewPath = "paper/Current_Paper_Preview.pdf";

if (!fs.existsSync(finalPath)) {
  throw new Error(`Missing final paper PDF: ${finalPath}`);
}

fs.copyFileSync(finalPath, previewPath);
console.log(`Copied ${finalPath} to ${previewPath}`);
