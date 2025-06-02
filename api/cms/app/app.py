from fastapi import FastAPI
from cms.app.lifespan import lifespan
from structlog import get_logger
from cms.utils.minio import MinioClient
app = FastAPI(title="College Management System", lifespan=lifespan)
@app.get("/")
async def root():
    print("request_recieved")
    client = MinioClient.get_client()
    await client.make_bucket("firebase")
    get_logger().info("Welcome to College Management System")
    return {"message": "Welcome to College Management System"}
