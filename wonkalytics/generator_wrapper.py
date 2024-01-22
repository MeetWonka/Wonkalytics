from copy import deepcopy
import wonkalytics.openai_wrapper as openai_wrapper
from .analytics import wonkalytics_and_promptlayer_api_request

def get_api_key():
    # raise an error if the api key is not set
    if openai_wrapper.api_key is None:
        raise Exception(
            "Please set your PROMPTLAYER_API_KEY environment variable or set API KEY in code using 'promptlayer.api_key = <your_api_key>' "
        )
    else:
        return openai_wrapper.api_key



class GeneratorWrapper:
    """
    A proxy wrapper for generators, facilitating both synchronous and asynchronous iterations,
    and handling API responses for analytics logging and result processing.
    """

    def __init__(self, generator, api_request_arguments):
        """
        Initializes the GeneratorProxy with a generator and API request arguments.

        Args:
            generator: The generator to be wrapped.
            api_request_arguments (dict): Arguments for API requests.
        """
        self.generator = generator
        self.results = []
        self.api_request_arguments = api_request_arguments

    def __iter__(self):
        """ Returns the iterator object itself for synchronous iteration. """
        return self

    def __aiter__(self):
        """ Returns the iterator object itself for asynchronous iteration. """
        return self

    async def __anext__(self):
        """ Retrieves the next item asynchronously from the generator. """
        result = await self.generator.__anext__()
        return self._overridden_next(result)

    def __next__(self):
        """ Retrieves the next item synchronously from the generator. """
        result = next(self.generator)
        return self._overridden_next(result)

    def _overridden_next(self, result):
        """
        Processes the result, appends it to results, and handles analytics logging.

        Args:
            result: The result obtained from the generator.

        Returns:
            The processed result, optionally alongside a request ID.
        """
        # Storing the result
        self.results.append(result)

        # Analytics handling based on provider type
        provider_type = self.api_request_arguments["provider_type"]
        end_condition_met = provider_type == "openai" and (
            result.choices[0].finish_reason in ["stop", "length"]
        )

        if end_condition_met:
            # Perform analytics API request if conditions are met
            request_id = self._perform_analytics_request()
            if self.api_request_arguments["return_pl_id"]:
                return result, request_id

        # Return result with or without request ID
        return result if not self.api_request_arguments["return_pl_id"] else (result, None)

    def _perform_analytics_request(self):
        """
        Performs an analytics request based on the gathered results and API arguments.

        Returns:
            The request ID from the analytics request.
        """
        # Processing the accumulated results for analytics request
        cleaned_result = self.clean_chunk()
        return wonkalytics_and_promptlayer_api_request(
            self.api_request_arguments["function_name"],
            self.api_request_arguments["provider_type"],
            self.api_request_arguments["args"],
            self.api_request_arguments["kwargs"],
            self.api_request_arguments["tags"],
            cleaned_result,
            self.api_request_arguments["request_start_time"],
            self.api_request_arguments["request_end_time"],
            get_api_key(),
            return_pl_id=self.api_request_arguments["return_pl_id"],
        )

    def clean_chunk(self):
        """
        Cleans and combines the accumulated results into a single response.

        Returns:
            The combined response from the results.
        """        
        # Check if the response is completion with delta
        if hasattr(self.results[0].choices[0], "delta"):
            return self._combine_delta_responses()

        # Return an empty string if no recognizable response type
        return ""


    def _combine_delta_responses(self):
        """ Combines delta responses into a single response object. """
        response = {"role": "", "content": ""}
        for result in self.results:
            delta = result.choices[0].delta
            if hasattr(delta, "role") and delta.role:
                response["role"] = delta.role
            if hasattr(delta, "content") and delta.content:
                response["content"] += delta.content
        final_result = deepcopy(self.results[-1])
        final_result.choices[0] = response
        return final_result
