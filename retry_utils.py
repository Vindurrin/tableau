#!/usr/bin/env python3
"""
Retry utilities for Tableau Server API calls.

Provides decorators and utilities for handling transient failures
in Tableau Server REST API operations including network timeouts,
rate limiting, and temporary server errors.
"""

import time
import random
from functools import wraps
from typing import Callable, Tuple, Type, Union, List
import tableauserverclient as TSC
from logger import get_logger

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0

# Retryable exception types
RETRYABLE_EXCEPTIONS = (
    TSC.ServerResponseError,
    ConnectionError,
    TimeoutError,
    # Add more specific exceptions as needed
)

logger = get_logger("retry_utils")

def exponential_backoff(attempt: int, 
                       base_delay: float = DEFAULT_BASE_DELAY,
                       max_delay: float = DEFAULT_MAX_DELAY, 
                       multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
                       jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay with optional jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Backoff multiplier
        jitter: Whether to add random jitter
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (multiplier ** attempt)
    delay = min(delay, max_delay)
    
    if jitter:
        # Add ±25% jitter to avoid thundering herd
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay

def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception is retryable.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the exception is retryable
    """
    # Check exception type
    if isinstance(exception, RETRYABLE_EXCEPTIONS):
        # For TSC.ServerResponseError, check specific conditions
        if isinstance(exception, TSC.ServerResponseError):
            # Retry on server errors (5xx) and rate limiting (429)
            if hasattr(exception, 'code'):
                return exception.code in [429, 500, 502, 503, 504]
            # If no code, check error message for common retryable patterns
            error_msg = str(exception).lower()
            retryable_patterns = [
                "timeout", "connection", "rate limit", "server error",
                "service unavailable", "internal server error"
            ]
            return any(pattern in error_msg for pattern in retryable_patterns)
        
        return True
    
    return False

def retry_api_call(max_retries: int = DEFAULT_MAX_RETRIES,
                  base_delay: float = DEFAULT_BASE_DELAY,
                  max_delay: float = DEFAULT_MAX_DELAY,
                  backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
                  retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS):
    """
    Decorator for retrying Tableau Server API calls.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_multiplier: Exponential backoff multiplier
        retryable_exceptions: Tuple of exception types to retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    if attempt > 0:
                        logger.info(
                            f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries + 1})",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_retries + 1
                        )
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} on attempt {attempt + 1}",
                            function=func.__name__,
                            successful_attempt=attempt + 1
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt >= max_retries or not is_retryable_error(e):
                        logger.error(
                            f"Final failure for {func.__name__}: {str(e)}",
                            function=func.__name__,
                            attempt=attempt + 1,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            retryable=is_retryable_error(e)
                        )
                        raise e
                    
                    # Calculate delay and wait
                    delay = exponential_backoff(attempt, base_delay, max_delay, backoff_multiplier)
                    
                    logger.warning(
                        f"Retryable error in {func.__name__}: {str(e)}. Retrying in {delay:.2f}s",
                        function=func.__name__,
                        attempt=attempt + 1,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_delay_seconds=delay
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator

class RetryableTableauOperation:
    """
    Context manager for retryable Tableau Server operations.
    
    Useful for complex operations that need retry logic but don't
    fit well with the decorator pattern.
    """
    
    def __init__(self, 
                 operation_name: str,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 base_delay: float = DEFAULT_BASE_DELAY):
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt = 0
        self.logger = get_logger("retryable_operation")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and is_retryable_error(exc_val):
            if self.attempt < self.max_retries:
                delay = exponential_backoff(self.attempt, self.base_delay)
                self.logger.warning(
                    f"Retryable error in {self.operation_name}: {str(exc_val)}. "
                    f"Will retry in {delay:.2f}s (attempt {self.attempt + 1}/{self.max_retries})",
                    operation=self.operation_name,
                    attempt=self.attempt + 1,
                    error_type=exc_type.__name__,
                    retry_delay_seconds=delay
                )
                time.sleep(delay)
                self.attempt += 1
                return True  # Suppress the exception
        
        # Don't suppress non-retryable errors or final failures
        return False
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if operation should be retried."""
        return (self.attempt < self.max_retries and 
                is_retryable_error(exception))

# Pre-configured decorators for common scenarios
tableau_api_retry = retry_api_call(max_retries=3, base_delay=1.0)
tableau_auth_retry = retry_api_call(max_retries=2, base_delay=0.5)  # Faster retry for auth
tableau_heavy_retry = retry_api_call(max_retries=5, base_delay=2.0, max_delay=60.0)  # More patient for heavy operations

if __name__ == "__main__":
    # Test the retry utilities
    @tableau_api_retry
    def test_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise TSC.ServerResponseError("Test server error", 500, None)
        return "Success!"
    
    try:
        result = test_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Final error: {e}")