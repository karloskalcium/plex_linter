from rich.prompt import InvalidResponse, PromptBase


class NonEmptyStringPrompt(PromptBase[str]):
    response_type = str
    validate_error_message = "[prompt.invalid]Please enter a non-empty string."

    def process_response(self, value: str) -> str:
        if len(value) > 0:
            return value
        else:
            raise InvalidResponse(self.validate_error_message)
