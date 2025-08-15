from flask import Flask, request, jsonify
import requests
import fitz  # PyMuPDF
import io
import re
from dateutil import parser

app = Flask(__name__)

def extract_text(pdf_bytes):
    doc = fitz.open("pdf", pdf_bytes)
    return "\n".join([page.get_text() for page in doc])

@app.route('/extract', methods=['POST'])
def extract():
    try:
        pdf_url = request.json.get('pdf_url')
        if not pdf_url:
            return jsonify({"error": "No PDF URL provided"}), 400

        pdf_data = requests.get(pdf_url).content
        text = extract_text(io.BytesIO(pdf_data))

       # --- Extract Company ---
        company = "Unknown"

        # First try: About company section
        about_match = re.search(r'About company\s*(.*?)\n', text, re.IGNORECASE)
        if about_match:
            line = about_match.group(1).strip()
            name_match = re.search(r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,4})', line)
            if name_match:
                company = name_match.group(1).strip()
            else:
                company = line
        else:
            # Fallback: match "XYZ will be conducting"
            conducting_match = re.search(r'([A-Za-z\- ]{2,100})\s+will be conducting', text, re.IGNORECASE)
            if conducting_match:
                raw_line = conducting_match.group(1).strip()

                 # Clean and extract last few capitalized words (like "SMS Magic")
                name_match = re.search(r'([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+){0,3})$', raw_line)
                if name_match:
                    company = name_match.group(1).strip()
                else:
                    company = raw_line


        # --- Extract Role ---
        role = "Unknown"
        role_match = re.search(r'Profile Offered\s*:\s*(.*?)\n', text, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip()
        else:
            jd_match = re.search(r'Job Description\s*(.*?)\n', text, re.IGNORECASE)
            if jd_match:
                role = jd_match.group(1).strip()

        # --- Extract Deadline ---
        deadline = "Not Found"
        deadline_match = re.search(
            r'APPLY\s*(?:on or before|by)\s*([0-9]{1,2}(?:st|nd|rd|th)?\s*(January|February|March|April|May|June|July|August|September|October|November|December)[’\']?\s*[0-9]{4})',
            text,
            re.IGNORECASE
        )
        if deadline_match:
            deadline_text = deadline_match.group(1)
            deadline_text = re.sub(r'(st|nd|rd|th)', '', deadline_text)
            deadline_text = re.sub(r'[’\']', '', deadline_text)
            try:
                deadline = parser.parse(deadline_text, fuzzy=True).strftime("%Y-%m-%d")
            except:
                pass
        else:
            # Fallback to "Deadline" or "Last date"
            fallback_match = re.search(
                r'(Deadline|Last date)[:\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?\s*(January|February|March|April|May|June|July|August|September|October|November|December)[’\']?\s*[0-9]{4})',
                text,
                re.IGNORECASE
            )
            if fallback_match:
                try:
                    deadline_text = fallback_match.group(2)
                    deadline_text = re.sub(r'(st|nd|rd|th)', '', deadline_text)
                    deadline_text = re.sub(r'[’\']', '', deadline_text)
                    deadline = parser.parse(deadline_text, fuzzy=True).strftime("%Y-%m-%d")
                except:
                    pass

        return jsonify({
            "company": company,
            "role": role,
            "deadline": deadline
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000)
