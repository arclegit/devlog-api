from fastapi import FastAPI

app = FastAPI(title="DevLog API")

@app.get("/")
def root():
    return {"message": "DevLog API is running"}