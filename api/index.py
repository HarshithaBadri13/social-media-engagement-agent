from fastapi import FastAPI

app = FastAPI(
    title="FastAPI on Vercel",
    description="FastAPI serverless application deployed on Vercel",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {"Python": "on Vercel"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
