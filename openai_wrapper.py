import datetime
import inspect
from utils import async_wrapper, get_api_key, wonkalytics_api_handler

class OpenAIWrapper(object):
    """
    Wraps OpenAI API objects for analytics and logging. It intercepts and processes function calls,
    allowing for data collection and additional function call handling.
    """

    def __init__(self, obj, function_name="", provider="openai"):
        """
        Initializes the wrapper with an object and optional metadata.
        
        Args:
            obj: The object to be wrapped.
            function_name (str): An optional name for the function being wrapped.
            provider (str): The provider type, defaulting to 'openai'.
        """
        object.__setattr__(self, "_obj", obj)
        object.__setattr__(self, "_function_name", function_name)
        object.__setattr__(self, "provider", provider)

    def __call__(self, *args, **kwargs):
        """
        Handles call to the wrapped object, adding analytics and logging functionalities.
        
        Args:
            *args: Positional arguments to pass to the function call.
            **kwargs: Keyword arguments to pass to the function call.
        
        Returns:
            The result of the function call, processed for analytics and logging.
        """
        # Process some tags
        tags = kwargs.pop("pl_tags", kwargs.pop("wl_tags", None))
        if tags is not None and not isinstance(tags, list):
            raise TypeError("Tags must be a list of strings.")

        return_pl_id = kwargs.pop("return_pl_id", kwargs.pop("return_wl_id", False))
        request_start_time = datetime.datetime.now().timestamp()

        # Accessing the actual object to be called
        wrapped_obj = object.__getattribute__(self, "_obj")
        # Handling instantiation if the object is a class
        if inspect.isclass(wrapped_obj):
            return OpenAIWrapper(
                wrapped_obj(*args, **kwargs),
                function_name=object.__getattribute__(self, "_function_name"),
                provider=object.__getattribute__(self, "provider"),
            )

        # Execute the function and handle the response
        response = wrapped_obj(*args, **kwargs)
        # If response is a coroutine, handle asynchronously
        if inspect.iscoroutine(response) or inspect.iscoroutinefunction(wrapped_obj):
            return async_wrapper(
                response, return_pl_id, request_start_time,
                object.__getattribute__(self, "_function_name"),
                object.__getattribute__(self, "provider"), tags, *args, **kwargs
            )

        # Handle synchronous function call
        request_end_time = datetime.datetime.now().timestamp()
        return wonkalytics_api_handler(
            object.__getattribute__(self, "_function_name"),
            object.__getattribute__(self, "provider"), args, kwargs, tags, response,
            request_start_time, request_end_time, get_api_key(), return_pl_id=return_pl_id
        )

    def __getattr__(self, name):
        """
        Retrieves the attribute from the wrapped object and wraps it if callable.
        
        Args:
            name (str): The name of the attribute to retrieve.
        
        Returns:
            The attribute from the wrapped object, possibly wrapped in another instance of WonkalyticsOpenAIWrapper.
        """
        # Get the actual attribute from the wrapped object
        attribute = getattr(object.__getattribute__(self, "_obj"), name)
        # Wrap callable attributes in another wrapper instance
        if name != "count_tokens" and (
            inspect.isclass(attribute) or inspect.isfunction(attribute) 
            or inspect.ismethod(attribute) or isinstance(attribute, object)):
            return OpenAIWrapper(
                attribute,
                function_name=f'{object.__getattribute__(self, "_function_name")}.{name}',
                provider=object.__getattribute__(self, "provider"),
            )
        # Return non-callable attributes directly
        return attribute

    def __setattr__(self, name, value):
        """
        Sets an attribute on the wrapped object.
        
        Args:
            name (str): The name of the attribute to set.
            value: The value to set for the attribute.
        """
        setattr(object.__getattribute__(self, "_obj"), name, value)

    def __delattr__(self, name):
        """
        Deletes an attribute from the wrapped object.
        
        Args:
            name (str): The name of the attribute to delete.
        """
        delattr(object.__getattribute__(self, "_obj"), name)
