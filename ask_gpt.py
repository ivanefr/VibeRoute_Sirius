# import openai
from openai import OpenAI
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

    def ask(self, query, tools):
        self.messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
        # model=f"gpt://{YANDEX_CLOUD_FOLDER}/yandexgpt/latest",
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/qwen3-235b-a22b-fp8/latest",
            messages=self.messages,
            temperature=0.3,
            tools=tools,
            tool_choice='required',
            max_tokens=2000
        )

        tool_call = response.choices[0].message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        return name, args

        # answer = response.choices[0].message.content
        # self.messages.append({"role": "assistant", "content": answer})

        # return answer
    
    def clear_history(self):
        self.messages = self.start_message

# def main():
#     t = QwenChat()

#     s = ''
#     cnt = 0
#     while s != '-1' and cnt < 20:
#         cnt += 1
#         print(t.ask(input()))


# if __name__ == "__main__":
#     main()
