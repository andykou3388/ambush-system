from fastapi import FastAPI

app = FastAPI(title="Ambush System Backend")


@app.get("/")
async def root():
    return {"message": "Welcome to Ambush System Backend"}
