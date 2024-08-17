
import time
from functools import wraps
from fastapi import Request, HTTPException, status


def rate_limiter(max_calls: int, time_frame: int):
    def decorator(func):
        calls = []
        
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            now = time.time()
            calls_in_time_frame = [call for call in calls if call > now - time_frame]
            if len(calls_in_time_frame) >= max_calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests."
                )
            calls.append(now)
            print(calls)
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator