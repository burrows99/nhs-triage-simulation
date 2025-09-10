from typing import Dict
from fastapi import FastAPI

app: FastAPI = FastAPI(
    title="Dissertation API",
    description="A FastAPI application for dissertation project",
    version="1.0.0"
)


@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello World"}