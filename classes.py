import get_embedding
import openai
import ask_gpt
import find_nearst_points
import get_database
import json

class Object:
    def __init__(self, x, y, id, street, desc, other_params):
        self.x = x
        self.y = y
        self.id = id
        self.desc = desc
        self.other = other_params
        self.street = street

    def __eq__(self, other):
        return isinstance(other, Object) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.desc)

class EmbSearch:
    def __init__(self, db, k):
        descs = []
        self.db = db
        for i in self.db:
            descs.append(i.desc)
        # self.emb = get_embedding.get_emb(descs)
        self.emb = []
        with open("points_embeddings", 'r', encoding='utf-8') as f:
            for i in range(266):
                l = list(map(float, f.readline().split()))
                self.emb.append(l)

        self.neigh = get_embedding.NN(self.emb, k)

    def search(self, query):
        q_emb = get_embedding.get_emb([query])
        idx = get_embedding.get_nearst_embedding(self.neigh, q_emb)
        # return idx

        res = []
        for i in idx[0]:
            res.append(self.db[i])

        return res

class LLMAgent:
    def __init__(self, tools, db, embs):
        self.model = ask_gpt.QwenChat()
        self.tools = tools
        self.db = db
        self.embs = embs

    def get_places(self, query : str):
        res_points = find_nearst_points.get_points(self.db, self.embs, self.a, self.b, query)
        ans = ''
        for i in res_points:
            ans += 'id: ' + str(i.id) + ', adress: ' + i.street + ', description: ' + i.desc + '\n'
        return ans
    
    def message(text, points):
        return [text, points]

    def answer_model(self):
        name, args = self.model.ask(self.system_prompt, self.tools)

        if name == "get_places":
            # self.system_prompt = self.get_place(**args)
            result = self.get_places(**args)
        elif name == "message":
            result = self.message(**args)
            self.ans.append(result)
        return result

    def get_answer(self, a, b, w_type, time):
        self.system_prompt = f"Ты находишься в России, на Федеральной территории Сириус. \
            Требуется построить пешеходный маршрут для {w_type}, который начинается в адресе \
            {a.street} и заканчивается в адресе {b.street}. Длительность маршрута должна \
            быть равна примерно {time} минут. Маршрут должен содержать не более 5 промежуточных \
            точек и быть интересным и наиболее подходящим для данного случая. Желательно не \
            заходить повторно в заведения одинакового типа (наприимер, в два кафе). Все точки \
            должны быть уникальными (в том числе ни одна промежуточная точка не должна совпадать \
            с точками {a.street} и {b.street}! Ты можешь спрашивать какие есть подходящие точки, \
            сделав запрос get_places. В качестве аргумента передай, какого типа точки тебе нужны. \
            Функция вернет тебе адреса, краткие описания и id всех подходящих заведений. \
            Когда будешь готов добавить точку в маршрут, вызови функцию message и передай ей адрес и id точки"

        self.a = a
        self.b = b
        self.w_type = w_type
        self.time = time
        self.ans = []
        cnt = 0
        while cnt < 10 and len(self.ans) < 5:
            cnt += 1

            print(self.system_prompt)
            res_gpt = self.answer_model()
            print(res_gpt)

            self.model.messages.append({
                "role": "tool",
                "tool_call_id": self.model.tool_call.id,
                "content": json.dumps(res_gpt, ensure_ascii=False)
            })
        self.model.clear_history()
        return self.ans

def main():
    db = get_database.get_database()

    a = db[15]
    b = db[150]
    w_type = "прогулка с друзьями"
    time = "2"

    embs = EmbSearch(db, 150)

    tools = [{
        "type": "function",
        "function" : {
            "name": "get_places",
            "parameters": {
                "type": "object",
                "description": "Функция получает строку запроса и возвращает 10 самых подходящих точек под запрос",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }},
        {"type" : "function",
        "function" : {
            "name": "message",
            "parameters": {
                "type": "object",
                "description": "В эту функцию нужно передать точки для маршрута в формате: адрес, id точки",
                "properties": {
                    "text": {"type": "string"},
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        # "description": "id каждой точки в маршруте",
                    }
                },
                "required": ["text", "points"]
            }
        }
    }]


    # with open("points_embeddings", 'w', encoding='utf-8') as f:
    #     for i in embs.emb:
    #         for j in i:
    #             f.write(str(j))
    #             f.write(' ')
    #         f.write('\n')

    model = LLMAgent(tools, db, embs)
    ans = model.get_answer(a, b, w_type, time)
    print(ans)

    for i in ans:
        print(db[i].street)

    # print(len(ans))
    # for i in ans:
    #     print(i)

if __name__ == '__main__':
    main()