from reportlab.pdfgen import canvas

inp = '/Users/simon/Documents/GitHub/dshsc_term3_python/app.py'  # input file
out = '/Users/simon/Documents/GitHub/dshsc_term3_python/app.pdf'  # output pdf file

# Create PDF canvas
pdf = canvas.Canvas(out)

with open(inp, 'r') as f:
    pdf.drawString(100, 800, f.read())

pdf.save()

print("PDF is Saved Successfully")