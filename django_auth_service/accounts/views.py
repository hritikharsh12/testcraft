import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger("accounts")


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        logger.info("user_registered username=%s", request.data.get("username"))
        return response


class LoginView(TokenObtainPairView):
    """
    Issues a short-lived access token + a refresh token on valid credentials.
    Rate-limited to blunt credential-stuffing / brute-force attempts.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RefreshView(TokenRefreshView):
    """
    Exchanges a valid, non-blacklisted refresh token for a new access token
    AND a new refresh token (rotation is enabled in settings). The old
    refresh token is blacklisted the moment this succeeds.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"


class LogoutView(APIView):
    """
    Client sends its current refresh token; we blacklist it immediately so
    it can't be replayed even if it leaks afterward. Access tokens are
    short-lived by design, so we don't try to revoke those individually.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (KeyError, TokenError):
            return Response({"detail": "Invalid or missing refresh token."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info("user_logout username=%s", request.user.username)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
