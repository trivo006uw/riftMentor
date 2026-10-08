from fastapi import FastAPI

app = FastAPI(title = "RiftMentor API")

@app.get("/health")
def healthCheck():
    return {"status" : "ok"}