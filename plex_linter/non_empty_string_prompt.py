from rich.prompt import InvalidResponse, Prompt


class NonEmptyStringPrompt(Prompt):
    validate_error_message = "[prompt.invalid]Please enter a non-empty string."

    def process_response(self, value: str) -> str:
        if not value:
            raise InvalidResponse(self.validate_error_message)
        return value
