from langchain_core.tools import tool


def _normalize_city_name_core(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        return ""

    key = raw.casefold().replace(".", "").replace(",", "")
    key = " ".join(key.split())

    aliases = {
        "ha noi": "Hà Nội",
        "hanoi": "Hà Nội",
        "hn": "Hà Nội",
        "da nang": "Đà Nẵng",
        "danang": "Đà Nẵng",
        "dn": "Đà Nẵng",
        "phu quoc": "Phú Quốc",
        "pq": "Phú Quốc",
        "ho chi minh": "Hồ Chí Minh",
        "hochiminh": "Hồ Chí Minh",
        "hcm": "Hồ Chí Minh",
        "tphcm": "Hồ Chí Minh",
        "tp hcm": "Hồ Chí Minh",
        "sai gon": "Hồ Chí Minh",
        "saigon": "Hồ Chí Minh",
        "sg": "Hồ Chí Minh",
    }
    return aliases.get(key, raw)


def _parse_hhmm_to_minutes(value: str) -> int | None:
    v = (value or "").strip()
    if not v or ":" not in v:
        return None
    hh, mm = v.split(":", 1)
    try:
        h = int(hh)
        m = int(mm)
    except ValueError:
        return None
    if h < 0 or h > 23 or m < 0 or m > 59:
        return None
    return h * 60 + m


FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1600000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1300000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3200000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1300000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1800000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1200000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3500000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1500000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2800000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1400000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180000, "area": "Quận 1", "rating": 4.6},
    ],
}

ATTRACTIONS_DB: dict[str, list[dict[str, str]]] = {
    "Đà Nẵng": [
        {"name": "Bãi biển Mỹ Khê", "type": "relax"},
        {"name": "Bán đảo Sơn Trà", "type": "family"},
        {"name": "Ngũ Hành Sơn", "type": "family"},
        {"name": "Cầu Rồng", "type": "family"},
        {"name": "Chợ Cồn", "type": "foodie"},
        {"name": "Chợ Hàn", "type": "foodie"},
        {"name": "Bà Nà Hills", "type": "family"},
    ],
    "Phú Quốc": [
        {"name": "Bãi Sao", "type": "relax"},
        {"name": "Bãi Dài", "type": "relax"},
        {"name": "Chợ đêm Phú Quốc", "type": "foodie"},
        {"name": "VinWonders / Vinpearl Safari", "type": "family"},
        {"name": "Hòn Thơm (cáp treo)", "type": "family"},
        {"name": "Làng chài Hàm Ninh", "type": "foodie"},
    ],
    "Hồ Chí Minh": [
        {"name": "Chợ Bến Thành", "type": "foodie"},
        {"name": "Phố đi bộ Nguyễn Huệ", "type": "family"},
        {"name": "Bưu điện Trung tâm", "type": "family"},
        {"name": "Nhà thờ Đức Bà", "type": "family"},
        {"name": "Bảo tàng Chứng tích Chiến tranh", "type": "family"},
        {"name": "Chợ Hồ Thị Kỷ (ẩm thực)", "type": "foodie"},
        {"name": "Thảo Cầm Viên", "type": "family"},
    ],
}

# Ước tính chi phí/ngày (ăn + di chuyển + vé tham quan) theo phong cách.
# Số liệu là giả lập cho bài lab, không phải báo giá thật.
DAILY_COST_DB: dict[str, dict[str, int]] = {
    "Đà Nẵng": {"relax": 450000, "foodie": 550000, "family": 650000},
    "Phú Quốc": {"relax": 600000, "foodie": 700000, "family": 850000},
    "Hồ Chí Minh": {"relax": 500000, "foodie": 650000, "family": 700000},
}


@tool
def normalize_city_name(name: str) -> str:
    """Chuẩn hoá tên thành phố (ví dụ: HCM/TPHCM/Sài Gòn -> Hồ Chí Minh)."""
    return _normalize_city_name_core(name)


@tool
def get_supported_cities() -> list[str]:
    """Trả về danh sách thành phố đang có dữ liệu trong DB."""
    cities: set[str] = set(HOTELS_DB.keys())
    for o, d in FLIGHTS_DB.keys():
        cities.add(o)
        cities.add(d)
    return sorted(cities)


@tool
def get_supported_routes() -> list[dict[str, str]]:
    """Trả về danh sách tuyến bay đang có dữ liệu."""
    routes: list[dict[str, str]] = []
    for o, d in FLIGHTS_DB.keys():
        routes.append({"origin": o, "destination": d})
    routes.sort(key=lambda r: (r["origin"], r["destination"]))
    return routes


@tool
def search_flights(origin: str, destination: str) -> str:
    """Tìm kiếm các chuyến bay giữa hai thành phố từ FLIGHTS_DB."""
    origin = _normalize_city_name_core(origin)
    destination = _normalize_city_name_core(destination)
    key = (origin, destination)
    reverse = False

    flights = FLIGHTS_DB.get(key)
    if flights is None:
        reverse_key = (destination, origin)
        flights = FLIGHTS_DB.get(reverse_key)
        reverse = flights is not None

    if not flights:
        return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."

    def format_price(value: int) -> str:
        return f"{value:,}".replace(",", ".")

    lines: list[str] = []
    for f in flights:
        dep_city, arr_city = (destination, origin) if reverse else (origin, destination)
        line = (
            f"- {f['airline']}: {dep_city} -> {arr_city}, "
            f"khởi hành {f['departure']}, đến nơi {f['arrival']}, "
            f"giá {format_price(f['price'])}đ, hạng {f['class']}."
        )
        lines.append(line)

    return "\n".join(lines)

@tool
def search_hotels(city: str, max_price_per_night: int = 9999999) -> str:
    """Tìm khách sạn trong một thành phố, có lọc theo giá và sắp xếp theo rating."""
    city = _normalize_city_name_core(city)
    hotels = HOTELS_DB.get(city)
    if not hotels:
        return f"Không tìm thấy khách sạn tại {city}."

    # Lọc theo giá tối đa
    filtered = [
        h for h in hotels
        if h["price_per_night"] <= max_price_per_night
    ]

    if not filtered:
        formatted_price = f"{max_price_per_night:,}".replace(",", ".")
        return (
            f"Không tìm thấy khách sạn tại {city} "
            f"với giá dưới {formatted_price}đ/đêm. Hãy thử tăng ngân sách."
        )

    # Sắp xếp theo rating giảm dần
    filtered.sort(key=lambda h: h["rating"], reverse=True)

    def format_price(value: int) -> str:
        return f"{value:,}".replace(",", ".")

    lines: list[str] = []
    for h in filtered:
        line = (
            f"- {h['name']} ({h['stars']}★), khu vực {h['area']}, "
            f"giá {format_price(h['price_per_night'])}đ/đêm, "
            f"rating {h['rating']}."
        )
        lines.append(line)

    return "\n".join(lines)


@tool
def get_attractions(city: str) -> list[dict[str, str]]:
    """Danh sách điểm đi chơi theo thành phố (DB giả lập)."""
    city = _normalize_city_name_core(city)
    return ATTRACTIONS_DB.get(city, [])


def _estimate_daily_cost_core(city: str, style: str) -> int:
    city = _normalize_city_name_core(city)
    style = (style or "").strip().lower()
    if style not in {"relax", "foodie", "family"}:
        style = "relax"

    city_costs = DAILY_COST_DB.get(city)
    if city_costs and style in city_costs:
        return int(city_costs[style])

    fallback_by_style = {"relax": 500000, "foodie": 650000, "family": 750000}
    return int(fallback_by_style[style])


@tool
def estimate_daily_cost(city: str, style: str) -> int:
    """Ước tính chi phí/ngày theo thành phố và phong cách (relax|foodie|family)."""
    return _estimate_daily_cost_core(city=city, style=style)


@tool
def build_itinerary(city: str, days: int, style: str = "relax") -> list[dict[str, object]]:
    """Lịch trình theo ngày dựa trên điểm tham quan (DB giả lập)."""
    city = _normalize_city_name_core(city)
    if days <= 0:
        return []

    style_norm = (style or "").strip().lower()
    if style_norm not in {"relax", "foodie", "family"}:
        style_norm = "relax"

    attractions = ATTRACTIONS_DB.get(city, [])
    if not attractions:
        return []

    preferred = [a["name"] for a in attractions if a.get("type") == style_norm]
    others = [a["name"] for a in attractions if a.get("type") != style_norm]
    pool: list[str] = preferred + others

    per_day = 3 if len(pool) >= 3 else max(1, len(pool))
    daily_budget = _estimate_daily_cost_core(city=city, style=style_norm)

    itinerary: list[dict[str, object]] = []
    idx = 0
    for d in range(1, days + 1):
        items: list[str] = []
        for _ in range(per_day):
            items.append(pool[idx % len(pool)])
            idx += 1

        itinerary.append(
            {
                "day": d,
                "city": city,
                "style": style_norm,
                "items": items,
                "estimated_daily_cost": daily_budget,
            }
        )

    return itinerary


def _recommend_flight_core(origin: str, destination: str, preference: str = "cheap") -> dict[str, object]:
    origin = _normalize_city_name_core(origin)
    destination = _normalize_city_name_core(destination)
    preference = (preference or "").strip().lower()
    if preference not in {"cheap", "early"}:
        preference = "cheap"

    flights = FLIGHTS_DB.get((origin, destination))
    reverse = False
    if flights is None:
        flights = FLIGHTS_DB.get((destination, origin))
        reverse = flights is not None

    if not flights:
        return {"ok": False, "message": f"Không tìm thấy chuyến bay từ {origin} đến {destination}."}

    dep_city, arr_city = (destination, origin) if reverse else (origin, destination)

    def key_fn(f: dict[str, object]):
        if preference == "early":
            t = _parse_hhmm_to_minutes(str(f.get("departure", "")))
            return (t if t is not None else 10**9, int(f.get("price", 10**9)))
        return (
            int(f.get("price", 10**9)),
            _parse_hhmm_to_minutes(str(f.get("departure", ""))) or 10**9,
        )

    best = min(flights, key=key_fn)
    return {
        "ok": True,
        "origin": dep_city,
        "destination": arr_city,
        "airline": best.get("airline"),
        "departure": best.get("departure"),
        "arrival": best.get("arrival"),
        "price": best.get("price"),
        "class": best.get("class"),
        "preference": preference,
    }


@tool
def recommend_flight(origin: str, destination: str, preference: str = "cheap") -> dict[str, object]:
    """Chọn 1 chuyến bay tốt nhất theo tiêu chí (cheap|early)."""
    return _recommend_flight_core(origin=origin, destination=destination, preference=preference)


def _recommend_hotel_core(
    city: str,
    max_price_per_night: int = 9999999,
    preference: str = "rating",
) -> dict[str, object]:
    city = _normalize_city_name_core(city)
    preference = (preference or "").strip().lower()
    if preference not in {"rating", "cheap"}:
        preference = "rating"

    hotels = HOTELS_DB.get(city)
    if not hotels:
        return {"ok": False, "message": f"Không tìm thấy khách sạn tại {city}."}

    filtered = [h for h in hotels if int(h["price_per_night"]) <= int(max_price_per_night)]
    if not filtered:
        return {
            "ok": False,
            "message": f"Không có khách sạn tại {city} trong mức {max_price_per_night}đ/đêm.",
        }

    def key_fn(h: dict[str, object]):
        if preference == "cheap":
            return (int(h.get("price_per_night", 10**9)), -float(h.get("rating", 0.0)))
        return (-float(h.get("rating", 0.0)), int(h.get("price_per_night", 10**9)))

    best = min(filtered, key=key_fn)
    return {
        "ok": True,
        "city": city,
        "name": best.get("name"),
        "stars": best.get("stars"),
        "area": best.get("area"),
        "rating": best.get("rating"),
        "price_per_night": best.get("price_per_night"),
        "preference": preference,
    }


@tool
def recommend_hotel(
    city: str,
    max_price_per_night: int = 9999999,
    preference: str = "rating",
) -> dict[str, object]:
    """Chọn 1 khách sạn tốt nhất theo tiêu chí (rating|cheap) trong ngân sách."""
    return _recommend_hotel_core(
        city=city, max_price_per_night=max_price_per_night, preference=preference
    )


def _estimate_trip_cost_core(
    city: str,
    nights: int,
    style: str = "relax",
    flight_price: int = 0,
    hotel_price_per_night: int = 0,
    extra: int = 0,
) -> dict[str, object]:
    city = _normalize_city_name_core(city)
    if nights < 0:
        nights = 0

    daily = _estimate_daily_cost_core(city=city, style=style)
    living = int(daily) * int(nights)
    hotel_total = int(hotel_price_per_night) * int(nights)
    flight_total = int(flight_price)
    extra_total = int(extra)
    total = living + hotel_total + flight_total + extra_total

    return {
        "city": city,
        "style": (style or "").strip().lower() or "relax",
        "nights": nights,
        "daily_cost": daily,
        "living_total": living,
        "hotel_price_per_night": int(hotel_price_per_night),
        "hotel_total": hotel_total,
        "flight_price": int(flight_price),
        "extra": extra_total,
        "total": total,
    }


@tool
def estimate_trip_cost(
    city: str,
    nights: int,
    style: str = "relax",
    flight_price: int = 0,
    hotel_price_per_night: int = 0,
    extra: int = 0,
) -> dict[str, object]:
    """Ước tính tổng chi phí chuyến đi (ăn/di chuyển/vé + khách sạn + vé bay + extra)."""
    return _estimate_trip_cost_core(
        city=city,
        nights=nights,
        style=style,
        flight_price=flight_price,
        hotel_price_per_night=hotel_price_per_night,
        extra=extra,
    )


@tool
def plan_trip(
    origin: str,
    destination: str,
    nights: int,
    budget: int,
    style: str = "relax",
    preference_flight: str = "cheap",
    preference_hotel: str = "rating",
) -> dict[str, object]:
    """Lập kế hoạch chuyến đi: chọn flight + hotel phù hợp và ước tính tổng chi phí so với budget."""
    origin = _normalize_city_name_core(origin)
    destination = _normalize_city_name_core(destination)
    destination_city = destination

    if nights < 0:
        nights = 0

    flight = _recommend_flight_core(origin=origin, destination=destination, preference=preference_flight)
    flight_price = int(flight["price"]) if isinstance(flight, dict) and flight.get("ok") and flight.get("price") else 0

    daily_cost = _estimate_daily_cost_core(city=destination_city, style=style)
    living_total = daily_cost * nights

    # Ngân sách còn lại cho khách sạn sau khi trừ vé bay + chi tiêu/ngày + extra (extra để 0 ở đây).
    remaining_for_hotel = int(budget) - int(flight_price) - int(living_total)
    max_hotel_per_night = max(0, remaining_for_hotel // nights) if nights > 0 else 0

    hotel = _recommend_hotel_core(
        city=destination_city,
        max_price_per_night=max_hotel_per_night if max_hotel_per_night > 0 else 9999999,
        preference=preference_hotel,
    )
    hotel_price_per_night = (
        int(hotel["price_per_night"])
        if isinstance(hotel, dict) and hotel.get("ok") and hotel.get("price_per_night") is not None
        else 0
    )

    cost = _estimate_trip_cost_core(
        city=destination_city,
        nights=nights,
        style=style,
        flight_price=flight_price,
        hotel_price_per_night=hotel_price_per_night,
        extra=0,
    )

    total = int(cost.get("total", 0)) if isinstance(cost, dict) else 0
    remaining = int(budget) - total

    return {
        "origin": origin,
        "destination": destination,
        "nights": nights,
        "style": (style or "").strip().lower() or "relax",
        "budget": int(budget),
        "flight": flight,
        "hotel_budget_per_night": int(max_hotel_per_night),
        "hotel": hotel,
        "cost": cost,
        "remaining": remaining,
        "ok": remaining >= 0 and bool(flight.get("ok")) and bool(hotel.get("ok")),
        "notes": (
            "Không đủ ngân sách theo cấu hình hiện tại."
            if remaining < 0
            else "Đã tìm được phương án phù hợp (theo dữ liệu giả lập)."
        ),
    }

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """Tính ngân sách còn lại sau khi trừ các khoản chi, kèm bảng chi tiết."""
    def format_money(value: int) -> str:
        return f"{value:,}".replace(",", ".") + "đ"

    if not expenses.strip():
        remaining = total_budget
        return (
            "Bảng chi phí:\n"
            "  (không có khoản chi nào)\n\n"
            f"Ngân sách ban đầu: {format_money(total_budget)}\n"
            f"Còn lại: {format_money(remaining)}"
        )

    items: dict[str, int] = {}
    parts = [p.strip() for p in expenses.split(",") if p.strip()]

    for part in parts:
        if ":" not in part:
            return (
                "Lỗi: expenses format sai. "
                "Mỗi khoản phải dạng 'ten_khoan:so_tien', ví dụ "
                "'ve_may_bay:890000,khach_san:650000'."
            )
        name, amount_str = part.split(":", 1)
        name = name.strip()
        amount_str = amount_str.strip()
        if not name or not amount_str:
            return (
                "Lỗi: expenses format sai. "
                "Tên khoản và số tiền không được để trống."
            )
        try:
            amount = int(amount_str)
        except ValueError:
            return (
                "Lỗi: expenses format sai. "
                "Số tiền phải là số nguyên, ví dụ 890000."
            )
        items[name] = items.get(name, 0) + amount

    total_expenses = sum(items.values())
    remaining = total_budget - total_expenses

    lines: list[str] = []
    lines.append("Bảng chi phí:")
    for name, amount in items.items():
        pretty_name = name.replace("_", " ")
        lines.append(f"- {pretty_name}: {format_money(amount)}")

    lines.append("")
    lines.append(f"Tổng chi: {format_money(total_expenses)}")
    lines.append(f"Ngân sách ban đầu: {format_money(total_budget)}")

    if remaining >= 0:
        lines.append(f"Còn lại: {format_money(remaining)}")
    else:
        shortage = -remaining
        lines.append(
            f"Vượt ngân sách {format_money(shortage)}! Cần điều chỉnh."
        )

    return "\n".join(lines)