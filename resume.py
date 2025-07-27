from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import boto3
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# 🔒 AWS Credentials (for testing/local use only — not production safe)
AWS_ACCESS_KEY = "Access-Key"      # Replace this with your AWS Access Key 
AWS_SECRET_KEY = "AWS-Secret-Key"  # Replace this with your AWS Secret Key
AWS_REGION = "us-east-1"           # Replace with your s3 bucket region 
BUCKET_NAME = "agentic-ai-screener-data"

# Initialize the boto3 S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Serve the frontend HTML
@app.route('/')
def index():
    return send_from_directory('.', 'resume.html')

# Handle file uploads
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'resume' not in request.files or 'jd' not in request.files:
        return jsonify({"error": "Missing resume or job description file"}), 400

    resume = request.files['resume']
    jd = request.files['jd']

    try:
        # Clean file names
        resume_filename = secure_filename(resume.filename)
        jd_filename = secure_filename(jd.filename)

        # Define S3 storage paths
        resume_s3_key = f"resumes/pending/{resume_filename}"
        jd_s3_key = f"job-descriptions/{jd_filename}"

        # Upload to S3
        s3.upload_fileobj(resume, BUCKET_NAME, resume_s3_key)
        s3.upload_fileobj(jd, BUCKET_NAME, jd_s3_key)

        return jsonify({
            "message": "✅ Files uploaded successfully",
            "resume_s3_key": resume_s3_key,
            "jd_s3_key": jd_s3_key
        }), 200

    except Exception as e:
        return jsonify({"error": f"❌ Upload failed: {str(e)}"}), 500

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
