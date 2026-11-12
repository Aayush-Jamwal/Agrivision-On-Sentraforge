"""
FastAPI Gateway Main Entrypoint
Exports the gateway application instance from app.gateway.
"""
from app.gateway import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.gateway:app", host="0.0.0.0", port=8080, reload=True)

