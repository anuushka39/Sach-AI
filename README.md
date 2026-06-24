<div align="center">

# 🛡️ Sach-AI - Misinformation Analysis System

### Detect. Verify. Understand.

**An AI-powered misinformation analysis platform that helps users evaluate the credibility of text, images, PDFs, and audio content through explainable risk assessment.**

<br>

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge\&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge\&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-Database-blue?style=for-the-badge\&logo=mysql)
![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-success?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-AI_Reasoning-orange?style=for-the-badge)
![OCR](https://img.shields.io/badge/Tesseract-OCR-red?style=for-the-badge)
![Whisper](https://img.shields.io/badge/Whisper-Speech_To_Text-purple?style=for-the-badge)

</div>

---

## The Problem

The rapid rise of generative AI has made misinformation easier to create and harder to identify.

False news articles, manipulated screenshots, misleading social media posts, edited documents, and synthetic audio can spread faster than traditional fact-checking systems can respond.

Most users don't need another chatbot.

They need a tool that helps them answer:

> **"Can I trust this content before sharing it?"**

---

## Our Solution

**Sach-AI** is a multimodal misinformation analysis platform that evaluates content across different formats and generates an explainable trust assessment.

Instead of simply labeling content as *fake* or *real*, the platform provides:

* Trust Score
* Risk Level
* Content Analysis
* Explainable Reasoning
* Historical Reports

allowing users to understand *why* a piece of content may be suspicious.

---

## Features

### Authentication System

* User Registration
* User Login
* Password Hashing
* Session Management

### Text Analysis

Analyze:

* News Articles
* Social Media Posts
* Messages
* Public Claims

Generate:

* Trust Score
* Risk Classification
* Explanation Report

### Image Analysis

* Image Upload Support
* OCR-based Text Extraction
* Screenshot Analysis
* Social Media Post Verification

### PDF Analysis

* PDF Upload
* Text Extraction
* Content Evaluation
* Report Generation

### Audio Analysis

* Speech-to-Text Conversion
* Voice Message Analysis
* Transcript Evaluation

### Explainable AI

Every prediction is accompanied by reasoning to help users understand the result rather than blindly trust an output.

### Analysis History

Users can revisit:

* Previous Uploads
* Generated Reports
* Historical Assessments

---

## System Architecture

```text
                    ┌─────────────────┐
                    │      User       │
                    └────────┬────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │ Upload Content     │
                  │ Text / Image / PDF │
                  │ Audio              │
                  └────────┬───────────┘
                           │
                           ▼
             ┌─────────────────────────────┐
             │ Content Extraction Layer    │
             ├─────────────────────────────┤
             │ OCR (Images)                │
             │ PDF Text Extraction         │
             │ Whisper Transcription       │
             └─────────────┬───────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ Text Processing Layer   │
              │ Cleaning + TF-IDF       │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ XGBoost Classifier      │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ Trust Score Generation  │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ Gemini Explanation      │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ Report Generation       │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ MySQL Database          │
              └─────────────────────────┘
```

---

## Technology Stack

### Frontend

```text
HTML5
CSS3
Jinja Templates
```

### Backend

```text
Flask
Flask-SQLAlchemy
Flask-Bcrypt
```

### Database

```text
MySQL
```

### Machine Learning

```text
Scikit-Learn
TF-IDF Vectorization
XGBoost
```

### Natural Language Processing

```text
NLTK
Regular Expressions
```

### OCR

```text
Tesseract OCR
Pillow
```

### Audio Processing

```text
Whisper
```

### AI Reasoning Layer

```text
Google Gemini API
```

### Report Generation

```text
ReportLab
```

---

## Project Flow

```text
Login
  ↓
Upload Content
  ↓
Extract Text
  ↓
Preprocess Data
  ↓
TF-IDF Vectorization
  ↓
XGBoost Prediction
  ↓
Trust Score
  ↓
AI Explanation
  ↓
Generate Report
  ↓
Store Results
  ↓
View History
```

---

## Database Design

### Users

```sql
id
name
email
password_hash
created_at
```

### Uploads

```sql
upload_id
user_id
file_path
file_type
upload_time
```

### Reports

```sql
report_id
user_id
trust_score
risk_level
report_path
created_at
```

---

## Project Structure

```bash
sach-ai/

├── app.py
├── config/
├── routes/
├── models/
├── services/
├── ml/
├── templates/
├── static/
├── uploads/
├── reports/
├── datasets/
├── requirements.txt
└── README.md
```

---

## Future Enhancements

* Deepfake Image Detection
* Video Analysis
* Reverse Image Search
* Browser Extension
* Multilingual Verification
* Real-Time Fact Checking
* Cloud Deployment
* Advanced User Analytics

---

## Vision

Sach-AI aims to make misinformation analysis more transparent, explainable, and accessible.

The goal is not to replace human judgment.

The goal is to help users make better-informed decisions before trusting or sharing digital content.

---

<div align="center">

### "Trust, but verify."

Built for AI Safety, Responsible AI, and Digital Trust.

</div>


## Team

Built during the Global South AI Safety Hackathon.


