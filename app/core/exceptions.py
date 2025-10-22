"""
Custom exception classes
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception"""
    def __init__(self, detail: str, status_code: int = 400, error_code: str = "APP_ERROR"):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(AppException):
    """Authentication related errors"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_ERROR"
        )


class AuthorizationError(AppException):
    """Authorization related errors"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class NotFoundError(AppException):
    """Resource not found errors"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )


class ValidationError(AppException):
    """Validation related errors"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )


class DocumentProcessingError(AppException):
    """Document processing errors"""
    def __init__(self, detail: str = "Failed to process document"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DOC_PROCESSING_ERROR"
        )


class PaymentError(AppException):
    """Payment related errors"""
    def __init__(self, detail: str = "Payment processing failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="PAYMENT_ERROR"
        )
