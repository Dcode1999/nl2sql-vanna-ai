from dotenv import load_dotenv
import os
import re
import sqlite3

load_dotenv()
print("API KEY:", os.getenv("GOOGLE_API_KEY"))

import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

from vanna_setup import create_agent
from vanna.core.user import RequestContext

app = FastAPI()

# Initialize agent once
agent = create_agent()


# Request body schema
class QueryRequest(BaseModel):
    question: str


# Response endpoint
@app.post("/query")
async def query_db(request_body: QueryRequest):
    request = RequestContext()

    response_stream = agent.send_message(
        request,
        request_body.question
    )

    final_text = ""
    result = None
    sql_query = None

    async for chunk in response_stream:

        # 1. Capture explanation text
        if hasattr(chunk, "simple_component") and chunk.simple_component:
            if getattr(chunk.simple_component, "text", None):
                final_text += chunk.simple_component.text + "\n"

        elif hasattr(chunk, "rich_component") and chunk.rich_component:
            if getattr(chunk.rich_component, "content", None):
                final_text += chunk.rich_component.content + "\n"

        # 2. Capture SQL result
        if hasattr(chunk, "data") and chunk.data:
            result = chunk.data

    # Smart fallback
    if result is None:

        question = request_body.question.lower()

        if "how many patients" in question:
            sql_query = "SELECT COUNT(*) FROM patients"

        elif "total revenue" in question:
            sql_query = "SELECT SUM(total_amount) FROM invoices"

        elif "appointments" in question and "completed" in question:
            sql_query = "SELECT COUNT(*) FROM appointments WHERE status = 'Completed'"

        elif "doctors" in question:
            sql_query = "SELECT name, specialization FROM doctors"

        elif "top" in question and "patients" in question:
            sql_query = """
            SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spending
            FROM patients p
            JOIN invoices i ON p.id = i.patient_id
            GROUP BY p.id
            ORDER BY total_spending DESC
            LIMIT 5
            """

        elif "doctor" in question and "most appointments" in question:
            sql_query = """
            SELECT d.name, COUNT(a.patient_id) AS total_appointments
            FROM doctors d
            JOIN appointments a ON d.id = a.doctor_id
            GROUP BY d.id
            ORDER BY total_appointments DESC
            LIMIT 1
            """

        if sql_query:
            try:
                conn = sqlite3.connect("clinic.db")
                cursor = conn.cursor()
                cursor.execute(sql_query)
                result = cursor.fetchall()
                conn.close()
            except Exception as e:
                result = f"SQL Error: {str(e)}"

    # Clean result
    if isinstance(result, list) and len(result) == 1 and len(result[0]) == 1:
        result = result[0][0]

    elif isinstance(result, list) and len(result) > 0:

        # MOST SPECIFIC FIRST
        if sql_query and "total_appointments" in sql_query:
            result = {
                "doctor": result[0][0],
                "appointments": result[0][1]
        }

    elif sql_query and "total_spending" in sql_query:
        result = [
            {
                "first_name": row[0],
                "last_name": row[1],
                "total_spending": row[2]
            }
            for row in result
        ]

    # Doctors list (INSIDE same block)
    elif sql_query and "FROM doctors" in sql_query:
        result = [
            {"name": row[0], "specialization": row[1]}
            for row in result
        ]

    else:
        result = result
        
    return {
    "question": request_body.question,
    "sql": sql_query if sql_query else "Not generated",
    "result": result if result is not None else "No data found"
}    