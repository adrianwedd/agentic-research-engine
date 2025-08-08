"""Authentication module for Long-Term Memory (LTM) service."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Dict, Optional

from fastapi import Header, HTTPException, status


class LTMAuthenticator:
    """Secure authentication for LTM service using API keys and HMAC."""
    
    def __init__(self):
        """Initialize with API keys from environment."""
        api_keys_raw = os.getenv("LTM_API_KEYS")
        if not api_keys_raw:
            raise ValueError(
                "LTM_API_KEYS environment variable must be set. "
                "Format: 'service1:key1,service2:key2'"
            )
        self.api_keys = self._parse_api_keys(api_keys_raw)
        self.signing_key = os.getenv("LTM_SIGNING_KEY", secrets.token_urlsafe(32))
    
    def _parse_api_keys(self, raw: str) -> Dict[str, str]:
        """Parse and validate API keys."""
        mapping: Dict[str, str] = {}
        for pair in raw.split(","):
            if not pair.strip():
                continue
            try:
                service, key = pair.split(":", 1)
                service = service.strip()
                key = key.strip()
                
                # Security validation
                if len(key) < 32:
                    raise ValueError(f"API key for '{service}' is too short (minimum 32 characters)")
                if not service or not key:
                    raise ValueError("Service name and key cannot be empty")
                
                mapping[key] = service
            except ValueError as e:
                if "not enough values to unpack" in str(e):
                    raise ValueError(f"Invalid API key format in pair: {pair}")
                raise
        return mapping
    
    def authenticate(
        self, 
        authorization: str = Header(...),
        x_ltm_timestamp: Optional[str] = Header(None),
        x_ltm_signature: Optional[str] = Header(None)
    ) -> str:
        """
        Authenticate request using API key or HMAC signature.
        
        Returns the authenticated service name.
        """
        # Basic API key authentication
        if authorization.startswith("Bearer "):
            token = authorization.split()[1]
            if len(token) < 32:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )
            
            service = self.api_keys.get(token)
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            return service
        
        # HMAC signature authentication (for high-security operations)
        elif x_ltm_timestamp and x_ltm_signature:
            return self._verify_hmac_signature(
                authorization, x_ltm_timestamp, x_ltm_signature
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def _verify_hmac_signature(
        self, 
        authorization: str, 
        timestamp: str, 
        signature: str
    ) -> str:
        """Verify HMAC signature for enhanced security."""
        try:
            # Check timestamp (prevent replay attacks)
            request_time = float(timestamp)
            current_time = time.time()
            if abs(current_time - request_time) > 300:  # 5 minutes
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Request timestamp too old"
                )
            
            # Extract service from authorization header
            if not authorization.startswith("Service "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization format for HMAC"
                )
            
            service = authorization.split()[1]
            
            # Compute expected signature
            message = f"{service}:{timestamp}".encode()
            expected_signature = hmac.new(
                self.signing_key.encode(),
                message,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature"
                )
            
            return service
            
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC authentication"
            )


# Global authenticator instance
ltm_auth = LTMAuthenticator()


def get_authenticated_service(
    authorization: str = Header(...),
    x_ltm_timestamp: Optional[str] = Header(None),
    x_ltm_signature: Optional[str] = Header(None)
) -> str:
    """FastAPI dependency for LTM service authentication."""
    return ltm_auth.authenticate(authorization, x_ltm_timestamp, x_ltm_signature)


def require_service(allowed_services: list[str]):
    """Decorator to restrict access to specific services."""
    def dependency(service: str = get_authenticated_service) -> str:
        if service not in allowed_services:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Service '{service}' not authorized for this operation"
            )
        return service
    return dependency