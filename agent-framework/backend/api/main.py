from fastapi import FastAPI
from agent_framework.core.agent import Agent

app = FastAPI()
agent = Agent()

@app.post('/run')
def run(payload: dict):
    return {"result": "ok"}
