from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from fastapi.responses import JSONResponse

audit = APIRouter(prefix="/audit", tags=["audit"])


# In-memory request counter by endpoint and IP address
request_counter = defaultdict(lambda: defaultdict(int))

# Middleware to track request counts and IP addresses
class RequestCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        ip_address = request.client.host
        request_counter[endpoint][ip_address] += 1
        response = await call_next(request)
        return response


# Endpoint to get request stats
@audit.get("/request-stats", response_class=JSONResponse)
async def get_request_stats():
    return {"request_counts": {endpoint: dict(ips) for endpoint, ips in request_counter.items()}}