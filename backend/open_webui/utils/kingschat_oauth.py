"""
KingsChat OAuth Handler

KingsChat uses a custom OAuth2 flow that differs from standard OIDC:
1. Login URL: Direct redirect with query params (no OIDC discovery)
2. Callback: POST with accessToken/refreshToken in form data (not auth code)
3. Profile: Separate API call to fetch user info

Environment Variables:
- KINGSCHAT_CLIENT_ID: Your KingsChat client ID (e.g., "com.kingschat")
- KINGSCHAT_LOGIN_URL: OAuth login URL (default: "https://accounts.kingsch.at")
- KINGSCHAT_API_URL: API base URL (default: "https://api.kingsch.at")
- KINGSCHAT_REDIRECT_URI: Your callback URL
- KINGSCHAT_SCOPES: JSON array of scopes (default: '["conference_calls"]')
"""

import logging
import sys
import uuid
import time
import datetime
from urllib.parse import urlencode, quote

import aiohttp
from fastapi import HTTPException, Request, status
from starlette.responses import RedirectResponse, Response

from open_webui.models.auths import Auths
from open_webui.models.users import Users
from open_webui.config import (
    KINGSCHAT_CLIENT_ID,
    KINGSCHAT_LOGIN_URL,
    KINGSCHAT_API_URL,
    KINGSCHAT_REDIRECT_URI,
    KINGSCHAT_SCOPES,
    DEFAULT_USER_ROLE,
    ENABLE_OAUTH_SIGNUP,
    OAUTH_MERGE_ACCOUNTS_BY_EMAIL,
    WEBHOOK_URL,
    JWT_EXPIRES_IN,
)
from open_webui.constants import ERROR_MESSAGES, WEBHOOK_MESSAGES
from open_webui.env import (
    AIOHTTP_CLIENT_SESSION_SSL,
    WEBUI_NAME,
    WEBUI_AUTH_COOKIE_SAME_SITE,
    WEBUI_AUTH_COOKIE_SECURE,
    SRC_LOG_LEVELS,
    GLOBAL_LOG_LEVEL,
)
from open_webui.utils.misc import parse_duration
from open_webui.utils.auth import get_password_hash, create_token
from open_webui.utils.webhook import post_webhook

logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("OAUTH", logging.INFO))


class KingsChatOAuth:
    """Handler for KingsChat OAuth authentication."""

    PROFILE_ENDPOINT = "/developer/api/profile"

    def __init__(self, app=None):
        self.app = app

    def is_enabled(self) -> bool:
        """Check if KingsChat OAuth is configured."""
        return bool(KINGSCHAT_CLIENT_ID.value)

    def get_login_url(self, redirect_uri: str, next_url: str = "/") -> str:
        """
        Build the KingsChat OAuth login URL.

        Args:
            redirect_uri: The callback URL for OAuth
            next_url: Where to redirect after successful auth

        Returns:
            The full OAuth login URL
        """
        base_url = KINGSCHAT_LOGIN_URL.value.rstrip("/")
        client_id = KINGSCHAT_CLIENT_ID.value
        scopes = KINGSCHAT_SCOPES.value

        # Build callback URL with next parameter
        callback_url = f"{redirect_uri}?next={quote(next_url)}"

        # KingsChat requires these specific parameters
        params = {
            "client_id": client_id,
            "post_redirect": "true",  # Enable POST callback
            "redirect_uri": callback_url,
        }

        # Add scopes - KingsChat expects them as a query param value
        # Format: scopes=["conference_calls"]
        login_url = f"{base_url}/?{urlencode(params)}&scopes={scopes}"

        log.debug(f"KingsChat login URL: {login_url}")
        return login_url

    async def handle_login(self, request: Request) -> RedirectResponse:
        """
        Initiate KingsChat OAuth login flow.

        Redirects user to KingsChat login page.
        """
        if not self.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KingsChat OAuth is not configured",
            )

        # Determine redirect URI
        redirect_uri = KINGSCHAT_REDIRECT_URI.value
        if not redirect_uri:
            # Auto-generate redirect URI from request
            redirect_uri = str(request.url_for("kingschat_callback"))

        # Get the 'next' parameter for where to go after auth
        next_url = request.query_params.get("next", "/")

        login_url = self.get_login_url(redirect_uri, next_url)
        return RedirectResponse(url=login_url)

    async def fetch_user_profile(self, access_token: str) -> dict:
        """
        Fetch user profile from KingsChat API.

        Args:
            access_token: The KingsChat access token

        Returns:
            Normalized user profile dict

        Raises:
            HTTPException: If profile fetch fails
        """
        api_url = KINGSCHAT_API_URL.value.rstrip("/")
        profile_url = f"{api_url}{self.PROFILE_ENDPOINT}"

        try:
            async with aiohttp.ClientSession(trust_env=True) as session:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
                async with session.get(
                    profile_url, headers=headers, ssl=AIOHTTP_CLIENT_SESSION_SSL
                ) as resp:
                    if not resp.ok:
                        error_text = await resp.text()
                        log.error(
                            f"KingsChat profile fetch failed: {resp.status} - {error_text}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Failed to fetch KingsChat profile",
                        )

                    data = await resp.json()

                    # Profile data might be nested under 'profile' key or at root
                    profile = data.get("profile", data)

                    # Normalize the profile data
                    return {
                        "id": profile.get("id"),
                        "username": profile.get("username"),
                        "email": profile.get("email", "").lower() if profile.get("email") else None,
                        "phone": profile.get("phone_number") or profile.get("phone", ""),
                        "first_name": profile.get("first_name") or (profile.get("name", "").split(" ")[0] if profile.get("name") else ""),
                        "last_name": profile.get("last_name") or (" ".join(profile.get("name", "").split(" ")[1:]) if profile.get("name") else ""),
                        "name": profile.get("name") or f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                        "avatar": profile.get("avatar") or profile.get("profile_picture", ""),
                    }

        except aiohttp.ClientError as e:
            log.error(f"KingsChat API connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to KingsChat API",
            )

    async def handle_callback(
        self, request: Request, response: Response
    ) -> RedirectResponse:
        """
        Handle KingsChat OAuth callback.

        KingsChat POSTs accessToken and refreshToken in form data.

        Args:
            request: The incoming request with form data
            response: Response object for setting cookies

        Returns:
            Redirect response to frontend with JWT token
        """
        if not self.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KingsChat OAuth is not configured",
            )

        try:
            # KingsChat sends tokens as form data in POST
            form_data = await request.form()
            access_token = form_data.get("accessToken")
            refresh_token = form_data.get("refreshToken")

            if not access_token:
                log.warning("KingsChat callback: No access token received")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received from KingsChat",
                )

            log.debug(f"KingsChat callback: Received access token")

            # Fetch user profile from KingsChat API
            profile = await self.fetch_user_profile(access_token)

            if not profile.get("id"):
                log.warning("KingsChat callback: No user ID in profile")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid KingsChat profile data",
                )

            # Create provider sub identifier
            provider_sub = f"kingschat@{profile['id']}"
            email = profile.get("email")
            username = profile.get("username", "")
            name = profile.get("name") or username or email or "KingsChat User"

            # Check if user exists by OAuth sub
            user = Users.get_user_by_oauth_sub(provider_sub)

            if not user and OAUTH_MERGE_ACCOUNTS_BY_EMAIL.value and email:
                # Try to find by email and link accounts
                user = Users.get_user_by_email(email)
                if user:
                    Users.update_user_oauth_sub_by_id(user.id, provider_sub)
                    log.info(f"Linked KingsChat account to existing user: {email}")

            if not user:
                # User doesn't exist, check if signup is enabled
                if not ENABLE_OAUTH_SIGNUP.value:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
                    )

                # Check for email uniqueness
                if email:
                    existing_user = Users.get_user_by_email(email)
                    if existing_user:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ERROR_MESSAGES.EMAIL_TAKEN,
                        )

                # Create email from username if not provided
                if not email:
                    email = f"{username}@kingschat.local"

                # Determine role
                user_count = Users.get_num_users()
                role = "admin" if user_count == 0 else DEFAULT_USER_ROLE.value

                # Get profile picture
                picture_url = profile.get("avatar", "/user.png") or "/user.png"

                # Create new user
                user = Auths.insert_new_auth(
                    email=email,
                    password=get_password_hash(str(uuid.uuid4())),
                    name=name,
                    profile_image_url=picture_url,
                    role=role,
                    oauth_sub=provider_sub,
                )

                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=ERROR_MESSAGES.CREATE_USER_ERROR,
                    )

                log.info(f"Created new user from KingsChat: {email}")

                # Send webhook notification
                if WEBHOOK_URL.value:
                    post_webhook(
                        WEBUI_NAME,
                        WEBHOOK_URL.value,
                        WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                        {
                            "action": "signup",
                            "message": WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                            "user": user.model_dump_json(exclude_none=True),
                        },
                    )

            # Generate JWT token
            jwt_token = create_token(
                data={"id": user.id},
                expires_delta=parse_duration(JWT_EXPIRES_IN.value),
            )

            # Set JWT cookie
            response.set_cookie(
                key="token",
                value=jwt_token,
                httponly=True,
                samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                secure=WEBUI_AUTH_COOKIE_SECURE,
            )

            # Store KingsChat tokens in cookies (optional, for API calls)
            response.set_cookie(
                key="kingschat_token",
                value=access_token,
                httponly=True,
                samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                secure=WEBUI_AUTH_COOKIE_SECURE,
                max_age=60 * 30,  # 30 minutes
            )

            if refresh_token:
                response.set_cookie(
                    key="kingschat_refresh_token",
                    value=refresh_token,
                    httponly=True,
                    samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                    secure=WEBUI_AUTH_COOKIE_SECURE,
                    max_age=60 * 60 * 24 * 365,  # 1 year
                )

            # Get the next URL from query params
            next_url = request.query_params.get("next", "/")

            # Build redirect URL
            redirect_base_url = str(
                request.app.state.config.WEBUI_URL or request.base_url
            )
            if redirect_base_url.endswith("/"):
                redirect_base_url = redirect_base_url[:-1]

            # Redirect to frontend with token
            redirect_url = f"{redirect_base_url}/auth#token={jwt_token}"

            log.info(f"KingsChat login successful for user: {user.email}")
            return RedirectResponse(
                url=redirect_url,
                headers=response.headers,
                status_code=status.HTTP_303_SEE_OTHER,
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"KingsChat callback error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process KingsChat authentication",
            )


# Global instance
kingschat_oauth = KingsChatOAuth()

