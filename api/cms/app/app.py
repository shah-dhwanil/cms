from cms.app.lifespan import lifespan
from cms.app.middlewares import (
    ContextMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)
from fastapi import FastAPI
from structlog import get_logger
from cms.users.views import router as users_router

app = FastAPI(
    title="College Management System",
    lifespan=lifespan,
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ContextMiddleware)
app.add_middleware(RequestIDMiddleware)


app.include_router(users_router)

@app.get("/")
async def root():
    logger = get_logger()
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to College Management System"}
