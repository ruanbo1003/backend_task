import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from fastapi.responses import JSONResponse
from typing import Any, Dict
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import uuid
from contextlib import asynccontextmanager
from enum import Enum

class TaskStatus(str, Enum):
    WAITING = "waiting"
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"

# MongoDB connection setup
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://user_api:abc123xyz@localhost:27017?authSource=backend_assignment")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.backend_assignment
collection = db.tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
    
    yield
    
    # Shutdown
    client.close()
    print("Closed MongoDB connection")

class GenerateRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=32)
    prompt: str = Field(..., min_length=8, max_length=256)


class ApiResponse(JSONResponse):
    def __init__(self, content: Any = None, code: int = 2000, message: str = "", **kwargs):
        self.custom_content = {
            "code": code,
            "msg": message,
            "data": content
        }
        # print("content:", content)

        super().__init__(content=self.custom_content, **kwargs)

app = FastAPI(default_response_class=ApiResponse, lifespan=lifespan)


# Get all tasks
@app.get("/api/v1/tasks")
async def get_all_tasks():
    try:
        # Find all tasks and sort by created_at in descending order
        cursor = collection.find().sort("created_at", -1)
        tasks = await cursor.to_list(length=None)

        # Convert ObjectId to string and datetime to ISO format for JSON serialization
        for task in tasks:
            task["_id"] = str(task["_id"])
            if "created_at" in task:
                task["created_at"] = task["created_at"].isoformat()

        return ApiResponse(
            content={"tasks": tasks},
            message="success"
        )
    except Exception as e:
        return ApiResponse(
            content=None,
            code=5000,
            message=str(e)
        )



@app.post("/api/v1/generate")
async def generate(request: GenerateRequest):
    try:
        # Generate task ID
        task_id = str(uuid.uuid4().hex)
        
        # Save request to MongoDB
        document = {
            "task_id": task_id,
            "username": request.username,
            "prompt": request.prompt,
            "created_at": datetime.datetime.now(datetime.UTC),
            "status": TaskStatus.WAITING.value  # Initial status
        }
        
        await collection.insert_one(document)

        # Return task information to client
        result = {
            "task_id": task_id,
            "username": request.username,
            "prompt": request.prompt,
            "status": TaskStatus.WAITING.value
        }
        
        return ApiResponse(content=result, message="success")
    except Exception as e:
        return ApiResponse(
            content=None,
            code=5000,
            message=str(e),
            status_code=500
        )


# 获取任务状态
@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    try:
        # 查询任务状态
        document = await collection.find_one({"task_id": task_id})
        if document:
            return ApiResponse(content=document, message="success")
        else:
            return ApiResponse(content=None, code=4040, message="Task not found")
    except Exception as e:
        return ApiResponse(content=None, code=5000, message=str(e))
    


#delete a task 
@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        # Find and delete the task
        result = await collection.delete_one({"task_id": task_id})
        
        if result.deleted_count > 0:
            return ApiResponse(
                content={"task_id": task_id},
                message="success"
            )
        else:
            return ApiResponse(
                content=None,
                code=4040,
                message="Task not found"
            )
    except Exception as e:
        return ApiResponse(
            content=None,
            code=5000,
            message=str(e)
        )

