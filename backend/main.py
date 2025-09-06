from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import auth, crud, log_parser, report
from .log_importer import import_logs_on_startup
import logging

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up - importing logs...")
    import_logs_on_startup()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes
app.include_router(auth.router)
# CRUD routes
app.include_router(crud.router)
# Log parser routes
app.include_router(log_parser.router)
# Report routes
app.include_router(report.router)

@app.get("/")
def root():
    return {"message": "API is running"}
