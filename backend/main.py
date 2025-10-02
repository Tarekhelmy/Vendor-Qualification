from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, vendors, applications, forms, documents

app = FastAPI(
    title="Vendor Qualification Portal API",
    description="API for vendor project qualification applications",
    version="1.0.0"
)

# CORS middleware - MUST be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(form1.router, prefix="/api/forms", tags=["Form 1"])
app.include_router(form2.router, prefix="/api/forms", tags=["Form 2"])
app.include_router(form3.router, prefix="/api/forms", tags=["Form 3"])

@app.get("/")
async def root():
    return {"message": "Vendor Qualification Portal API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)