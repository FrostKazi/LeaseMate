from flask import Flask, request, jsonify, render_template
import os
import fitz 
import docx
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACTED_FOLDER = os.path.join(BASE_DIR, 'extracted')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

# Ensure directories exist
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index_v3.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'contract_file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
        
    file = request.files['contract_file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    extracted_text = ""

    try:
        # --- Handle PDF Files ---
        if ext == '.pdf':
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n"
                
        # --- Handle DOCX Files ---
        elif ext == '.docx':
            doc = docx.Document(file)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
                
        else:
            return jsonify({'error': 'Invalid file type. Please upload a PDF or DOCX.'}), 400
        
        # --- Save the Extracted Text ---
        base_name = os.path.splitext(filename)[0]
        txt_filename = f"{base_name}_extracted.txt"
        txt_filepath = os.path.join(EXTRACTED_FOLDER, txt_filename)
        
        context_block = request.form.get('context_block', '')
        full_text = (context_block + extracted_text.strip()) if context_block else extracted_text.strip()
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(full_text)
            

        # Success — frontend will now poll /get-results
        return jsonify({'message': 'File successfully processed and text saved!'}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

@app.route('/get-results')
def get_results():
    result_path = os.path.join(OUTPUT_FOLDER, 'results.json')

    if not os.path.exists(result_path):
        return jsonify({'error': 'results.json not found in output folder'}), 404

    # Serve results.json directly — polling only starts after a fresh upload
    # so stale-result risk is already mitigated by the frontend flow.

    with open(result_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)