from cms.app.lifespan import lifespan
from cms.app.middlewares import (
    ContextMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger
from cms.users.views import router as users_router
from cms.permissions.views import router as permissions_router
from cms.sessions.views import router as sessions_router
from cms.auth.views import router as auth_router
from cms.students.views import router as students_router
from cms.staff.views import router as staff_router
from cms.parents.views import router as parents_router
from cms.schools.views import router as schools_router
from cms.departments.views import router as departments_router
from cms.programs.views import router as programs_router
from cms.batch.views import router as batch_router
from cms.auth.exceptions import (
    NotEnoughPermissionsException,
    CredentialsNotFoundException,
    SessionInvalidOrExpiredException,
)
from cms.auth.exception_handler import (
    credentials_not_found_exception_handler,
    not_enough_permissions_exception_handler,
    session_invalid_or_expired_exception_handler,
)

app = FastAPI(
    title="College Management System",
    lifespan=lifespan,
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ContextMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_exception_handler(
    NotEnoughPermissionsException,
    not_enough_permissions_exception_handler,
)
app.add_exception_handler(
    CredentialsNotFoundException,
    credentials_not_found_exception_handler,
)
app.add_exception_handler(
    SessionInvalidOrExpiredException,
    session_invalid_or_expired_exception_handler,
)


app.include_router(users_router)
app.include_router(permissions_router)
app.include_router(sessions_router)
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(staff_router)
app.include_router(parents_router)
app.include_router(schools_router)
app.include_router(departments_router)
app.include_router(programs_router)
app.include_router(batch_router)


@app.get("/")
async def root():
    logger = get_logger()
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to College Management System"}
