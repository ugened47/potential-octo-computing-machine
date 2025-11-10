"""Rate limiting middleware."""

from collections.abc import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(
        self,
        app: Callable,
        calls: int = 100,
        period: int = 60,
        key_func: Callable[[Request], str] | None = None,
    ):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            calls: Number of allowed calls per period
            period: Time period in seconds
            key_func: Function to generate rate limit key from request
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        """Generate default rate limit key from request.

        Args:
            request: FastAPI request

        Returns:
            Rate limit key
        """
        # Use user ID if authenticated, otherwise use IP address
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"rate_limit:user:{user_id}"
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:ip:{client_ip}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware handler

        Returns:
            Response
        """
        # Skip rate limiting for health check and static files
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        try:
            redis_client = await get_redis_client()
            key = self.key_func(request)

            # Get current count
            current = await redis_client.get(key)
            if current is None:
                # First request in period
                await redis_client.setex(key, self.period, "1")
                return await call_next(request)

            count = int(current)
            if count >= self.calls:
                # Rate limit exceeded
                return Response(
                    content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded"}}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(self.period),
                    },
                )

            # Increment count
            await redis_client.incr(key)
            remaining = self.calls - count - 1

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response
        except Exception:
            # If Redis fails, allow request (graceful degradation)
            return await call_next(request)
