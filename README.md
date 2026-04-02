## 🚀 NL2SQL System using Vanna AI & FastAPI

### 📌 Overview

This project converts natural language queries into SQL and executes them on a database.

Users can query data without writing SQL.

---

### 🛠 Tech Stack

* Python
* FastAPI
* Vanna AI
* SQLite
* Gemini API

---

### ⚙️ Features

* Natural Language → SQL
* Automatic SQL execution
* Fallback system for reliability
* Structured JSON API response

---

### 🔥 Example

#### Input:

```json
{
  "question": "Which doctor has the most appointments?"
}
```

#### Output:

```json
{
  "question": "...",
  "sql": "SELECT ...",
  "result": {
    "doctor": "Lisa Horton",
    "appointments": 43
  }
}
```

---

### ▶️ How to Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
http://127.0.0.1:8000/docs
