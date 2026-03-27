from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.routers import metrics, admin

app = FastAPI(title="Quality Metrics Platform API")

# Include routers
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(admin.router)

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint to verify the service is running.
    Returns a simple JSON payload with status and a greeting.
    """
    return {"status": "ok", "message": "Quality Metrics Platform is healthy"}

# If this module is run directly, start the Uvicorn server for quick local testing.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
