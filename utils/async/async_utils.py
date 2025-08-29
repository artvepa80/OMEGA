# utils/async_utils.py
"""
Async utilities for safe event loop handling across the OMEGA system
Prevents "Cannot run the event loop while another loop is running" errors
"""

import asyncio
import logging
import threading
from typing import Any, Awaitable, Callable, Optional
from concurrent.futures import ThreadPoolExecutor
import functools

logger = logging.getLogger(__name__)

class AsyncExecutionManager:
    """Manages async execution patterns safely across the system"""
    
    def __init__(self):
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async-executor")
    
    def is_event_loop_running(self) -> bool:
        """Check if an event loop is currently running"""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    def safe_run_async(self, coro_or_future: Awaitable[Any]) -> Any:
        """
        Safely run async code regardless of current event loop state
        
        Args:
            coro_or_future: Coroutine or future to execute
            
        Returns:
            Result of the async operation
        """
        if self.is_event_loop_running():
            # Running from within an event loop - use thread pool
            logger.debug("🔄 Event loop detected, executing in thread pool")
            future = self._thread_pool.submit(self._run_in_new_thread, coro_or_future)
            return future.result()
        else:
            # No event loop running - safe to use asyncio.run
            logger.debug("🔄 No event loop, using asyncio.run()")
            return asyncio.run(coro_or_future)
    
    def _run_in_new_thread(self, coro_or_future: Awaitable[Any]) -> Any:
        """Run coroutine in a new thread with its own event loop"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(coro_or_future)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    
    async def safe_await(self, coro_or_future: Awaitable[Any]) -> Any:
        """
        Safe await that can be used in async contexts
        """
        return await coro_or_future
    
    def create_sync_wrapper(self, async_func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
        """
        Create a synchronous wrapper for an async function
        
        Args:
            async_func: Async function to wrap
            
        Returns:
            Synchronous wrapper function
        """
        @functools.wraps(async_func)
        def sync_wrapper(*args, **kwargs):
            coro = async_func(*args, **kwargs)
            return self.safe_run_async(coro)
        
        return sync_wrapper
    
    def shutdown(self):
        """Clean shutdown of the async execution manager"""
        self._thread_pool.shutdown(wait=True)
        logger.debug("🔄 AsyncExecutionManager shutdown complete")

# Global instance for system-wide use
async_manager = AsyncExecutionManager()

def safe_run_async(coro_or_future: Awaitable[Any]) -> Any:
    """
    Global function for safe async execution
    
    Usage:
        # Instead of:
        result = asyncio.run(my_async_function())
        
        # Use:
        result = safe_run_async(my_async_function())
    """
    return async_manager.safe_run_async(coro_or_future)

def sync_wrapper(async_func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    """
    Decorator to create sync wrappers for async functions
    
    Usage:
        @sync_wrapper
        async def my_async_function():
            # async code here
            pass
        
        # Now can be called synchronously:
        result = my_async_function()
    """
    return async_manager.create_sync_wrapper(async_func)

async def safe_gather(*awaitables, return_exceptions: bool = False) -> list:
    """Safe version of asyncio.gather that works in any context"""
    if not awaitables:
        return []
    
    try:
        return await asyncio.gather(*awaitables, return_exceptions=return_exceptions)
    except Exception as e:
        logger.warning(f"⚠️ Error in safe_gather: {e}")
        if return_exceptions:
            return [e] * len(awaitables)
        raise

def is_async_context() -> bool:
    """Check if we're currently in an async context"""
    return async_manager.is_event_loop_running()

# Context manager for safe async execution
class AsyncContext:
    """Context manager for safe async operations"""
    
    def __init__(self, enable_logging: bool = True):
        self.enable_logging = enable_logging
        self._original_loop = None
    
    def __enter__(self):
        if self.enable_logging:
            logger.debug("🔄 Entering AsyncContext")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enable_logging:
            logger.debug("🔄 Exiting AsyncContext")
        if exc_type:
            logger.error(f"⚠️ AsyncContext error: {exc_val}")
    
    def run(self, coro_or_future: Awaitable[Any]) -> Any:
        """Run async code within this context"""
        return safe_run_async(coro_or_future)

def cleanup_async_resources():
    """Clean up global async resources"""
    async_manager.shutdown()
    logger.debug("🔄 Async resources cleaned up")

# Register cleanup on module exit
import atexit
atexit.register(cleanup_async_resources)