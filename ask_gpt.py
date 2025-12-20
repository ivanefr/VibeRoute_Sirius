import openai

with open("api_key", 'r') as file:
    lines_list = file.readlines()

YANDEX_CLOUD_FOLDER = lines_list[0].removesuffix('\n')
YANDEX_CLOUD_API_KEY = lines_list[1].removesuffix('\n')

client = openai.OpenAI(
    api_key=YANDEX_CLOUD_API_KEY,
    base_url="https://llm.api.cloud.yandex.net/v1",
    project=YANDEX_CLOUD_FOLDER
)

def ask_gpt(message):
    response = client.chat.completions.create(
        # model=f"gpt://{YANDEX_CLOUD_FOLDER}/yandexgpt/latest",
        model=f"gpt://{YANDEX_CLOUD_FOLDER}/qwen3-235b-a22b-fp8/latest",
        messages=[
            {"role": "user", "content": message}
        ],
        max_tokens=2000,
        temperature=0.3,
        stream=True
    )

    res = ''
    for chunk in response:
        if len(chunk.choices) >= 1 and chunk.choices[0].delta.content is not None:
            res += chunk.choices[0].delta.content
    return res
