import time
import uuid
from typing import Optional, List
from fastapi import FastAPI, Request, Response, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt

app = FastAPI()

ALLOWED_ORIGIN_Q3 = "https://dash-oyxbjn.example.com"
STUDENT_EMAIL = "24f3005284@ds.study.iitm.ac.in"

# OIDC Verification Config (Q4)
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

# Custom CORS and Headers Middleware
# Handles strict origin for Q3 /stats, and open CORS for Q5 /effective-config and others
@app.middleware("http")
async def main_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    path = request.url.path
    
    # Handle preflight OPTIONS
    if request.method == "OPTIONS":
        start_time = time.perf_counter()
        if path == "/stats":
            if origin == ALLOWED_ORIGIN_Q3:
                res = Response(content="OK", status_code=200)
                res.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN_Q3
                res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
                res.headers["Access-Control-Allow-Headers"] = "*"
                res.headers["Access-Control-Allow-Credentials"] = "true"
            else:
                res = Response(content="Disallowed CORS origin", status_code=400)
        else:
            # For other routes including /effective-config, allow cross-origin
            res = Response(content="OK", status_code=200)
            if origin:
                res.headers["Access-Control-Allow-Origin"] = origin
            else:
                res.headers["Access-Control-Allow-Origin"] = "*"
            res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
            res.headers["Access-Control-Allow-Headers"] = "*"
            res.headers["Access-Control-Allow-Credentials"] = "true"
        
        process_time = time.perf_counter() - start_time
        res.headers["X-Request-ID"] = str(uuid.uuid4())
        res.headers["X-Process-Time"] = f"{process_time:.6f}"
        return res
    
    # Normal requests
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start_time
    
    # Add timing and request-id
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    # CORS headers for response
    if path == "/stats":
        if origin == ALLOWED_ORIGIN_Q3:
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN_Q3
            response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
            
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
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"valid": False}
        )


# --- Q5 Endpoint (12-Factor Config Precedence) ---
def coerce_config_value(key: str, val):
    if key in ("port", "workers"):
        return int(val)
    elif key == "debug":
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        return s in ("true", "1", "yes", "on")
    else:
        return str(val)

@app.get("/effective-config")
def effective_config(request: Request):
    # Layer 1: defaults (hardcoded)
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    
    # Layer 2: config.development.yaml
    # port: 8840, debug: true
    config["port"] = 8840
    config["debug"] = True
    
    # Layer 3: .env file
    # APP_PORT=8122, NUM_WORKERS=10 (alias NUM_WORKERS -> workers)
    config["port"] = 8122
    config["workers"] = 10
    
    # Layer 4: OS env vars (APP_* prefix)
    # APP_DEBUG=true, APP_API_KEY=key-e3p0ajqk6v
    config["debug"] = True
    config["api_key"] = "key-e3p0ajqk6v"
    
    # Layer 5: CLI overrides passed via ?set=key=value query parameters
    query_params = request.query_params.multi_items()
    for param_key, param_val in query_params:
        if param_key == "set" and "=" in param_val:
            k, v = param_val.split("=", 1)
            k = k.strip()
            v = v.strip()
            # If alias is used in CLI override
            if k == "NUM_WORKERS":
                k = "workers"
            elif k.startswith("APP_"):
                # Handle potential APP_ prefix
                sub = k[4:].lower()
                if sub in ("port", "workers", "debug", "log_level", "api_key"):
                    k = sub
            
            try:
                coerced = coerce_config_value(k, v)
                config[k] = coerced
            except Exception:
                config[k] = v
                
    # Final type coercion pass for standard keys
    result = {}
    for k in ("port", "workers", "debug", "log_level", "api_key"):
        if k in config:
            result[k] = coerce_config_value(k, config[k])
            
    # Also include any extra custom keys if passed via ?set=
    for k, v in config.items():
        if k not in result and k != "NUM_WORKERS":
            result[k] = coerce_config_value(k, v)
            
    # Secret masking: api_key must always appear as "****" in the response
    result["api_key"] = "****"
    
    return result


@app.get("/")
def root():
    return {"message": "Service is running", "email": STUDENT_EMAIL}