from typing import Any


class TokenMonitor:
    """A monitor to track and validate LLM context token usage and detect Danger Zone (D-Zone) thresholds.
    Supports English and Vietnamese text token count estimation fallback.
    """

    def __init__(self, max_tokens: int = 128000) -> None:
        """Initialize the TokenMonitor with a max_tokens limit.

        Args:
            max_tokens: The maximum tokens allowed for the context. Must be a positive integer.

        Raises:
            TypeError: If max_tokens is not an integer.
            ValueError: If max_tokens is less than or equal to 0.
        """
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool):
            raise TypeError("max_tokens must be a positive integer")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than 0")

        self.max_tokens = max_tokens
        self._encoding = None
        self._tiktoken_failed = False

    def _get_string_tokens(self, text: str) -> int:
        """Encode the string to get token count, falling back to a Vietnamese-aware estimation if tiktoken fails."""
        if not text:
            return 0

        # Try to load tiktoken encoding
        if self._encoding is None and not self._tiktoken_failed:
            try:
                import tiktoken

                self._encoding = tiktoken.get_encoding("cl100k_base")
            except (ImportError, Exception):
                self._tiktoken_failed = True

        if self._encoding is not None:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass

        # Vietnamese-aware character/word fallback estimation
        is_ascii = True
        try:
            is_ascii = text.isascii()
        except AttributeError:
            is_ascii = all(ord(c) < 128 for c in text)

        if is_ascii:
            return max(len(text) // 4, int(len(text.split()) * 1.3))
        else:
            return max(int(len(text) * 0.7), int(len(text.split()) * 2.5))

    def get_context_token_count(self, messages: list[Any] | None = None) -> int:
        """Compute the total context token count for the given message list.

        Args:
            messages: A list of messages. Elements can be strings, dicts, or objects
                      with to_dict() or dict() methods.

        Returns:
            The total token count (integer).

        Raises:
            TypeError: If a message element cannot be converted to a dictionary or if
                       messages is not a list or tuple.
        """
        if messages is not None and not isinstance(messages, (list, tuple)):
            raise TypeError("messages must be a list or tuple of messages")

        if not messages:
            return 0

        num_tokens = 0
        for message in messages:
            num_tokens += 3  # Formatting overhead per message

            # Convert message element to dictionary structure
            msg_dict = message
            if hasattr(msg_dict, "to_dict") and callable(msg_dict.to_dict):
                msg_dict = msg_dict.to_dict()
            elif hasattr(msg_dict, "dict") and callable(msg_dict.dict):
                msg_dict = msg_dict.dict()
            elif isinstance(msg_dict, str):
                msg_dict = {"content": msg_dict}

            if not isinstance(msg_dict, dict):
                raise TypeError(
                    f"Unsupported message type: {type(message)}. Message elements must "
                    "be dict, str, or objects with .to_dict() or .dict() methods."
                )

            # Check if name is present in message dict
            if "name" in msg_dict and msg_dict["name"] is not None:
                num_tokens += 1
                name_val = msg_dict["name"]
                if isinstance(name_val, str):
                    num_tokens += self._get_string_tokens(name_val)

            # Count role if present
            role_val = msg_dict.get("role")
            if isinstance(role_val, str):
                num_tokens += self._get_string_tokens(role_val)

            # Count content if present
            content_val = msg_dict.get("content")
            if isinstance(content_val, str):
                num_tokens += self._get_string_tokens(content_val)
            elif isinstance(content_val, list):
                for item in content_val:
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type == "image_url":
                            num_tokens += 85
                        elif item_type == "text" and "text" in item:
                            text_val = item["text"]
                            if isinstance(text_val, str):
                                num_tokens += self._get_string_tokens(text_val)
                        else:
                            # Try to fall back to text key or general string check
                            text_val = item.get("text")
                            if isinstance(text_val, str):
                                num_tokens += self._get_string_tokens(text_val)
                    elif isinstance(item, str):
                        num_tokens += self._get_string_tokens(item)

            # Count tool_calls or function_call if present
            if "function_call" in msg_dict and msg_dict["function_call"] is not None:
                fc = msg_dict["function_call"]
                if hasattr(fc, "to_dict") and callable(fc.to_dict):
                    fc = fc.to_dict()
                elif hasattr(fc, "dict") and callable(fc.dict):
                    fc = fc.dict()
                if isinstance(fc, dict):
                    f_name = fc.get("name")
                    f_args = fc.get("arguments")
                    if isinstance(f_name, str):
                        num_tokens += self._get_string_tokens(f_name)
                    if isinstance(f_args, str):
                        num_tokens += self._get_string_tokens(f_args)

            if "tool_calls" in msg_dict and msg_dict["tool_calls"] is not None:
                tc_list = msg_dict["tool_calls"]
                if isinstance(tc_list, list):
                    for tc in tc_list:
                        if hasattr(tc, "to_dict") and callable(tc.to_dict):
                            tc = tc.to_dict()
                        elif hasattr(tc, "dict") and callable(tc.dict):
                            tc = tc.dict()
                        if isinstance(tc, dict):
                            func = tc.get("function")
                            if func:
                                if hasattr(func, "to_dict") and callable(func.to_dict):
                                    func = func.to_dict()
                                elif hasattr(func, "dict") and callable(func.dict):
                                    func = func.dict()
                                if isinstance(func, dict):
                                    f_name = func.get("name")
                                    f_args = func.get("arguments")
                                    if isinstance(f_name, str):
                                        num_tokens += self._get_string_tokens(f_name)
                                    if isinstance(f_args, str):
                                        num_tokens += self._get_string_tokens(f_args)

        num_tokens += 3  # Priming tokens overhead for assistant response prefix
        return num_tokens

    def get_usage_percentage(self, current_tokens: int) -> float:
        """Compute the current usage percentage out of max_tokens.

        Args:
            current_tokens: The current token count. Must be a non-negative integer or float.

        Returns:
            The usage percentage as a float.

        Raises:
            TypeError: If current_tokens is not an integer or float.
            ValueError: If current_tokens is negative.
        """
        if not isinstance(current_tokens, (int, float)) or isinstance(current_tokens, bool):
            raise TypeError("current_tokens must be an integer or float")
        if current_tokens < 0:
            raise ValueError("current_tokens must be non-negative")

        return (current_tokens / self.max_tokens) * 100.0

    def check_d_zone(self, current_tokens: int) -> tuple[bool, str]:
        """Check if the context token usage is in the Danger Zone (>= 40.0%).

        Args:
            current_tokens: The current token count.

        Returns:
            A tuple of (is_in_d_zone, warning_message).
        """
        percentage = self.get_usage_percentage(current_tokens)
        if percentage >= 40.0:
            warning_message = (
                f"Warning: Context token usage is at {percentage:.2f}% "
                f"({current_tokens}/{self.max_tokens} tokens). "
                "Danger Zone (D-Zone) reached! Please consider summarizing "
                "the conversation history or resetting the context to free up space."
            )
            return True, warning_message
        return False, ""
