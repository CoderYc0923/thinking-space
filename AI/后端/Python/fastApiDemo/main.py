from fastapi import FastAPI

app = FastAPI(title="demo", description="this is a demo api", version="1.0.0")


@app.get("/")
def index():
    return {"message": "Hello World", "code": 200}
