import os
import io
import datetime
from flask import Flask, request, send_file, render_template
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for uploads (optional)

def flatten_pdf(input_stream):
    """
    Flatten the input PDF (given as a BytesIO stream)
    and return a BytesIO object containing the flattened PDF.
    """
    input_stream.seek(0)
    reader = PdfReader(input_stream)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream

def sign_pdf(pdf_stream, signature_path):
    """
    Add a signature and date to all pages of the PDF (in-memory).
    Returns a BytesIO object of the signed PDF.
    """
    # Flatten first
    flattened_stream = flatten_pdf(pdf_stream)

    reader = PdfReader(flattened_stream)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        # Create a temporary PDF in-memory for the signature
        temp_buffer = io.BytesIO()
        c = canvas.Canvas(temp_buffer, pagesize=letter)

        # Adjust these coordinates for your signature & date placement
        c.drawImage(signature_path, -160, -90, width=600, height=300, mask="auto")
        c.drawString(240, 50, str(datetime.date.today()))
        c.save()

        temp_buffer.seek(0)
        sig_reader = PdfReader(temp_buffer)
        page.merge_page(sig_reader.pages[0])
        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream

@app.route('/')
def index():
    # This will render templates/index.html
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # The uploaded PDF is in the form field named 'pdfFile'
    file = request.files.get('pdfFile')
    if not file:
        return "No PDF file uploaded.", 400

    # Path to your signature image in the 'static' folder
    signature_path = os.path.join(app.root_path, 'static', 'signature.png')
    if not os.path.exists(signature_path):
        return "Signature file not found on the server.", 500

    # Convert the uploaded PDF into an in-memory stream
    pdf_stream = io.BytesIO(file.read())

    # Sign the PDF
    signed_pdf_stream = sign_pdf(pdf_stream, signature_path)

    # Return the signed PDF as an attachment (trigger download)
    return send_file(
        signed_pdf_stream,
        as_attachment=True,
        download_name='signed_output.pdf',
        mimetype='application/pdf'
    )

# Replit often expects you to write this check, or set the 'Run' command in the .replit config
if __name__ == '__main__':
    # For local debugging, app.run(debug=True), but Replit may prefer a different approach.
    app.run(host='0.0.0.0', port=81, debug=True)
