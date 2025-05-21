from fastapi import FastAPI

app = FastAPI(title="College Management System")

@app.get("/")
async def root():
    return {"message": "Welcome to College Management System"}
