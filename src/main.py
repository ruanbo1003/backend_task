from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Any
from pydantic import BaseModel, Field
import datetime
import uuid
from contextlib import asynccontextmanager
from const import TaskStatus
from tasks import text2image
from database import MongoUtil
from logger import log_info, log_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await MongoUtil.ping()
        log_info("app", "Successfully connected to MongoDB")
    except Exception as e:
        log_error("app", f"Failed to connect to MongoDB: {str(e)}")
    
    yield
    
    # Shutdown
    MongoUtil.close()
    log_info("app", "Closed MongoDB connection")

class GenerateRequest(BaseModel):
    username: str = Field(min_length=4, max_length=32)
    prompt: str = Field(min_length=8, max_length=256)


class ApiResponse(JSONResponse):
    def __init__(self, content: Any = None, code: int = 2000, message: str = "", **kwargs):
        self.custom_content = {
            "code": code,
            "msg": message,
            "data": content
        }
        super().__init__(content=self.custom_content, **kwargs)

app = FastAPI(default_response_class=ApiResponse, lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Get request body if it exists
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = await request.body()

    log_info("api", {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "body": body
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    log_info("api", {
        "request_id": request_id,
        "status_code": response.status_code
    })
    
    return response

# Get all tasks
@app.get("/api/v1/tasks")
async def get_all_tasks():
    try:
        # Find all tasks and sort by created_at in descending order
        tasks = await MongoUtil.all_tasks()

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
        
        await MongoUtil.insert_one(document)

        # Send task to Celery
        text2image.delay(task_id, request.username, request.prompt)

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


# Get status of a task
@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str):
    try:
        # 查询任务状态
        document = await MongoUtil.find_one({"task_id": task_id})
        if document:
            return ApiResponse(content=document, message="success")
        else:
            return ApiResponse(content=None, code=4040, message="Task not found")
    except Exception as e:
        return ApiResponse(content=None, code=5000, message=str(e))


#Delete a task
@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        # Find and delete the task
        result = await MongoUtil.update_task_status(task_id, TaskStatus.CANCEL.value)
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
