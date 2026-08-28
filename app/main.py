from fastapi import FastAPI

app = FastAPI(
    title="AI Operator",
    version="0.1.0",
    description="Bounded voice AI call-center operator backend",
)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    # Provider readiness will be added only after real providers are configured.
    return {"status": "foundation-ready"}
