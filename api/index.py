import time
import uuid
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-oyxbjn.example.com"
STUDENT_EMAIL = "24f3005284@ds.study.iitm.ac.in"

# Add standard CORS middleware configured specifically for the allowed origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def custom_headers_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start_time
    
    # Required headers
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    return response

@app.get("/stats")
def get_stats(values: Optional[str] = None):
    if not values:
        nums = []
    else:
        nums = [int(x.strip()) for x in values.split(",") if x.strip()]
    
    n = len(nums)
    if n == 0:
        return {
            "email": STUDENT_EMAIL,
            "count": 0,
            "sum": 0,
            "min": 0,
            "max": 0,
            "mean": 0.0
        }
    
    total = sum(nums)
    minimum = min(nums)
    maximum = max(nums)
    mean_val = total / n
    
    return {
        "email": STUDENT_EMAIL,
        "count": n,
        "sum": total,
        "min": minimum,
        "max": maximum,
        "mean": mean_val
    }

@app.get("/")
def root():
    return {"message": "CORS-Aware Metrics API is running", "email": STUDENT_EMAIL}