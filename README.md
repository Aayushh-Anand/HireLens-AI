# HireLens AI – AI-Powered Resume Analysis and Job Matching System

<p align="center">
  <strong>Analyze. Optimize. Get Job-Ready.</strong>
</p>

<p align="center">
  An AI-powered platform that helps students, fresh graduates, and job seekers analyze their resumes against specific job descriptions and identify opportunities for improvement.
</p>

---

## 📌 About the Project

**HireLens AI** is an AI and Natural Language Processing (NLP)-based web application designed to make resume analysis and job matching smarter, easier, and more effective.

In today's competitive job market, candidates often struggle to understand whether their resumes meet the requirements of a particular job. Traditional resume screening methods primarily depend on keyword matching, which may overlook contextual relationships between skills and job requirements.

HireLens AI addresses this challenge by analyzing uploaded resumes against job descriptions and providing meaningful insights, including compatibility analysis, skill matching, missing keywords, resume quality evaluation, and improvement suggestions.

The primary goal is to help candidates create more relevant, job-specific resumes and better understand their strengths and skill gaps.

## ✨ Key Features

- **Resume Upload:** Upload resumes in PDF and DOCX formats.
- **Job Description Analysis:** Analyze job descriptions to identify important requirements, skills, and keywords.
- **Resume–Job Matching:** Compare resume content with job-specific requirements.
- **Compatibility Score:** Generate a matching score to indicate how closely a resume aligns with a given job description.
- **Skill Gap Analysis:** Identify matching and missing skills.
- **ATS Keyword Analysis:** Evaluate keyword coverage and highlight relevant missing keywords.
- **Resume Quality Analysis:** Analyze resume content and provide quality-related insights.
- **Semantic Matching:** Identify contextual similarities beyond exact keyword matching.
- **Actionable Suggestions:** Provide insights to help candidates improve their resumes.
- **Interactive Dashboard:** Present analysis results in a structured and user-friendly interface.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| API Communication | REST API |
| Document Processing | PDF and DOCX parsing |
| AI / NLP | Natural Language Processing, Text Processing |
| Matching Techniques | Keyword Matching, Semantic Similarity |
| Similarity Measurement | Embeddings, Cosine Similarity |
| Development Tools | VS Code, Git, GitHub |

## 🏗️ System Architecture

HireLens AI follows a frontend–backend architecture.

1. **User Interface:** Users upload their resumes and enter the target job description.
2. **API Layer:** FastAPI receives the resume and job description.
3. **Document Processing:** Text is extracted from the uploaded PDF or DOCX document.
4. **Text Processing:** Extracted content is cleaned and normalized.
5. **Matching Engine:** Resume content is compared with job requirements.
6. **Analysis Modules:** Skill matching, semantic suggestions, ATS keyword analysis, and resume quality analysis are performed.
7. **Results Dashboard:** The frontend displays the generated analysis and recommendations.

## 📂 Project Structure

```text
HireLens-AI/
│
├── app/
│   ├── main.py
│   ├── jd_parser.py
│   ├── matching_engine.py
│   ├── semantic_matcher.py
│   ├── resume_quality_analyzer.py
│   └── ats_keyword_analyzer.py
│
├── client/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── requirements.txt
├── .gitignore
└── README.md
```

*Note: This represents the intended core structure. Additional files and folders may exist in the actual implementation.*

## ⚙️ Installation and Setup

Follow these steps to run HireLens AI locally.

### Prerequisites

Make sure you have installed:

- Python 3.10 or later
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/HireLens-AI.git
```

```bash
cd HireLens-AI
```

### 2. Set Up the Backend

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Backend server:

```text
http://127.0.0.1:8000
```

### 3. Set Up the Frontend

Open a new terminal and navigate to the client directory:

```bash
cd client
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local frontend URL displayed in your terminal, usually:

```text
http://localhost:5173
```

## 🔌 API Endpoints

HireLens AI uses FastAPI to expose REST API endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze a resume against a job description |

### API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Once the backend is running, visit:

```text
http://127.0.0.1:8000/docs
```

## 🔍 How It Works

1. Upload your resume in PDF or DOCX format.
2. Enter or paste the target job description.
3. Submit the information for analysis.
4. The system extracts and processes the resume and job description.
5. NLP and matching techniques analyze the relationship between candidate skills and job requirements.
6. The system generates a compatibility score, matching insights, skill gaps, keyword analysis, and resume quality feedback.
7. Review the results and use the suggestions to improve your resume.

## 🎯 Project Objectives

- Automate resume analysis using Artificial Intelligence.
- Improve job-specific resume optimization.
- Identify relevant and missing skills.
- Analyze keyword coverage for ATS-oriented resumes.
- Use semantic techniques to improve resume–job matching.
- Help students and fresh graduates understand job requirements.
- Provide actionable feedback for improving resume quality.

## 🚀 Future Scope

The project can be extended with the following features:

- AI-powered resume rewriting and optimization.
- Resume generation using predefined templates.
- Multiple job description comparison.
- Personalized career recommendations.
- Advanced semantic matching using transformer-based models.
- User authentication and personalized dashboards.
- Resume history and analysis tracking.
- Downloadable resume analysis reports.
- Integration with job portals and recruitment platforms.

## ⚠️ Important Disclaimer

The compatibility score generated by HireLens AI is an indicative measure of resume alignment with a particular job description. It is not an official ATS score, a hiring probability, or a guarantee of selection.

The analysis is intended to support candidates in improving their resumes and understanding job requirements.

## 🎓 Project Information

**Project Name:** HireLens AI  
**Full Title:** HireLens – AI-Powered Resume Analysis and Job Matching System  
**Project Domain:** Artificial Intelligence and Machine Learning  
**Subdomains:** Natural Language Processing, Resume Analysis, Semantic Matching  
**Project Type:** Web-Based AI Application  
**Purpose:** Academic and Educational Project

## 👨‍💻 Author

**Developed by:** Aayush Anand

---

<p align="center">
  <strong>HireLens AI</strong><br/>
  Making Resume Analysis Smarter with Artificial Intelligence.
</p>