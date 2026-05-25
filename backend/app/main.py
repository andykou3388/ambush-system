from fastapi import FastAPI
from app.core.metrics import metrics_middleware, metrics_endpoint

app = FastAPI(title="Ambush System Backend")
app.middleware("http")(metrics_middleware)
app.add_route("/metrics", metrics_endpoint)


@app.get("/")
async def root():
    return {"message": "Welcome to Ambush System Backend"}
