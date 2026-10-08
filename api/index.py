from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA = [
    {"region": "apac", "service": "recommendations", "latency_ms": 123.46, "uptime_pct": 97.851, "timestamp": 20250301},
    {"region": "apac", "service": "recommendations", "latency_ms": 202.37, "uptime_pct": 98.301, "timestamp": 20250302},
    {"region": "apac", "service": "support", "latency_ms": 175.27, "uptime_pct": 98.135, "timestamp": 20250303},
    {"region": "apac", "service": "recommendations", "latency_ms": 143.59, "uptime_pct": 97.104, "timestamp": 20250304},
    {"region": "apac", "service": "support", "latency_ms": 174.68, "uptime_pct": 98.595, "timestamp": 20250305},
    {"region": "apac", "service": "support", "latency_ms": 110.94, "uptime_pct": 98.631, "timestamp": 20250306},
    {"region": "apac", "service": "payments", "latency_ms": 227.08, "uptime_pct": 98.614, "timestamp": 20250307},
    {"region": "apac", "service": "payments", "latency_ms": 203.96, "uptime_pct": 97.322, "timestamp": 20250308},
    {"region": "apac", "service": "checkout", "latency_ms": 113.73, "uptime_pct": 98.442, "timestamp": 20250309},
    {"region": "apac", "service": "catalog", "latency_ms": 174.43, "uptime_pct": 98.059, "timestamp": 20250310},
    {"region": "apac", "service": "recommendations", "latency_ms": 159.95, "uptime_pct": 97.945, "timestamp": 20250311},
    {"region": "apac", "service": "support", "latency_ms": 196.87, "uptime_pct": 97.265, "timestamp": 20250312},

    {"region": "emea", "service": "support", "latency_ms": 179.92, "uptime_pct": 97.297, "timestamp": 20250301},
    {"region": "emea", "service": "recommendations", "latency_ms": 194.85, "uptime_pct": 98.911, "timestamp": 20250302},
    {"region": "emea", "service": "checkout", "latency_ms": 182.90, "uptime_pct": 98.746, "timestamp": 20250303},
    {"region": "emea", "service": "payments", "latency_ms": 228.65, "uptime_pct": 97.548, "timestamp": 20250304},
    {"region": "emea", "service": "catalog", "latency_ms": 195.19, "uptime_pct": 98.304, "timestamp": 20250305},
    {"region": "emea", "service": "support", "latency_ms": 133.15, "uptime_pct": 97.880, "timestamp": 20250306},
    {"region": "emea", "service": "recommendations", "latency_ms": 202.88, "uptime_pct": 97.185, "timestamp": 20250307},
    {"region": "emea", "service": "checkout", "latency_ms": 118.05, "uptime_pct": 99.320, "timestamp": 20250308},
    {"region": "emea", "service": "catalog", "latency_ms": 129.94, "uptime_pct": 98.805, "timestamp": 20250309},
    {"region": "emea", "service": "payments", "latency_ms": 143.42, "uptime_pct": 98.549, "timestamp": 20250310},
    {"region": "emea", "service": "support", "latency_ms": 195.90, "uptime_pct": 97.193, "timestamp": 20250311},
    {"region": "emea", "service": "recommendations", "latency_ms": 213.94, "uptime_pct": 98.308, "timestamp": 20250312},

    {"region": "amer", "service": "recommendations", "latency_ms": 137.90, "uptime_pct": 99.367, "timestamp": 20250301},
    {"region": "amer", "service": "recommendations", "latency_ms": 135.85, "uptime_pct": 99.160, "timestamp": 20250302},
    {"region": "amer", "service": "support", "latency_ms": 233.66, "uptime_pct": 99.027, "timestamp": 20250303},
    {"region": "amer", "service": "recommendations", "latency_ms": 203.41, "uptime_pct": 98.271, "timestamp": 20250304},
    {"region": "amer", "service": "support", "latency_ms": 221.36, "uptime_pct": 98.473, "timestamp": 20250305},
    {"region": "amer", "service": "support", "latency_ms": 124.15, "uptime_pct": 99.027, "timestamp": 20250306},
    {"region": "amer", "service": "payments", "latency_ms": 195.01, "uptime_pct": 98.188, "timestamp": 20250307},
    {"region": "amer", "service": "payments", "latency_ms": 206.17, "uptime_pct": 97.365, "timestamp": 20250308},
    {"region": "amer", "service": "checkout", "latency_ms": 123.31, "uptime_pct": 99.100, "timestamp": 20250309},
    {"region": "amer", "service": "catalog", "latency_ms": 221.29, "uptime_pct": 98.703, "timestamp": 20250310},
    {"region": "amer", "service": "recommendations", "latency_ms": 199.18, "uptime_pct": 98.702, "timestamp": 20250311},
    {"region": "amer", "service": "support", "latency_ms": 119.63, "uptime_pct": 99.127, "timestamp": 20250312},
]


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, percentile):
    values = sorted(values)

    if not values:
        return 0.0

    position = (len(values) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    return values[lower] + (values[upper] - values[lower]) * (
        position - lower
    )


@app.post("/")
def analytics(request: AnalyticsRequest):
    results = []

    for region in request.regions:
        rows = [
            row for row in DATA
            if row["region"] == region
        ]

        latencies = [
            row["latency_ms"]
            for row in rows
        ]

        uptimes = [
            row["uptime_pct"]
            for row in rows
        ]

        if not rows:
            results.append({
                "region": region,
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            })
            continue

        results.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for value in latencies
                if value > request.threshold_ms
            )
        })

    return {"results": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )

    