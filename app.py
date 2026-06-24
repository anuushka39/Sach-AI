from flask import Flask, request, render_template, request, redirect, url_for, session, flash, send_file,jsonify
from markupsafe import escape, Markup
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pdf_service import generate_report
from services.preprocessing import preprocess_text
from services.ai_detector import detect_ai_text
from services.fact_checker import check_fact
from services.source_checker import get_source_score
from services.crediblity_score import calculate_score

app = Flask(__name__)
latest_claim = ""
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():

    global latest_claim

    data = request.get_json()
    
    latest_claim = data["claim"]

    clean_claim = preprocess_text(
        latest_claim
    )

    ai_result = detect_ai_text(
        clean_claim
    )

    fact_result = check_fact(
        latest_claim
    )

    source_result = get_source_score()

    trust_score = calculate_score(
        ai_result["ai_probability"],
        fact_result["fact_score"],
        source_result["source_score"]
    )

    latest_report = {

    "claim": latest_claim,

    "processed_claim": clean_claim,

    "ai_score": ai_result["ai_probability"],

    "ai_label": ai_result["label"],

    "fact_verdict": fact_result["verdict"],

    "fact_score": fact_result["fact_score"],

    "source_name": source_result["source_name"],

    "source_score": source_result["source_score"],

    "trust_score": trust_score
}

    app.config["REPORT"] = latest_report

    print(latest_report)

    return {
        "status": "success"
    }


@app.route("/download-report")
def download_report():

    report = app.config["REPORT"]

    pdf_file = generate_report(
        report
    )

    return send_file(
        pdf_file,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)
