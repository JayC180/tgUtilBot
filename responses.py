def handle_response(text:str) -> str:
    lower: str = text.lower()

    if 'hello' or 'hi' or 'hey' in lower:
        return "Hi."

    return 'I can\'t understand.'