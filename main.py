from flask import Flask, render_template_string, request, jsonify, send_from_directory
import random
import json
import requests
import os

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

PLACES = [{
      "type": "Feature",
      "properties": {
        "amenity": "cafe",
        "name": "Шоколадница",
        "name:en": "Shokoladnitsa",
        "phone": "+7 862 2383923",
        "website": "https://shoko.ru/",
        "cuisine": "coffee_shop",
        "opening_hours": "Mo-Su 10:00-22:00",
        "name:ru": "Шоколадница",
        "level": "0",
        "popularity_score": 8
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          39.9262057,
          43.4272589
        ]
      }
    },{
      "type": "Feature",
      "properties": {
        "amenity": "pub",
        "name": "O'Sullivan's Irish Pub",
        "phone": "+7 938 4550074",
        "website": "http://osullivans.ru/",
        "addr:city": "Сочи",
        "addr:housenumber": "55",
        "addr:street": "улица 65 лет Победы",
        "cuisine": "irish",
        "opening_hours": "Mo-Su 12:00-24:00",
        "internet_access": "wlan",
        "alt_name": "Ирландский паб",
        "mapillary": "841823033145973",
        "survey:date": "2017-09-11",
        "theme": "irish",
        "popularity_score": 8
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          39.9755125,
          43.3964213
        ]
      }
    },
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
# PLACES = []
# try:
#     with open("places.json", "r", encoding="utf-8") as f:
#         PLACES = json.load(f)
# except FileNotFoundError:
#     PLACES = []

# Получает данные из формы


def parse_form(req_form):
    fd = {}
    fd["start_addr"] = req_form.get("start_addr", "")
    fd["end_addr"] = req_form.get("end_addr", "")
    fd["start_lat"] = req_form.get("start_lat", "")
    fd["start_lng"] = req_form.get("start_lng", "")
    fd["end_lat"] = req_form.get("end_lat", "")
    fd["end_lng"] = req_form.get("end_lng", "")
    fd["duration_hrs"] = int(req_form.get("duration_hrs", 2))
    fd["duration_mins"] = int(req_form.get("duration_mins", 0))
    fd["budget"] = int(req_form.get("budget", 2000))
    fd["vibe"] = req_form.get("vibe", "romantic")
    fd["extra_notes"] = req_form.get("extra_notes", "")
    fd["map_lat"] = req_form.get("map_lat", "")
    fd["map_lng"] = req_form.get("map_lng", "")
    fd["map_zoom"] = req_form.get("map_zoom", "")
    return fd


def get_end_location_coords(req_form):
    lat_str = req_form.get("end_lat", "")
    lng_str = req_form.get("end_lng", "")

    if lat_str and lng_str:
        try:
            return {"lat": float(lat_str), "lng": float(lng_str)}
        except (ValueError, TypeError):
            return None


def forward_geocode(query):
    query = (query or "").strip()
    if not query:
        return None

    try:
        yandex_resp = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={
                "format": "json",
                "geocode": query,
                "results": 1
            },
            timeout=3
        )
        yandex_resp.raise_for_status()
        yandex_data = yandex_resp.json()
        features = yandex_data.get("response", {}).get(
            "GeoObjectCollection", {}).get("featureMember", [])
        if features:
            geo_object = features[0].get("GeoObject", {})
            pos = geo_object.get("Point", {}).get("pos", "")
            if pos:
                lng_str, lat_str = pos.split()[:2]
                return {"lat": float(lat_str), "lng": float(lng_str)}
    except:
        pass

    try:
        nominatim_resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "format": "jsonv2",
                "q": query,
                "limit": 1,
                "accept-language": "ru"
            },
            headers={"User-Agent": "viberoute-demo/1.0"},
            timeout=5
        )
        nominatim_resp.raise_for_status()
        data = nominatim_resp.json() or []
        if data:
            return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
    except:
        pass

    return None
    return None


def get_start_location_coords(req_form):
    """
    Получает координаты начального местоположения из формы.

    Args:
        req_form: объект request.form из Flask

    Returns:
        dict: {"lat": float, "lng": float} или None, если координаты не переданы
    """
    lat_str = req_form.get("start_lat", "")
    lng_str = req_form.get("start_lng", "")

    if lat_str and lng_str:
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            return {"lat": lat, "lng": lng}
        except (ValueError, TypeError):
            return None
    return None


def demo_route_steps(formdata):
    points = []
    if formdata.get("start_addr"):
        points.append(formdata["start_addr"])
    if formdata.get("end_addr"):
        points.append(formdata["end_addr"])
    N = len(points)
    steps = []
    used = []
    vibe_map = {v[0]: v[2] for v in VIBES}
    vibe_verbose = vibe_map.get(formdata.get("vibe"), "")

    for i in range(N):
        # Берём данные о месте: сначала из PLACES (json)
        if PLACES:
            # пытаемся не повторять места по name
            available = [p for p in PLACES if p.get(
                "name") not in used] or PLACES
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
            title = ""
            desc = ""
            budget = ""
            img = ""
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
        if v[0] == vibe:
            return v[2]
    return "Романтическая"


def demo_tips(formdata):
    rest = max(formdata['budget'] - 700 * 2, 0)
    return (
        f"Остаток бюджета <span style='font-weight:bold'>{rest} ₽</span> можно потратить на десерт в кофейне у конечной точки или на покупку сувениров."
        "<br>Дополнительно: Возьмите power bank, чтобы не пропустить красивые фото!<br>"
    )

# =========== ROUTES ============


@app.route('/', methods=['GET', 'POST'])
def index():
    loading = False
    formdata = {}
    result_data = None
    generated = False
    if request.method == 'POST':
        loading = True
        formdata = parse_form(request.form)
        start_coords = get_start_location_coords(request.form)
        end_coords   = get_end_location_coords(request.form)

        if not start_coords and formdata.get("start_addr"):
            start_coords = forward_geocode(formdata.get("start_addr"))
        if not end_coords and formdata.get("end_addr"):
            end_coords = forward_geocode(formdata.get("end_addr"))

        if start_coords:
            formdata["start_lat"] = str(start_coords["lat"])
            formdata["start_lng"] = str(start_coords["lng"])
        if end_coords:
            formdata["end_lat"] = str(end_coords["lat"])
            formdata["end_lng"] = str(end_coords["lng"])

        if start_coords:
            print(f"START: {start_coords['lat']}, {start_coords['lng']}")

        if end_coords:
            print(f"END: {end_coords['lat']}, {end_coords['lng']}")
        # print(request.args)
        # print(request)
        # Получаем координаты начального местоположения (если были переданы)
        start_coords = get_start_location_coords(request.form)
        if start_coords:
            pass
            # print(
            #     f"Координаты начального местоположения: lat={start_coords['lat']}, lng={start_coords['lng']}")
            # Здесь можно использовать координаты для построения маршрута, поиска ближайших мест и т.д.

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
        for k in ["start_addr", "end_addr", "duration_hrs", "duration_mins", "budget", "vibe", "extra_notes", "map_lat", "map_lng", "map_zoom"]:
            if k in request.args:
                formdata[k] = request.args[k]
    if result_data is not None:
        print(f"{formdata=}")
        print(f"{result_data=}")
    # Читаем шаблон в UTF-8, чтобы не падать на эмодзи/спецсимволах в Windows-консоли
    # Вот здесь появится функция которая получает массив PLACE
    with open('index.html', 'r', encoding='utf-8') as file:
        BASE_HTML = file.read()
    return render_template_string(BASE_HTML, formdata=formdata, vibes=VIBES, result_data=result_data, generated=generated, loading=loading, places=PLACES)


@app.route('/reverse_geocode')
def reverse_geocode():
    lat = request.args.get("lat", "")
    lng = request.args.get("lng", "")

    if not lat or not lng:
        return jsonify({"address": ""})

    address = ""

    # Сначала пробуем Яндекс Геокодер (точнее для России, работает без ключа для небольшого количества запросов)
    try:
        yandex_resp = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={
                "format": "json",
                "geocode": f"{lng},{lat}",  # Яндекс использует порядок lng,lat
                "kind": "house",  # Запрашиваем адрес дома
                "results": 1
            },
            timeout=3
        )
        yandex_resp.raise_for_status()
        yandex_data = yandex_resp.json()

        # Извлекаем адрес из ответа Яндекс
        try:
            features = yandex_data.get("response", {}).get(
                "GeoObjectCollection", {}).get("featureMember", [])
            if features:
                geo_object = features[0].get("GeoObject", {})
                address = geo_object.get("metaDataProperty", {}).get(
                    "GeocoderMetaData", {}).get("text", "")
        except:
            pass

    except:
        pass

    # Если Яндекс не вернул адрес, пробуем Nominatim
    if not address:
        try:
            nominatim_resp = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "format": "jsonv2",
                    "lat": lat,
                    "lon": lng,
                    "accept-language": "ru"
                },
                headers={"User-Agent": "viberoute-demo/1.0"},
                timeout=5
            )
            nominatim_resp.raise_for_status()
            nominatim_data = nominatim_resp.json()

            # Пытаемся собрать более точный адрес из компонентов
            addr_parts = nominatim_data.get("address", {})
            if addr_parts:
                # Собираем адрес из компонентов (улица, дом, город)
                street = addr_parts.get(
                    "road") or addr_parts.get("pedestrian") or ""
                house = addr_parts.get("house_number") or ""
                city = addr_parts.get("city") or addr_parts.get(
                    "town") or addr_parts.get("village") or ""

                if street:
                    if house:
                        address = f"{street}, {house}"
                    else:
                        address = street
                    if city:
                        address = f"{address}, {city}"
                else:
                    # Если нет улицы, используем display_name
                    address = nominatim_data.get("display_name", "")
            else:
                address = nominatim_data.get("display_name", "")

        except:
            pass

    # Если оба сервиса не вернули адрес, возвращаем координаты
    if not address:
        address = f"{lat}, {lng}"

    return jsonify({"address": address})


@app.route('/geocode')
def geocode():
    query = (request.args.get("query", "") or "").strip()
    if not query:
        return jsonify({"lat": None, "lng": None})
    coords = forward_geocode(query)
    if coords:
        return jsonify(coords)
    return jsonify({"lat": None, "lng": None})


@app.route('/style.css')
def style_css():
    return send_from_directory(os.path.dirname(__file__), 'style.css', mimetype='text/css')


if __name__ == "__main__":
    app.run(debug=True)
