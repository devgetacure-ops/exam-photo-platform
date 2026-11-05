from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[3]
SLIDES = Path(__file__).resolve().parents[1] / "exports" / "linkedin" / "product-overview"
OUTPUT = ROOT / "output" / "pdf" / "examuploadkit-linkedin-product-overview.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

files = sorted(SLIDES.glob("*.png"))
if len(files) != 11:
    raise RuntimeError(f"Expected 11 LinkedIn slides, found {len(files)}")

page_width, page_height = 1200, 1500
pdf = canvas.Canvas(str(OUTPUT), pagesize=(page_width, page_height), pageCompression=1)
pdf.setTitle("ExamUploadKit product overview")
pdf.setAuthor("ExamUploadKit")
pdf.setSubject("Exam-specific upload file preparation for Indian examinations")
for file in files:
    pdf.drawImage(ImageReader(str(file)), 0, 0, page_width, page_height, preserveAspectRatio=False, mask="auto")
    pdf.showPage()
pdf.save()
print(OUTPUT)
