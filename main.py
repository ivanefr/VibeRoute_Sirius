from flask import Flask, render_template_string, request, jsonify
import random
import json

app = Flask(__name__)


with open('index.html', 'r', encoding='utf-8') as file:
    BASE_HTML = file.read()

VIBES = [
    ("friendly", "🤝", "Дружеская"),
    ("romantic", "❤️", "Романтическая"),
    ("family", "👨‍👩‍👧‍👦", "Семейная"),
    ("cultural", "🏛️", "Культурная"),
    ("active", "🚴", "Активная"),
    ("cozy", "☕", "Спокойная / Уютная"),
    ("gourmet", "🍕", "Гурманская"),
]

PLACE_DEMOS = [
    ("Гараж — Музей современного искусства", "Идеальное место для начала %vibe% прогулки. Погрузитесь в мир современного искусства.", "Билеты: ~500-700 ₽ на человека.", "https://placehold.co/300x150?text=Гараж"),
    ("Москва-Сити", "Высотки и красивые виды для незабываемых впечатлений.", "Коктейль: ~800 ₽. Подъём на смотровую: ~1200 ₽.", "https://placehold.co/300x150?text=Сити"),
    ("Кофейня Surf Coffee", "Отдохните и обсудите дальнейшие планы в уютной атмосфере.", "Кофе: ~350 ₽.", "https://placehold.co/300x150?text=Кофейня"),
    ("Парк Горького", "Прогуляйтесь по набережной, наслаждаясь природой.", "Вход свободный.", "https://placehold.co/300x150?text=Парк+Горького"),
    ("Третьяковская Галерея", "Осмотрите коллекцию шедевров русского искусства.", "Вход: ~600 ₽.", "https://placehold.co/300x150?text=Третьяковка"),
    ("Ресторан LavkaLavka", "Фермерская кухня и приятная атмосфера для завершения прогулки.", "Ужин: ~2000 ₽ на чел.", "https://placehold.co/300x150?text=LavkaLavka")
]

# ====== Загрузка реальных мест из JSON-файла ======
# Ожидаемый формат файла places.json (в корне проекта):
# [
#   {
#     "name": "Парк Горького",
#     "lat": 55.729876,
#     "lng": 37.603456,
#     "desc": "Большой парк с набережной и прокатом.",
#     "budget": "Вход свободный, кофе ~300 ₽",
#     "img": "https://example.com/gorky.png"
#   },
#   ...
# ]
PLACES = []
try:
    with open("places.json", "r", encoding="utf-8") as f:
        PLACES = json.load(f)
except FileNotFoundError:
    PLACES = []

# Получает данные из формы

def parse_form(req_form):
    fd = {}
    fd["start_addr"] = req_form.get("start_addr", "")
    fd["end_addr"] = req_form.get("end_addr", "")
    fd["duration_hrs"] = int(req_form.get("duration_hrs", 2))
    fd["duration_mins"] = int(req_form.get("duration_mins", 0))
    fd["budget"] = int(req_form.get("budget", 2000))
    fd["vibe"] = req_form.get("vibe", "romantic")
    fd["extra_notes"] = req_form.get("extra_notes", "")
    # Custom waypoints parser
    waypoints = []
    if "waypoints_json" in req_form:
        import json
        try: waypoints = json.loads(req_form.get("waypoints_json"))
        except: waypoints = []
    else:
        waypoints = req_form.getlist("waypoints")
    fd["waypoints"] = [w for w in waypoints if w and w.strip()]
    # print(fd['start_addr'])
    # print(fd['waypoints'])
    return fd

def demo_route_steps(formdata):
    points = []
    if formdata.get("start_addr"): points.append(formdata["start_addr"])
    points.extend(formdata.get("waypoints", []))
    if formdata.get("end_addr"): points.append(formdata["end_addr"])
    N = len(points)
    steps = []
    used = []
    vibe_map = {v[0]: v[2] for v in VIBES}
    vibe_verbose = vibe_map.get(formdata.get("vibe"), "")

    for i in range(N):
        # Берём данные о месте: сначала из PLACES (json), fallback — из PLACE_DEMOS
        if PLACES:
            # пытаемся не повторять места по name
            available = [p for p in PLACES if p.get("name") not in used] or PLACES
            place = random.choice(available)
            title = place.get("name", "Место")
            desc = place.get("desc", "")
            budget = place.get("budget", "")
            img = place.get("img", "https://placehold.co/300x150?text=Place")
            lat = place.get("lat")
            lng = place.get("lng")
            if lat is not None and lng is not None:
                map_link = f"https://yandex.ru/maps/?ll={lng},{lat}&z=16"
            else:
                map_link = f"https://yandex.ru/maps/?text={points[i]}" if points[i] else "#"
        else:
            title, desc, budget, img = random.choice([p for p in PLACE_DEMOS if p[0] not in used] or PLACE_DEMOS)
            map_link = f"https://yandex.ru/maps/?text={points[i]}" if points[i] else "#"

        used.append(title)

        # Подставляем характер прогулки, если в описании есть плейсхолдер
        if "%vibe%" in desc and vibe_verbose:
            desc = desc.replace("%vibe%", vibe_verbose)

        step = {
            "name": points[i] if points[i].strip() else title,
            "desc": desc,
            "budget": budget,
            "img": img,
            "map_link": map_link,
            "segment": (f"Время в пути до следующей точки: {15+5*i} минут пешком ({1.2+0.3*i:.1f} км)" if i < N-1 else "")
        }
        steps.append(step)
    return steps

def get_vibe_verbose(vibe):
    for v in VIBES:
        if v[0]==vibe:
            return v[2]
    return "Романтическая"

def demo_tips(formdata):
    rest = max(formdata['budget'] - 700*(2+len(formdata.get("waypoints",[]))), 0)
    return (
        f"Остаток бюджета <span style='font-weight:bold'>{rest} ₽</span> можно потратить на десерт в кофейне у конечной точки или на покупку сувениров."
        "<br>Дополнительно: Возьмите power bank, чтобы не пропустить красивые фото!<br>"
    )

# =========== ROUTES ============

@app.route('/', methods=['GET', 'POST'])
def index():
    loading = False
    formdata = {"waypoints":[]}
    result_data = None
    generated = False
    if request.method == 'POST':
        loading = True
        formdata = parse_form(request.form)
        # Demo: use dummy route info/LLM generated results
        steps = demo_route_steps(formdata)
        summary = {
            "vibe_verbose": get_vibe_verbose(formdata["vibe"]),
            "duration_str": f"{formdata['duration_hrs']} ч {formdata['duration_mins']} мин" if formdata['duration_mins'] else f"{formdata['duration_hrs']} ч",
            "budget": formdata['budget'],
            "distance": f"{5.2+random.randint(-1,2)*0.3:.1f}",
            "steps": steps,
            "tips": demo_tips(formdata),
        }
        result_data = summary
        generated = True
        loading = False
    else:
        # Try get prefilled params if url params
        for k in ["start_addr","end_addr","duration_hrs","duration_mins","budget","vibe","extra_notes"]:
            if k in request.args:
                formdata[k] = request.args[k]
        wps = request.args.getlist('waypoints')
        if wps:
            formdata["waypoints"] = wps
        else:
            formdata["waypoints"] = []
    # Читаем шаблон в UTF-8, чтобы не падать на эмодзи/спецсимволах в Windows-консоли
    with open('index.html', 'r', encoding='utf-8') as file:
        BASE_HTML = file.read()
    return render_template_string(BASE_HTML, formdata=formdata, vibes=VIBES, result_data=result_data, generated=generated, loading=loading)

@app.route('/reverse_geocode')
def reverse_geocode():
    lat = request.args.get("lat","")
    lng = request.args.get("lng","")
    # print(lat, lng)
    # Emulate nearby addresses for demo
    fake_addr = f"Улица-{str(int(float(lat)*100)%1000)} Дом {str(int(float(lng)*100)%50)}"
    return jsonify({"address": fake_addr})

if __name__ == "__main__":
    app.run(debug=True)