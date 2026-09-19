import logging
import time
import uuid

logger = logging.getLogger("core.middleware")


class RequestLoggingMiddleware:
    """
    Logs every request with a correlation id, method, path, status code,
    duration, and the authenticated user if any. Never logs request bodies
    or headers directly, since those can contain passwords/tokens.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        user = getattr(request, "user", None)
        user_label = user.username if getattr(user, "is_authenticated", False) else "anonymous"

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s user=%s",
            request_id, request.method, request.path,
            response.status_code, duration_ms, user_label,
        )
        response["X-Request-ID"] = request_id
        return response
