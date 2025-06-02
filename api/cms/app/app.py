from cms.app.lifespan import lifespan
from fastapi import FastAPI
from structlog import get_logger
from cms.users.views import app as user_app

app = FastAPI(title="College Management System", lifespan=lifespan)
app.mount("/users", user_app, "Users")


@app.get("/")
async def root():
    print("request_recieved")
    get_logger().info("Welcome to College Management System")
    return {"message": "Welcome to College Management System"}
