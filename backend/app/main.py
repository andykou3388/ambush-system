from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Ambush System Backend")

@app.get("/")
async def root():
    return {"message": "Welcome to Ambush System Backend"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)