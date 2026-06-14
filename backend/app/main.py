from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import dashboard, projects, vendors, agent, rag

app = FastAPI(
    title="AI Construction Commander",
    description="Multi-agent root cause analysis for construction project delays",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(projects.router)
app.include_router(vendors.router)
app.include_router(agent.router)
app.include_router(rag.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Construction Commander API"}
