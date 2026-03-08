from fastapi import FastAPI

app = FastAPI(
    title="NewLearn API",
    version="1.0"
)

@app.get("/")
def root():
    return {"message": "server running"}