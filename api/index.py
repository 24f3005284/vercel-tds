import time
import uuid
import json
import urllib.request
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, status, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt

app = FastAPI()

ALLOWED_ORIGIN_Q3 = "https://dash-oyxbjn.example.com"
STUDENT_EMAIL = "24f3005284@ds.study.iitm.ac.in"
ASSIGNED_API_KEY_Q7 = "ak_jphu7lkbdew9kedpwtnxuqo4"

# Upstash Redis REST config (Q6 persistence)
REDIS_URL = "https://wanted-herring-220319.upstash.io"
REDIS_TOKEN = "gQAAAAAAA1yfAQIgcDE5YjU5MDhjZWFiMjU0ZjY1ODgxOWVjZjM0MTMwZjY0NQ"

def redis_exec(*args):
    payload = json.dumps(args).encode("utf-8")
    req = urllib.request.Request(
        REDIS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {REDIS_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("result")

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
            # Allow cross-origin for all other endpoints including /analytics
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
    
    # Check API key before route processing for /analytics so missing/wrong key always returns 401
    if path == "/analytics":
        x_api_key = request.headers.get("x-api-key")
        if not x_api_key or x_api_key != ASSIGNED_API_KEY_Q7:
            res = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API Key"}
            )
            res.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            res.headers["X-Request-ID"] = str(uuid.uuid4())
            res.headers["X-Process-Time"] = "0.000100"
            return res

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
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    config["port"] = 8840
    config["debug"] = True
    config["port"] = 8122
    config["workers"] = 10
    config["debug"] = True
    config["api_key"] = "key-e3p0ajqk6v"
    
    query_params = request.query_params.multi_items()
    for param_key, param_val in query_params:
        if param_key == "set" and "=" in param_val:
            k, v = param_val.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "NUM_WORKERS":
                k = "workers"
            elif k.startswith("APP_"):
                sub = k[4:].lower()
                if sub in ("port", "workers", "debug", "log_level", "api_key"):
                    k = sub
            
            try:
                coerced = coerce_config_value(k, v)
                config[k] = coerced
            except Exception:
                config[k] = v
                
    result = {}
    for k in ("port", "workers", "debug", "log_level", "api_key"):
        if k in config:
            result[k] = coerce_config_value(k, config[k])
            
    for k, v in config.items():
        if k not in result and k != "NUM_WORKERS":
            result[k] = coerce_config_value(k, v)
            
    result["api_key"] = "****"
    return result


# --- Q6 Endpoints (Multi-Container / Redis persistence) ---
@app.post("/hit/{key}")
def hit_key(key: str):
    res = redis_exec("INCR", f"counter:{key}")
    return {"key": key, "count": int(res)}

@app.get("/count/{key}")
def get_count(key: str):
    res = redis_exec("GET", f"counter:{key}")
    if res is None:
        return {"key": key, "count": 0}
    return {"key": key, "count": int(res)}

@app.get("/healthz")
def healthz():
    try:
        ping_res = redis_exec("PING")
        if ping_res == "PONG":
            return {"status": "ok", "redis": "up"}
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "redis": "down"}
            )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "redis": "down"}
        )


# --- Q7 Endpoint (POST /analytics) ---
class EventItem(BaseModel):
    user: str
    amount: float
    ts: Optional[Any] = None

class AnalyticsBatchRequest(BaseModel):
    events: List[EventItem]

@app.post("/analytics")
def analytics_endpoint(
    req: AnalyticsBatchRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    if not x_api_key or x_api_key != ASSIGNED_API_KEY_Q7:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API Key"}
        )
    
    total_events = len(req.events)
    unique_users_set = set()
    total_revenue = 0.0
    user_positive_revenue: Dict[str, float] = {}
    
    for event in req.events:
        user = event.user
        unique_users_set.add(user)
        amt = event.amount
        if amt > 0:
            total_revenue += amt
            user_positive_revenue[user] = user_positive_revenue.get(user, 0.0) + amt
            
    if user_positive_revenue:
        top_user = max(user_positive_revenue.items(), key=lambda item: item[1])[0]
    else:
        top_user = ""
        
    return {
        "email": STUDENT_EMAIL,
        "total_events": total_events,
        "unique_users": len(unique_users_set),
        "revenue": round(total_revenue, 4),
        "top_user": top_user
    }


@app.get("/")
def root():
    return {"message": "Service is running", "email": STUDENT_EMAIL}