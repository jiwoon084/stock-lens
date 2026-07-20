from fastapi import FastAPI

app = FastAPI(title="Stock Lens API")


@app.get("/api/health")
def health():
    return {"status": "ok"}
