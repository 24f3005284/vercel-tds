import time
import uuid
from typing import Optional
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-oyxbjn.example.com"
STUDENT_EMAIL = "24f3005284@ds.study.iitm.ac.in"

# OIDC Verification Config
IDP_ISSUER = "https://idp.exam.local"
IDP_AUDIENCE = "tds-fzt6kfje.apps.exam.local"
IDP_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

# CORS middleware for question 3
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
    
    # Required headers for Q3
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    return response

# --- Q3 Endpoint ---
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

# --- Q4 Endpoint ---
class TokenVerifyRequest(BaseModel):
    token: str

@app.post("/verify")
def verify_token(req: TokenVerifyRequest):
    try:
        # Decode and verify RS256 token against key, issuer, audience, and expiration
        payload = jwt.decode(
            req.token,
            IDP_PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=IDP_ISSUER,
            audience=IDP_AUDIENCE,
            options={"require": ["exp", "iss", "aud", "sub"]}
        )
        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"valid": False}
        )

@app.get("/")
def root():
    return {"message": "Service is running", "email": STUDENT_EMAIL}