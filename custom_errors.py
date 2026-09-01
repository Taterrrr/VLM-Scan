class VLMError(Exception):
    """Base class for VLM-related errors."""
    pass


class MissingInputError(VLMError):
    """Raised when missing prompt or image for VLM input."""
    pass


class TooManyTablesError(VLMError):
    """Raised when VLM output contains too many tables."""
    pass


class RetryLimitExceededError(VLMError):
    """Raised when retry limit is exceeded."""
    pass

class NoResponseError(VLMError):
    """Raised when no response from VLM."""
    pass

class ClaimsNameError(VLMError):
    """Raised when "claims" is misspelled"."""
    pass

class NotDictError(VLMError):
    """Raised when answer is not a dict."""
    pass

class KeysNameError(VLMError):
    """Raised when claims keys are incorrectly named."""
    pass