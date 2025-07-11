from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json

from ..services.i18n_service import i18n_service
from ..database import SessionLocal

class I18nMiddleware(BaseHTTPMiddleware):
    """Middleware to handle i18n for requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Get language from various sources
        language_code = await self._get_request_language(request)
        
        # Store language in request state
        request.state.language = language_code
        
        # Process request
        response = await call_next(request)
        
        # Add language header to response
        response.headers["Content-Language"] = language_code
        
        return response
    
    async def _get_request_language(self, request: Request) -> str:
        """Determine language from request"""
        # Priority order:
        # 1. Query parameter (?lang=ko)
        # 2. Header (Accept-Language)
        # 3. User preference (if authenticated)
        # 4. Default language
        
        # Check query parameter
        if "lang" in request.query_params:
            return request.query_params["lang"]
        
        # Check custom header
        if "X-Language" in request.headers:
            return request.headers["X-Language"]
        
        # Check Accept-Language header
        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            # Parse Accept-Language header
            languages = self._parse_accept_language(accept_language)
            if languages:
                return languages[0]
        
        # Check user preference if authenticated
        if hasattr(request.state, "user") and request.state.user:
            db = SessionLocal()
            try:
                user_lang = await i18n_service.get_user_language(
                    request.state.user.id,
                    db
                )
                return user_lang
            finally:
                db.close()
        
        # Return default
        return i18n_service.default_language
    
    def _parse_accept_language(self, accept_language: str) -> list:
        """Parse Accept-Language header"""
        languages = []
        
        for lang in accept_language.split(","):
            parts = lang.strip().split(";")
            if parts:
                # Extract language code
                lang_code = parts[0].split("-")[0].lower()
                languages.append(lang_code)
        
        return languages


def get_request_language(request: Request) -> str:
    """Helper function to get language from request"""
    return getattr(request.state, "language", i18n_service.default_language)