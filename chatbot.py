import chainlit as cl

# Model
from langchain_openai import ChatOpenAI

# Prompt
from langchain_core.prompts import ChatPromptTemplate

# Tool
from tools import get_company_profile_tool, get_competitors_tool

# Agent 
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions

# Memory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate

import os
from dotenv import load_dotenv

load_dotenv()

rapid_api_key = os.getenv("RAPID_API_KEY")
llm = ChatOpenAI(model_name = "gpt-3.5-turbo", temperature = 0)

store = {} 

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


@cl.set_starters
async def starters():
    return [
       cl.Starter(
           label="Question 1",
           message="What is AAPL and META? Is the head quarter located in the same country?"
       ),
       cl.Starter(
           label="Question 2",
           message="List all competitors of GOOG?"
       )
    ]

@cl.step(type="tool")
async def tool():
    input = cl.user_session.get("input")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "you're a helpful assistant"),
        ("placeholder", "{history}"), 
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    tools = [get_company_profile_tool, get_competitors_tool]

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose = True, return_intermediate_steps=True)

    agent_executor_w_memory = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )

    response = await agent_executor_w_memory.ainvoke({"input":input},
                                                     config={"configurable": {"session_id": "abc123"}},
                                                     callbacks=[cl.AsyncLangchainCallbackHandler()])
    
    return response

@cl.on_message
async def chat(message: cl.Message):
    cl.user_session.set("input", message.content)
    
    response = await tool()
    print(response)

    history = get_session_history("abc123")
    intermediate_steps = format_to_openai_functions(response['intermediate_steps'])

    if len(intermediate_steps) > 0:
        history.add_message(intermediate_steps[1])

    await cl.Message(response["output"]).send()

