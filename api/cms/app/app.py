from fastapi import FastAPI
from cms.app.lifespan import lifespan
from structlog import get_logger
app = FastAPI(title="College Management System",lifespan=lifespan)

@app.get("/")
async def root():
    get_logger().info("Welcome to College Management System")
    return {"message": "Welcome to College Management System"}
