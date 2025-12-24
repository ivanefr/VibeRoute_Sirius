import get_embedding
import openai
import ask_gpt
import find_nearst_points
import get_database
import json
import math
from loguru import logger

class Object:
    def __init__(self, x, y, street, name=None, amenity=None, desc=None, id=None, other_params=None):
        self.x = x
        self.y = y
        self.id = id
        self.desc = desc
        self.other = other_params
        self.street = street
        self.name = name
        self.amenity = amenity

    def dist_between_points(self, other):
        R = 6371000
        lat1, lon1, lat2, lon2 = map(math.radians, [self.x, self.y, other.x, other.y])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def __eq__(self, other):
        return isinstance(other, Object) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.desc)

    def __repr__(self):
        return f"{self.x=}; {self.y=}; {self.id=}, {self.desc=}; {self.other=}; {self.street=}"

class EmbSearch:
    def __init__(self, db, k, start_embs=None):
        descs = []
        self.db = db
        for i in self.db:
            descs.append(i.desc)

        # self.emb = get_embedding.get_emb(descs)
        self.emb = []
        if start_embs == None:
            with open("points_embeddings.txt", 'r', encoding='utf-8') as f:
                for i in self.db:
                    l = list(map(float, f.readline().split()))
                    self.emb.append(l)
        else:
            logger.info(db)
            for i in self.db:
                self.emb.append(start_embs.emb[i.id])

        self.neigh = get_embedding.NN(self.emb, k)

    def search(self, query):
        q_emb = get_embedding.get_emb([query])
        idx = get_embedding.get_nearst_embedding(self.neigh, q_emb)
        res = []
        for i in idx[0]:
            res.append(self.db[i])

        return res

class LLMAgent:
    def __init__(self):
        self.model = ask_gpt.QwenChat()
        self.tools = [{
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
                        "text": {
                            "type": "string",
                            "description": "Описание маршрута"
                        },
                        "points": {
                            "type": "array",
                            "description": "список id точек маршрута",
                            "items": {
                                "type": "integer"
                            },
                        }
                    },
                    "required": ["text", "points"]
                }
            }
        }]
        self.db = get_database.get_database()
        self.embs = EmbSearch(self.db, 3)

    def get_places(self, query : str):
        res_points = find_nearst_points.get_points(self.db, self.embs, self.a, self.b, query)
        ans = ''
        for i in res_points:
            ans += 'id: ' + str(i.id) + ', adress: ' + str(i.street) + ', description: ' + str(i.desc) + '\n'
        return ans

    def message(self, text, points):
        return text, points

    def answer_model(self):
        name, args, id = self.model.ask(self.system_prompt, self.tools)

        if name == "get_places":
            result = self.get_places(**args)
        elif name == "message":
            desc = args['text']
            points = args['points']
            result = self.message(desc, points)
            self.desc, self.ans_id = result
        return result, id

    def get_answer(self, a, b, w_type, time):
        dist = a.dist_between_points(b)
        self.system_prompt = f"Ты находишься в России, на Федеральной территории Сириус. \
Требуется построить пешеходный маршрут для цели: \"{w_type}\", который начинается в адресе \
{a.street} и заканчивается в адресе {b.street}. Длительность маршрута должна \
быть равна примерно {time} минут. Расстояние от точки {a.street} до точки {b.street} -- {dist} метров. Маршрут должен содержать не более 5 промежуточных \
точек и быть интересным и наиболее подходящим для данного случая. В маршруте не должно быть \
больше одного кафе или ресторана, если пользователь не попросил больше! \
Все точки должны быть уникальными (в частности, ни одна промежуточная точка не должна совпадать \
с точками {a.street} и {b.street})! Ты можешь спрашивать какие есть подходящие точки, \
сделав запрос get_places. В качестве аргумента передай, какого типа точки тебе нужны. \
Функция вернет тебе адреса, краткие описания и id всех подходящих заведений. \
Когда будешь готов добавить точку в маршрут, вызови функцию message и передай ей адреса и массив id точек. \
За раз можно сделать только один запрос к функциям. Всего, прежде чем выдать ответ, сделай не более 5 запросов. \
После 5 запросов обязательно выведи ответ, если не сделал этого раньше!!! \
Начальную и конечную точку не нужно добавлять в маршрут!"

        self.a = a
        self.b = b
        self.w_type = w_type
        self.time = time
        self.ans_id = []
        self.ans = []
        self.desc = 'no-description'
        cnt = 0
        while cnt < 10 and len(self.ans_id) == 0:
            cnt += 1

            res_gpt, id = self.answer_model()

            self.model.messages.append({
                "role": "tool",
                "tool_call_id": id, # self.model.tool_call.id,
                "content": json.dumps(res_gpt, ensure_ascii=False)
            })
            self.system_prompt = ""
        self.model.clear_history()

        for i in self.ans_id:
            self.ans.append(self.db[i])

        return self.desc, self.ans
