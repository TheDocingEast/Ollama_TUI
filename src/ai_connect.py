from ollama import AsyncClient


class OllamaClient(AsyncClient):
    def __init__(self, host: str = "http://localhost:11434"):
        super().__init__(host=host)

    async def send_message(self, model: str, msg_content: str, img=None):
        message = [
            {
                "role": "user",
                "content": msg_content,
            }
        ]

        if img is not None and isinstance(img, str):
            message[0]["images"] = [img]
        response = await self.chat(model=model, messages=message, keep_alive="10m")
        return response
