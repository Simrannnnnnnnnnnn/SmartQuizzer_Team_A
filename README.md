# 🧠 **SmartQuizzer: AI-Powered Quiz Generator**
**Team A - Final Project | Infosys Internship**

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Render-%23430098.svg?style=for-the-badge&logo=render&logoColor=white)

SmartQuizzer is a full-stack web application designed to help students and educators generate high-quality quizzes instantly using Artificial Intelligence. Users can input topics, raw text, or even upload PDF documents to create customized multiple-choice questions.

**Live Demo:** [https://smartquizzer.onrender.com](https://smartquizzer.onrender.com)

## 👥 Team Roles & Responsibilities

| Member | Professional Role | Key Area of Responsibility |
| :--- | :--- | :--- |
| **@Simran** | **Team Lead** | **Project Architecture & Deployment**: Managing GitHub, coordinating team workflows, and final project hosting on Render. |
| **@AkashRaja123** | **UI/UX & Security** | **User Experience & Auth**: Designing the visual interface and building the secure Login/Signup system with personalized dashboards. |
| **@ChavalaRevathi** | **Data Ingestion** | **Data Processing**: Building the logic to handle PDF uploads, raw text inputs, and preparing study materials for the AI. |
| **@RiddhiWani** | **Frontend Interactivity** | **Real-time Features**: Developing the 30-second quiz timer and the instant "Correct/Incorrect" feedback pop-ups. |
| **@gopika2204** | **AI Engine Specialist** | **LLM Integration**: Engineering the Llama-3 (Groq API) prompts to generate accurate MCQs and detailed explanations. |
| **@Ankita-Kumari0309** | **Data Analytics** | **Progress Tracking**: Managing the database for user learning streaks and creating performance visualization charts. |


---

## 🚀 **Features**

* **AI Generation:** Leverages the Groq API (LLM) to generate accurate MCQs with explanations.
* **Multiple Inputs:** Generate quizzes from text, specific topics, or uploaded PDF files.
* **User Authentication:** Secure Signup/Login system using Flask-Login.
* **Personal Library:** Save generated quizzes to a personal dashboard to review or retake later.
* **Progress Tracking:** Interactive quiz interface with real-time scoring and streak tracking.
* **Responsive Design:** Mobile-friendly interface built with modern CSS.

---

## 🛠️ **Tech Stack**

* **Backend:** Python (Flask)
* **Frontend:** HTML5, CSS3, JavaScript
* **Database:** SQLAlchemy (SQLite)
* **AI Integration:** Groq API / LLM Client
* **File Processing:** PyPDF
* **Deployment:** Render

---

## 📂 **Project Structure**

```text
SmartQuizzer/
├── app/                # Backend logic
│   ├── routes.py       # Flask Blueprints & routing
│   ├── models.py       # Database schemas (User, Question)
│   └── llm_client.py   # AI integration logic
├── templates/          # HTML files (Root level)
├── static/             # CSS, JS, and Images
├── main.py             # App entry point
├── requirements.txt    # Python dependencies
└── .env                # Environment variables (Hidden)
```
---
## ⚙️ Installation & Setup

### 1. Clone the repository
git clone https://github.com/Simrannnnnnnnnnnn/SmartQuizzer.git
cd ai-quiz-generator

### 2. Create and activate a Virtual Environment
python -m venv venv
#### On Windows: venv\Scripts\activate
#### On Mac/Linux: source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Set up Environment variables
#### Create a .env file and add your keys:
#### GROQ_API_KEY=your_api_key_here
#### SECRET_KEY=your_secret_key

### 5. Run the application
python main.py

---
## 📬 Contact

If you have any questions or feedback, feel free to reach out!

* **Name:** Simran Kaur
* **Email:** [kaur.simran1542@gmail.com](mailto:kaur.simran1542@gmail.com)
* **GitHub:** [Simrannnnnnnnnnnn](https://github.com/Simrannnnnnnnnnnn)
* **Project Link:** [SmartQuizzer](https://github.com/Simrannnnnnnnnnnn/SmartQuizzer)
---
