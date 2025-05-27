from flask import Flask, render_template, request, jsonify, send_file ,url_for, current_app
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from werkzeug.utils import secure_filename
from datetime import timedelta
import os

app = Flask(__name__)



@app.route("/",methods=["GET","POST"])
def index():
    return render_template("index.html")
# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}

# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS




@app.route("/rotate-pdf", methods=["POST"])
def rotate_pdf():
    rotation = request.form.get("rotation", type=int)
    starting_date = request.form.get("date")
    files = request.files.getlist("files")
    print("starting date",starting_date)
    if not rotation or not starting_date or not files:
        return jsonify({"error": "Missing rotation, date, or files"}), 400

    try:
        starting_date = datetime.strptime(starting_date, "%m/%d/%Y")

        daycount = starting_date.isoweekday()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use MM/DD/YYYY."}), 400

    Days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    output_files = []

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            try:
                reader = PdfReader(file)
                writer = PdfWriter()

                for page in reader.pages:
                    page.rotate(rotation)
                    writer.add_page(page)

                # Safe filename format
                output_filename = f"{starting_date.strftime('%B')}-{starting_date.day}-{starting_date.year}-{Days[daycount-1]}.pdf"
                output_filename = secure_filename(output_filename)  # Ensure filename safety
                output_path = os.path.join("output", output_filename)

                os.makedirs("output", exist_ok=True)
                with open(output_path, "wb") as pdf_out:
                    writer.write(pdf_out)

                # Ensure URL generation works inside request context
                with current_app.app_context():
                    output_files.append({
                        "filename": output_filename,
                        "file_path": output_path,
                        "download_url": url_for('download_file', filename=output_filename, _external=True)
                    })

                starting_date += timedelta(days=1)
                daycount = starting_date.isoweekday() 

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                return jsonify({"error": f"Error processing {filename}: {str(e)}"}), 500

    if not output_files:
        return jsonify({"error": "No valid PDFs processed."}), 400

    return jsonify({"processed_pdfs": output_files}),200


@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join("output", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


if __name__  in "__main__":
    app.run()