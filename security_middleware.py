#!/usr/bin/env python3
"""
Security Middleware for Agentic Research Engine
Enterprise-grade security controls and input validation
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import secrets
import html

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    max_request_size: int = 1048576  # 1MB
    rate_limit_per_minute: int = 100
    session_timeout: int = 1800  # 30 minutes
    min_password_length: int = 12
    require_https: bool = True
    csrf_token_length: int = 32
    
class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(\-\-)|(\#)|(/\*)|(\*/)",
        r"(union\s+select)|(or\s+1\s*=\s*1)|(drop\s+table)",
        r"(insert\s+into)|(update\s+.*set)|(delete\s+from)",
        r"(script\s*>)|(javascript:)|(vbscript:)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$\(\){}]",
        r"(rm\s+)|(sudo\s+)|(chmod\s+)",
        r"(wget\s+)|(curl\s+)|(nc\s+)",
    ]
    
    @classmethod
    def validate_sql_input(cls, value: str) -> bool:
        """Check for SQL injection patterns"""
        if not isinstance(value, str):
            return True
            
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected: {pattern}")
                return False
        return True
    
    @classmethod
    def validate_xss_input(cls, value: str) -> bool:
        """Check for XSS patterns"""
        if not isinstance(value, str):
            return True
            
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS attempt detected: {pattern}")
                return False
        return True
    
    @classmethod
    def validate_command_injection(cls, value: str) -> bool:
        """Check for command injection patterns"""
        if not isinstance(value, str):
            return True
            
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                logger.warning(f"Command injection attempt detected: {pattern}")
                return False
        return True
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML content"""
        if not isinstance(value, str):
            return value
        return html.escape(value)
    
    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate JSON structure against schema"""
        try:
            for field, field_type in schema.items():
                if field in data:
                    if not isinstance(data[field], field_type):
                        logger.warning(f"Invalid type for field {field}: expected {field_type}, got {type(data[field])}")
                        return False
            return True
        except Exception as e:
            logger.error(f"JSON validation error: {e}")
            return False
    
    @classmethod
    def validate_comprehensive(cls, value: str) -> bool:
        """Run all validation checks"""
        return (
            cls.validate_sql_input(value) and
            cls.validate_xss_input(value) and
            cls.validate_command_injection(value)
        )

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.clients = {}
        
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        if client_id not in self.clients:
            self.clients[client_id] = []
        
        # Remove old requests
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.clients[client_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False
        
        # Add current request
        self.clients[client_id].append(now)
        return True

class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token: str, expected_token: str) -> bool:
        """Validate CSRF token"""
        if not token or not expected_token:
            return False
        return secrets.compare_digest(token, expected_token)

class SessionManager:
    """Secure session management"""
    
    def __init__(self, timeout: int = 1800):
        self.timeout = timeout
        self.sessions = {}
    
    def create_session(self, user_id: str) -> str:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
        }
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session and return user_id if valid"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        now = datetime.utcnow()
        
        # Check timeout
        if (now - session['last_activity']).seconds > self.timeout:
            del self.sessions[session_id]
            return None
        
        # Update activity
        session['last_activity'] = now
        return session['user_id']
    
    def invalidate_session(self, session_id: str) -> None:
        """Invalidate session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

class SecurityHeaders:
    """Security headers management"""
    
    SECURITY_HEADERS = {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Get security headers"""
        return cls.SECURITY_HEADERS.copy()

class EncryptionUtils:
    """Encryption and hashing utilities"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 instead of weak hashing algorithms
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = EncryptionUtils.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

class SecurityMiddleware:
    """Main security middleware class"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute)
        self.session_manager = SessionManager(self.config.session_timeout)
        self.csrf = CSRFProtection()
        
    def validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive request validation"""
        errors = []
        
        # Check request size
        request_size = len(json.dumps(request_data).encode('utf-8'))
        if request_size > self.config.max_request_size:
            errors.append(f"Request size {request_size} exceeds limit {self.config.max_request_size}")
        
        # Validate all string inputs
        def validate_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    validate_recursive(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    validate_recursive(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                if not self.validator.validate_comprehensive(obj):
                    errors.append(f"Security validation failed for field: {path}")
        
        validate_recursive(request_data)
        
        if errors:
            return {'valid': False, 'errors': errors}
        return {'valid': True, 'errors': []}
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for response"""
        return SecurityHeaders.get_headers()
    
    def create_secure_session(self, user_id: str) -> Dict[str, str]:
        """Create secure session with CSRF token"""
        session_id = self.session_manager.create_session(user_id)
        csrf_token = self.csrf.generate_token()
        
        return {
            'session_id': session_id,
            'csrf_token': csrf_token
        }

# Security decorators
def require_validation(schema: Optional[Dict[str, Any]] = None):
    """Decorator for input validation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request data from kwargs or args
            request_data = kwargs.get('request_data') or (args[0] if args else {})
            
            if isinstance(request_data, dict):
                middleware = SecurityMiddleware()
                validation_result = middleware.validate_request(request_data)
                
                if not validation_result['valid']:
                    raise ValueError(f"Security validation failed: {validation_result['errors']}")
                
                if schema and not InputValidator.validate_json_structure(request_data, schema):
                    raise ValueError("JSON structure validation failed")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(requests_per_minute: int = 100):
    """Decorator for rate limiting"""
    def decorator(func):
        limiter = RateLimiter(requests_per_minute)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = kwargs.get('client_id', 'default')
            
            if not limiter.is_allowed(client_id):
                raise PermissionError(f"Rate limit exceeded for client {client_id}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_csrf():
    """Decorator for CSRF protection"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            csrf_token = kwargs.get('csrf_token')
            expected_token = kwargs.get('expected_csrf_token')
            
            if not CSRFProtection.validate_token(csrf_token, expected_token):
                raise PermissionError("CSRF token validation failed")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    # Test input validation
    validator = InputValidator()
    
    # Test SQL injection detection
    test_cases = [
        "SELECT * FROM users",  # Should fail
        "'; DROP TABLE users; --",  # Should fail
        "normal input",  # Should pass
        "<script>alert('xss')</script>",  # Should fail
        "rm -rf /",  # Should fail
    ]
    
    print("Security validation tests:")
    for test in test_cases:
        result = validator.validate_comprehensive(test)
        print(f"'{test}': {'PASS' if result else 'FAIL'}")
    
    # Test rate limiting
    limiter = RateLimiter(5)  # 5 requests per minute
    client_id = "test_client"
    
    print("\nRate limiting tests:")
    for i in range(7):
        allowed = limiter.is_allowed(client_id)
        print(f"Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'}")
    
    # Test session management
    session_mgr = SessionManager(10)  # 10 second timeout
    session_id = session_mgr.create_session("user123")
    print(f"\nSession created: {session_id}")
    print(f"Session valid: {session_mgr.validate_session(session_id)}")