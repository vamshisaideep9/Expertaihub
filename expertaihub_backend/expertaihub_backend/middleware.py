import asyncio
from django.conf import settings
from django.http import HttpResponseServerError
from asgiref.sync import sync_to_async, iscoroutinefunction

class RequestTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, 'VIEW_TIMEOUT', 300)
        self._is_coroutine = iscoroutinefunction(get_response)

    def __call__(self, request):
        if self._is_coroutine:
            return self._async_call(request)
        return self._sync_call(request)

    def _sync_call(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            return HttpResponseServerError(f"Server error: {str(e)}")

    async def _async_call(self, request):
        try:
            # Create a task for the view
            view_task = asyncio.create_task(self.get_response(request))
            
            # Wait for the view to complete with timeout
            try:
                response = await asyncio.wait_for(view_task, timeout=self.timeout)
                return response
            except asyncio.TimeoutError:
                # If the view times out, cancel it and return an error
                view_task.cancel()
                return HttpResponseServerError(
                    "Request timed out. The server took too long to respond."
                )
        except Exception as e:
            # Handle any other exceptions
            return HttpResponseServerError(f"Server error: {str(e)}") 