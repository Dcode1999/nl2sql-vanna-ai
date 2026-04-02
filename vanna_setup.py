import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Vanna imports
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory

from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
)

from vanna.core.user import User, UserResolver, RequestContext

# Gemini LLM
from vanna.integrations.google import GeminiLlmService


# Simple user resolver
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request: RequestContext) -> User:
        return User(id="default_user")


def create_agent():
    # 1. LLM
    llm = GeminiLlmService(api_key=GOOGLE_API_KEY, model="gemini-2.5-flash")

    # 2. Database runner
    runner = SqliteRunner("clinic.db")

    # 3. Tool registry
    tool_registry = ToolRegistry()

    tool_registry.tools = [
        RunSqlTool(runner),
        VisualizeDataTool(),
        SaveQuestionToolArgsTool(),
        SearchSavedCorrectToolUsesTool(),
    ]

    # 4. Memory
    memory = DemoAgentMemory()

    # 5. User resolver
    user_resolver = SimpleUserResolver()

    # 6. Agent config
    config = AgentConfig(
        system_prompt="""
    You are an AI SQL assistant.

    STRICT INSTRUCTIONS:
    - Always convert the user question into SQL.
    - Always execute SQL using available tools.
    - Never stop at explanation.
    - Always return the final result from the database.

    Database schema:
    patients(id, first_name, last_name, city, gender)
    doctors(id, name, specialization)
    appointments(patient_id, doctor_id, appointment_date, status)
    invoices(patient_id, total_amount, status)

    IMPORTANT RULE:
    - patients table uses 'id', NOT 'patient_id'
    - Only use 'patient_id' in other tables
    """
    )

    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=memory,
        config=config,
    )

    print("Agent created successfully")

    return agent


# For testing
import asyncio
from vanna.core.user import RequestContext


async def main():
    agent = create_agent()
    print("Agent type:", type(agent))

    request = RequestContext()

    response_stream = agent.send_message(request, "How many patients do we have?")

    async for chunk in response_stream:
        if hasattr(chunk, "simple_component") and chunk.simple_component:
            print(chunk.simple_component.text)


if __name__ == "__main__":
    asyncio.run(main())
