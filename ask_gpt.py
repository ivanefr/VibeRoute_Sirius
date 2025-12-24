# import openai
from openai import OpenAI
from loguru import logger
import json

with open("api_key", 'r') as file:
    lines_list = file.readlines()

YANDEX_CLOUD_FOLDER = lines_list[0].removesuffix('\n')
YANDEX_CLOUD_API_KEY = lines_list[1].removesuffix('\n')

class QwenChat:
    def __init__(self):
        self.start_message = "Ты -- нейросеть, которая умеет строить оптимальные маршруты с учетом пожеланий пользователя."
        self.client = OpenAI(
            api_key=YANDEX_CLOUD_API_KEY,
            base_url="https://llm.api.cloud.yandex.net/v1",
            project=YANDEX_CLOUD_FOLDER
        )
        self.messages = [
            {"role": "system", "content": self.start_message}
        ]

    def ask(self, query, tools, model_name="qwen_235b"):
        if len(query) >= 1:
            self.messages.append({"role": "user", "content": query})

        # Map form model names to actual API model names
        model_mapping = {
            "qwen_235b": f"gpt://{YANDEX_CLOUD_FOLDER}/qwen3-235b-a22b-fp8/latest",
            "gpt-oss-120b": f"gpt://{YANDEX_CLOUD_FOLDER}/gpt-oss-120b/latest"
        }

        model = model_mapping.get(model_name, f"gpt://{YANDEX_CLOUD_FOLDER}/qwen3-235b-a22b-fp8/latest")

        response = self.client.chat.completions.create(
        model=model,
            messages=self.messages,
            temperature=0.3,
            tools=tools,
            tool_choice='required',
            max_tokens=2000
        )

        tool_call = response.choices[0].message.tool_calls[0]
        name = tool_call.function.name
        id = tool_call.id
        args = json.loads(tool_call.function.arguments)

        answer = response.choices[0].message
        self.messages.append(answer)
        # self.messages.append({"role": "assistant", "content": answer})
        return name, args, id
    
    def clear_history(self):
        self.messages = [
            {"role": "system", "content": self.start_message}
        ]
