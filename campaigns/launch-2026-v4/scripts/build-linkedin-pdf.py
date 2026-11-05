from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

CAMPAIGN = Path(__file__).resolve().parents[1]
SLIDES = CAMPAIGN / "exports" / "linkedin-product-overview"
OUTPUT = SLIDES / "examuploadkit-linkedin-product-journey.pdf"

files = sorted(SLIDES.glob("*.png"))
if len(files) != 8:
    raise RuntimeError(f"Expected 8 LinkedIn slides, found {len(files)}")

page_width, page_height = 1200, 1500
pdf = canvas.Canvas(str(OUTPUT), pagesize=(page_width, page_height), pageCompression=1)
pdf.setTitle("ExamUploadKit: from exam rules to ready files")
pdf.setAuthor("ExamUploadKit")
pdf.setSubject("A concise product journey for exam-specific upload preparation")
for file in files:
    pdf.drawImage(ImageReader(str(file)), 0, 0, page_width, page_height, preserveAspectRatio=False, mask="auto")
    pdf.showPage()
pdf.save()
print(OUTPUT)
