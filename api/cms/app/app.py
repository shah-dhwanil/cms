from cms.app.lifespan import lifespan
from cms.users.views import router as user_router
from cms.permissions.views import router as permission_router
from cms.sessions.views import router as session_router
from cms.auth.views import router as auth_router
from cms.auth.exceptions import (
    CredentialsNotFound,
    credentials_not_found_exception_handler,
    SessionInvalidOrExpired,
    session_invalid_or_expired_exception_handler,
    NotEnoughPermissions,
    not_enough_permissions_exception_handler,
)
from fastapi import FastAPI
from structlog import get_logger

app = FastAPI(
    title="College Management System",
    lifespan=lifespan,
    exception_handlers={
        CredentialsNotFound: credentials_not_found_exception_handler,
        SessionInvalidOrExpired: session_invalid_or_expired_exception_handler,
        NotEnoughPermissions: not_enough_permissions_exception_handler,
    },
)
app.include_router(user_router)
app.include_router(permission_router)
app.include_router(session_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    print("request_recieved")
    get_logger().info("Welcome to College Management System")
    return {"message": "Welcome to College Management System"}
