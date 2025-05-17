import asyncio
import random
import os
from celery import Celery
from const import TaskStatus
from database import MongoUtil
from logger import log_info, log_error


# Celery configuration
celery_app = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)


async def do_text_to_image(task_id: str, username: str, prompt: str):
    try:
        # Update task status to pending
        task = await MongoUtil.find_one(
            {"task_id": task_id},
        )
        if not task:
            return

        # only the `waiting` status task will be handled
        if task['status'] != 'waiting':
            return

        # Update task status to pending
        result = await MongoUtil.update_task_status(task_id, TaskStatus.PENDING.value)
        if result.modified_count == 0:
            log_error("text2image", "update to done failed")
        else:
            log_info("text2image", "update to done")
            return

        # TODO: run ComfyUI to generate image
        # result = comfyui_generate_image(task_id, prompt)

        # Update task status to done
        result = await MongoUtil.update_task_status(task_id, TaskStatus.DONE.value, info="success")
        if result.modified_count == 0:
            log_error("text2image", "update to done failed")
        else:
            log_info("text2image", "update to done")

    except Exception as e:
        # Update task status to error
        log_error("text2image", f"task error: {str(e)}")
        await MongoUtil.update_task_status(task_id, TaskStatus.ERROR.value, info=str(e))


def is_gpu_available():
    # TODO: get current GPU status, to check if any GPU is available
    return random.choice([True, False])   # TODO: simulate if gpu is available


@celery_app.task(bind=True, name='text2image', max_retries=3, default_retry_delay=10)
def text2image(self, task_id: str, username: str, prompt: str):
    if not is_gpu_available():
        log_error("text2image", "gpu un-available")

        if self.request.retries >= self.max_retries - 1:
            # Max retry, set the status to error
            asyncio.run(MongoUtil.update_task_status(task_id, TaskStatus.ERROR.value, "gpu busy"))
            return
        else:
            # retry
            raise self.retry(exc=RuntimeError("GPU busy"))

    asyncio.run(do_text_to_image(task_id, username, prompt))
