import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection setup
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://user_api:abc123xyz@localhost:27017?authSource=backend_assignment")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.backend_assignment
tasks_collection = db.tasks


class MongoUtil:
    @staticmethod
    async def ping():
        await client.admin.command('ping')

    @staticmethod
    def close():
        client.close()

    @staticmethod
    async def insert_one(doc, coll=tasks_collection):
        await coll.insert_one(doc)

    @staticmethod
    async def update_one(query: dict, update: dict, coll=tasks_collection):
        return await coll.update_one(query, update)

    @staticmethod
    async def find_one(query: dict, coll=tasks_collection):
        return await coll.find_one(query)

    @staticmethod
    async def all_tasks():
        cursor = tasks_collection.find().sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def update_task_status(task_id, status, info=""):
        return await MongoUtil.update_one(
            query={"task_id": task_id},
            update={"$set": {
                "status": status,
                "info": info,
            }},
        )
