from flask import Flask, request, jsonify
import requests
import fitz
import io
import re
import os
import json
from dateutil import parser
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"✅ AI MODE ENABLED - Using Gemini API")
else:
    print("⚠️  No API key found - Using regex fallback mode")

def extract_text(pdf_bytes):
    """Extract text from PDF bytes"""
    doc = fitz.open("pdf", pdf_bytes)
    return "\n".join(page.get_text() for page in doc)

def extract_with_ai(text):
    """Use Gemini AI to extract company, role, and deadline from text"""
    try:
        if not GEMINI_API_KEY:
            print("⚠️  AI extraction skipped - no API key")
            return None
        
        print(f"🤖 Using AI to extract from {len(text)} characters of text...")
        
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        prompt = f"""
You are an expert at extracting structured information from recruitment documents. 
Analyze the following text extracted from a recruitment PDF and extract:
1. Company Name (the organization conducting recruitment)
2. Role/Position/Profile being offered
3. Application Deadline (convert to YYYY-MM-DD format)

Text to analyze:
{text[:4000]}

Respond ONLY with a valid JSON object in this exact format:
{{
  "company": "Company Name Here",
  "role": "Role/Position Here",
  "deadline": "YYYY-MM-DD"
}}

Rules:
- If you cannot find any field, use "Unknown" for company/role or "Not Found" for deadline
- For deadline, look for registration deadline, application deadline, or reporting date
- Extract the actual company name, not generic terms
- Be precise and concise
"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        print(f"📝 AI Response: {result_text}")
        
        # Remove markdown code blocks if present
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
        
        # Parse JSON response
        data = json.loads(result_text)
        
        result = {
            "company": data.get("company", "Unknown"),
            "role": data.get("role", "Unknown"),
            "deadline": data.get("deadline", "Not Found")
        }
        
        print(f"✅ AI Extracted: {result}")
        return result
    
    except Exception as e:
        print(f"❌ AI extraction error: {e}")
        return None

def extract_with_regex(text):
    """Fallback regex-based extraction with improved patterns"""
    
    # ---------------- COMPANY ----------------
    company = "Unknown"
    
    # Clean the text first - remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Multiple patterns to try (ordered by specificity)
    company_patterns = [
        # Pattern 1: "Company: XYZ" or "Organisation: XYZ"
        (r'(?:Company|Organisation|Organization)\s*[:\-]\s*([A-Z][A-Za-z0-9\&\.\-\s]{2,40})(?:\s+(?:will|is|has|Internship|Recruitment)|\n|$)', 1),
        
        # Pattern 2: "XYZ will be conducting" - capture only company name
        (r'\b([A-Z][A-Za-z][A-Za-z0-9\&\.\-\s]{1,35}?)\s+(?:will be conducting|is conducting|has announced)', 1),
        
        # Pattern 3: "XYZ Internship/Recruitment Drive"
        (r'\b([A-Z][A-Za-z][A-Za-z0-9\&\.\-\s]{1,35}?)\s+(?:Internship|Recruitment|Placement)\s+(?:cum\s+)?(?:PPO\s+)?(?:Drive|Program)', 1),
        
        # Pattern 4: At start of document (first capitalized phrase)
        (r'^([A-Z][A-Za-z0-9\&\.\-\s]{2,40})(?:\s+(?:Internship|Recruitment|Drive|will|is|has)|\n)', 1),
    ]
    
    for pattern, group_num in company_patterns:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            candidate = m.group(group_num).strip()
            
            # Clean up the candidate
            # Remove trailing conjunctions and common words
            candidate = re.sub(r'\s+(?:and|or|the|will|is|has|be|to|that|all|above|students)$', '', candidate, flags=re.IGNORECASE)
            
            # Remove phrases that indicate it's not a company name
            if any(phrase in candidate.lower() for phrase in [
                'is to inform', 'this is', 'subject', 'dear', 'attention',
                'all students', 'hereby', 'pleased to', 'happy to'
            ]):
                continue
            
            # Filter out single words that are too generic
            if len(candidate.split()) == 1 and candidate.lower() in ['the', 'all', 'this', 'that']:
                continue
            
            # Valid company name found
            if len(candidate) >= 2 and len(candidate) <= 50:
                company = candidate
                break
    
    # ---------------- ROLE ----------------
    role = "Unknown"
    
    role_patterns = [
        # Explicit role with label (capture up to 100 chars or newline, whichever comes first)
        (r'(?:Profile|Role|Position)\s*(?:Offered|Available)?\s*[:\-]\s*([^\n\r]+)', 1),
        (r'(?:Job Title|Designation|Post)\s*[:\-]\s*([^\n\r]+)', 1),
        (r'(?:Hiring for|Recruiting for|Looking for)\s+([^\n\r]+)', 1),
    ]
    
    for pattern, group_num in role_patterns:
        role_match = re.search(pattern, text, re.IGNORECASE)
        if role_match:
            role = role_match.group(group_num).strip()
            # Clean up role
            role = re.sub(r'\s+', ' ', role)  # normalize whitespace
            role = re.sub(r'[,\.]$', '', role)  # remove trailing punctuation
            # Remove numbers and colons (e.g., "Intern:8" -> "Intern")
            role = re.sub(r'[:\d]+$', '', role).strip()
            role = re.sub(r'^[\d]+[:\s]*', '', role).strip()  # Remove leading numbers
            
            # Filter out "Eligibility Criteria" and similar phrases
            if re.search(r'eligibility\s+criteria', role, re.IGNORECASE):
                continue
            
            # Filter out if it contains document-like text (indicates greedy match)
            if any(word in role.lower() for word in ['students', 'inform', 'notification', 'apply', 'eligible', 'directed', 'received']):
                continue
            
            # Limit to reasonable length and take only first line if multiple
            role = role.split('\n')[0].strip()
            role = re.sub(r'\.\s+.*$', '', role) # remove sentence end
            role = role[:100].strip()
            
            # Filter out if it looks like a sentence rather than a role
            if len(role.split()) > 8:  # Too long to be a role name
                continue
            
            # Must be at least 2 chars and not too long
            if len(role) >= 2 and len(role) <= 60:
                break

    
    # Fallback: infer from context if still unknown
    if role == "Unknown":
        if re.search(r'Internship.*PPO', text, re.IGNORECASE):
            role = "Internship + PPO"
        elif re.search(r'PPO', text, re.IGNORECASE):
            role = "Pre-Placement Offer"
        elif re.search(r'Internship', text, re.IGNORECASE):
            role = "Internship"
        elif re.search(r'Full[\s\-]?Time', text, re.IGNORECASE):
            role = "Full-Time Position"
    
    # ---------------- DEADLINE ----------------
    deadline = "Not Found"
    
    # Enhanced date patterns - comprehensive to catch various formats
    date_patterns = [
        # HIGHEST PRIORITY: "APPLY on or before 16th Dec'2025" (EXACT format from PDF - no space after ')
        r"(?:apply|APPLY|register|submit)\s+(?:on\s+)?(?:or\s+)?(?:before|by)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s*[A-Za-z]+\s*['’]\s*[0-9]{4})",
        
        # Also catch variations with no space after apostrophe
        r"([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+['’][0-9]{4})",
        
        # "fill the form by 12 jan 2025" or "submit by DATE"
        r'(?:fill|submit|register|complete).*?(?:by|before)\s+([0-9]{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{4})',
        
        # Date with apostrophe and optional space (e.g., "16 dec' 2025" or "16 dec'2025")
        r"([0-9]{1,2}(?:st|nd|rd|th)?\s*[A-Za-z]+\s*['’]\s*[0-9]{4})",
        
        # "APPLY on or before DATE" or similar keywords
        r'(?:APPLY|apply|register|submit)\s+(?:on\s+)?(?:or\s+)?(?:before|by)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s*[-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[-\.\s\'’]*[0-9]{4})',
        
        # Standard deadline labels
        r'(?:Deadline|Last Date|Last date|Registration closes?)\s*:?\s*([0-9]{1,2}(?:st|nd|rd|th)?\s*[-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[-\.\s,]*[0-9]{4})',
        
        # "by DATE" or "before DATE" anywhere
        r'(?:by|before|until)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{4})',
        
        # Numeric date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        r'(?:deadline|last date|apply by|submit by|before)\s*:?\s*([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})',
        
        # Standalone numeric dates (last resort)
        r'([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{4})',
        
        # Any date pattern with month name (very broad - last resort)
        r'([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[0-9]{4})',
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            try:
                date_str = date_match.group(1).strip()
                # Clean up date string
                clean_date = re.sub(r'(st|nd|rd|th)', '', date_str, flags=re.IGNORECASE)
                clean_date = re.sub(r"['’\\]", '', clean_date)  # Remove apostrophes and backslashes
                clean_date = re.sub(r'[,\s]+', ' ', clean_date).strip()
                clean_date = re.sub(r'[\.]+', ' ', clean_date).strip()  # Replace dots with spaces
                clean_date = clean_date.replace('-', ' ')  # Replace hyphens with spaces for text dates
                
                # Parse date (dayfirst=True for DD/MM/YYYY format)
                parsed_date = parser.parse(clean_date, fuzzy=True, dayfirst=True)
                deadline = parsed_date.strftime("%Y-%m-%d")
                break
            except Exception as e:
                continue
    
    return {
        "company": company,
        "role": role,
        "deadline": deadline
    }

@app.route("/extract", methods=["POST"])
def extract():
    try:
        print("\n" + "="*60)
        print("📥 NEW EXTRACTION REQUEST")
        print("="*60)
        
        pdf_url = request.json.get("pdf_url")
        if not pdf_url:
            return jsonify({"error": "No PDF URL provided"}), 400

        print(f"📄 PDF URL: {pdf_url}")
        
        # Download PDF
        print("⬇️  Downloading PDF...")
        pdf_data = requests.get(pdf_url, timeout=30).content
        print(f"✅ Downloaded {len(pdf_data)} bytes")
        
        text = extract_text(io.BytesIO(pdf_data))
        print(f"📝 Extracted {len(text)} characters of text")
        print(f"First 200 chars: {text[:200]}")
        
        if not text or len(text.strip()) < 10:
            return jsonify({"error": "Failed to extract text from PDF"}), 400
        
        # Try AI extraction first (if API key is available)
        print(f"\n🤖 Attempting AI extraction...")
        result = extract_with_ai(text)
        
        # Fallback to regex if AI fails
        if not result:
            print("⚠️  AI returned None, falling back to regex...")
            result = extract_with_regex(text)
            print(f"📊 Regex result: {result}")
        
        print(f"\n✅ FINAL RESULT: {result}")
        print("="*60 + "\n")
        
        return jsonify(result)

    except requests.exceptions.RequestException as e:
        print(f"❌ PDF Download Error: {e}")
        return jsonify({"error": f"Failed to download PDF: {str(e)}"}), 500
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "ai_enabled": bool(GEMINI_API_KEY)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
