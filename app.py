from flask import Flask, render_template_string, request
import os

import requests
from datetime import datetime

app = Flask(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
DEFAULT_CITY = "newyork"

CITY_OPTIONS = {
    "newyork": {
        "name": "New York",
        "name_he": "ניו יורק",
        "country": "United States",
        "timezone": "UTC-4",
        "accent": "#60a5fa",
        "emoji": "🌆",
    },
    "sydney": {
        "name": "Sydney",
        "name_he": "סידני",
        "country": "Australia",
        "timezone": "UTC+10",
        "accent": "#22d3ee",
        "emoji": "🌊",
    },
    "capetown": {
        "name": "Cape Town",
        "name_he": "קייפ טאון",
        "country": "South Africa",
        "timezone": "UTC+2",
        "accent": "#4ade80",
        "emoji": "⛰️",
    },
    "bangkok": {
        "name": "Bangkok",
        "name_he": "בנגקוק",
        "country": "Thailand",
        "timezone": "UTC+7",
        "accent": "#fb7185",
        "emoji": "🌃",
    },
}

WEATHER_VISUALS = {
    "clear": {"icon": "☀️", "label": "בהיר"},
    "clouds": {"icon": "☁️", "label": "מעונן"},
    "rain": {"icon": "🌧️", "label": "גשום"},
    "storm": {"icon": "⛈️", "label": "סוער"},
    "snow": {"icon": "❄️", "label": "שלג"},
    "mist": {"icon": "🌫️", "label": "ערפל"},
    "calm": {"icon": "🌤️", "label": "רגוע"},
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>WeatherPro - תחזית ערים</title>
    <style>
        :root {
            color-scheme: dark;
            --bg: #070a12;
            --surface: #0d111c;
            --surface-2: #121826;
            --surface-3: #182033;
            --text: #f8fafc;
            --text-soft: #cbd5e1;
            --muted: #94a3b8;
            --line: rgba(148, 163, 184, 0.18);
            --accent: {{ city.accent }};
            --shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        }

        * { box-sizing: border-box; }

        html { min-height: 100%; }

        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 22%, transparent), transparent 34rem),
                linear-gradient(180deg, #0b1020 0%, var(--bg) 54%, #050711 100%);
            color: var(--text);
        }

        body::before {
            content: "";
            position: fixed;
            inset: 0;
            z-index: -1;
            background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
            background-size: 56px 56px;
            mask-image: linear-gradient(to bottom, black, transparent 78%);
            pointer-events: none;
        }

        button, select { font: inherit; }
        a { color: inherit; text-decoration: none; }

        .page {
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 28px 0 36px;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 34px;
        }

        .brand {
            display: inline-flex;
            align-items: center;
            gap: 12px;
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            background: var(--surface-2);
            border: 1px solid var(--line);
            color: var(--accent);
            font-weight: 900;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.05);
        }

        .brand-title, .brand-subtitle { margin: 0; }
        .brand-title { font-size: 1rem; font-weight: 800; letter-spacing: -.02em; }
        .brand-subtitle { margin-top: 2px; color: var(--muted); font-size: .86rem; }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            padding: 9px 13px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(13, 17, 28, .72);
            color: var(--text-soft);
            font-size: .9rem;
            white-space: nowrap;
        }

        .status-clock,
        .status-user-clock {
            margin-left: 10px;
            color: var(--text);
            font-weight: 700;
            white-space: nowrap;
        }

        .status-user-clock::before {
            content: "הזמן שלי:";
            margin-right: 6px;
            color: var(--muted);
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 5px rgba(34,197,94,.12);
        }

        .layout {
            display: grid;
            grid-template-columns: 330px minmax(0, 1fr);
            gap: 18px;
            align-items: stretch;
        }

        .panel {
            border: 1px solid var(--line);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(18,24,38,.94), rgba(13,17,28,.94));
            box-shadow: var(--shadow);
        }

        .sidebar { padding: 18px; }

        .section-title {
            margin: 0 0 14px;
            font-size: .86rem;
            color: var(--muted);
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .selector {
            display: grid;
            gap: 12px;
            margin-bottom: 18px;
        }

        .select-wrap { position: relative; }
        .select-wrap::after {
            content: "⌄";
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--muted);
            pointer-events: none;
        }

        select {
            width: 100%;
            min-height: 50px;
            padding: 0 14px 0 42px;
            appearance: none;
            color: var(--text);
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            outline: none;
        }

        select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 18%, transparent);
        }

        .button {
            min-height: 50px;
            border: 0;
            border-radius: 16px;
            color: #07101f;
            background: var(--accent);
            font-weight: 900;
            cursor: pointer;
            transition: transform .18s ease, filter .18s ease;
        }

        .button:hover { transform: translateY(-1px); filter: brightness(1.07); }

        .city-list {
            display: grid;
            gap: 10px;
            margin-top: 16px;
        }

        .city-card {
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 12px;
            min-height: 66px;
            padding: 12px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: rgba(7,10,18,.34);
            transition: border-color .18s ease, background .18s ease, transform .18s ease;
        }

        .city-card:hover, .city-card.active {
            border-color: color-mix(in srgb, var(--item-accent) 52%, var(--line));
            background: color-mix(in srgb, var(--item-accent) 12%, var(--surface));
            transform: translateX(-2px);
        }

        .city-emoji { font-size: 1.35rem; }
        .city-name { display: block; font-weight: 850; }
        .city-meta { display: block; margin-top: 3px; color: var(--muted); font-size: .82rem; }
        .city-tz { color: var(--muted); font-size: .78rem; direction: ltr; }

        .weather {
            padding: 28px;
            min-height: 590px;
            position: relative;
            overflow: hidden;
        }

        .weather::after {
            content: "";
            position: absolute;
            width: 340px;
            height: 340px;
            left: -120px;
            top: -120px;
            border-radius: 50%;
            background: color-mix(in srgb, var(--accent) 18%, transparent);
            filter: blur(14px);
            pointer-events: none;
        }

        .weather-inner {
            position: relative;
            z-index: 1;
            min-height: 100%;
            display: grid;
            gap: 24px;
            align-content: space-between;
        }

        .hero {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 22px;
            align-items: start;
        }

        .hero > div:last-child {
            display: grid;
            gap: 12px;
            justify-items: center;
            text-align: center;
        }

        .icon-status {
            margin: 0;
            color: var(--text-soft);
            font-weight: 700;
            font-size: .95rem;
            max-width: 180px;
            word-break: break-word;
        }

        .kicker {
            margin: 0;
            color: var(--accent);
            font-weight: 900;
            font-size: .92rem;
        }

        h1 {
            margin: 0;
            font-size: clamp(2.4rem, 5vw, 5.3rem);
            line-height: .94;
            letter-spacing: -.08em;
        }

        .description {
            margin: 16px 0 0;
            max-width: 560px;
            color: var(--text-soft);
            font-size: 1.08rem;
            line-height: 1.7;
        }

        .weather-icon {
            width: 132px;
            height: 132px;
            display: grid;
            place-items: center;
            border: 1px solid var(--line);
            border-radius: 30px;
            background: rgba(255,255,255,.04);
            font-size: 4.8rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
        }

        .temperature {
            display: flex;
            align-items: flex-start;
            justify-content: flex-start;
            direction: ltr;
            gap: 10px;
        }

        .temperature strong {
            font-size: clamp(5rem, 13vw, 10rem);
            line-height: .85;
            letter-spacing: -.08em;
        }

        .temperature span {
            margin-top: 10px;
            color: var(--muted);
            font-size: 1.6rem;
            font-weight: 800;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }

        .metric {
            min-height: 112px;
            padding: 16px;
            border: 1px solid var(--line);
            border-radius: 20px;
            background: rgba(7,10,18,.38);
        }

        .metric span {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--muted);
            font-size: .84rem;
            font-weight: 750;
        }

        .metric-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 8px;
            background: rgba(255,255,255,.06);
            color: var(--accent);
            font-size: 0.95rem;
        }

        .metric strong {
            display: block;
            margin-top: 18px;
            color: var(--text);
            font-size: 1.28rem;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .notice {
            padding: 18px;
            border: 1px solid var(--line);
            border-radius: 20px;
            background: rgba(7,10,18,.38);
            color: var(--text-soft);
            line-height: 1.7;
        }

        .notice.error {
            color: #fecaca;
            border-color: rgba(248,113,113,.36);
            background: rgba(127,29,29,.18);
        }

        .empty-cities {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }

        .empty-city {
            padding: 16px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: rgba(7,10,18,.32);
        }

        .empty-city span { color: var(--muted); font-size: .8rem; }
        .empty-city strong { display: block; margin-top: 8px; }

        @media (max-width: 900px) {
            .layout { grid-template-columns: 1fr; }
            .weather { min-height: auto; }
        }

        @media (max-width: 640px) {
            .page { width: min(100% - 22px, 1120px); padding-top: 18px; }
            .topbar, .hero { align-items: stretch; display: grid; grid-template-columns: 1fr; }
            .status-pill { width: max-content; }
            .weather, .sidebar { padding: 16px; border-radius: 22px; }
            .weather-icon { width: 104px; height: 104px; font-size: 3.8rem; }
            .metrics, .empty-cities { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <main class="page">
        <header class="topbar" aria-label="WeatherPro">
            <a class="brand" href="/" aria-label="WeatherPro home">
                <span class="brand-mark">W</span>
                <span>
                    <span class="brand-title">WeatherPro</span>
                    <span class="brand-subtitle">תחזית ערים בזמן אמת</span>
                </span>
            </a>

            <div class="status-pill" aria-label="Location and local time">
                <span class="status-dot" aria-hidden="true"></span>
                <span>{{ city.country }} · {{ city.timezone }}</span>
                <span class="status-clock" id="city-clock">--:--:--</span>
                <span class="status-user-clock" id="user-clock">--:--:--</span>
            </div>
        </header>

        <div class="layout">
            <aside class="panel sidebar" aria-label="בחירת עיר">
                <p class="section-title">בחר עיר</p>

                <form class="selector" method="get" action="/weather">
                    <div class="select-wrap">
                        <select name="city" id="city" aria-label="עיר" onchange="this.form.submit()">
                            {% for key, option in city_options.items() %}
                            <option value="{{ key }}" {% if key == selected_city %}selected{% endif %}>
                                {{ option.name_he }} · {{ option.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                </form>

                <nav class="city-list" aria-label="ערים זמינות">
                    {% for key, option in city_options.items() %}
                    <a class="city-card {% if key == selected_city %}active{% endif %}"
                       style="--item-accent: {{ option.accent }}"
                       href="/weather?city={{ key }}">
                        <span class="city-emoji" aria-hidden="true">{{ option.emoji }}</span>
                        <span>
                            <span class="city-name">{{ option.name_he }}</span>
                            <span class="city-meta">{{ option.name }}, {{ option.country }}</span>
                        </span>
                        <span class="city-tz">{{ option.timezone }}</span>
                    </a>
                    {% endfor %}
                </nav>
            </aside>

            <section class="panel weather" aria-labelledby="forecast-title">
                <div class="weather-inner">
                    <div class="hero">
                        <div>
                            <h1 id="forecast-title">{{ city.name_he }}</h1>
                            <p class="description">{{ description }}</p>
                        </div>
                        <div>
                            <div class="weather-icon" aria-label="{{ visual.label }}">
                                {% if weather and weather.icon_url %}
                                    <img src="{{ weather.icon_url }}" alt="{{ visual.label }}" style="width:100%;height:100%;object-fit:contain;border-radius:20px;" />
                                {% else %}
                                    {{ visual.icon }}
                                {% endif %}
                            </div>
                            <p class="icon-status">{{ weather.description or visual.label }}</p>
                            <p class="kicker">{{ city.name }}</p>
                        </div>
                    </div>

                    {% if weather %}
                    <div class="temperature" aria-label="טמפרטורה">
                        <strong>{{ temperature_value }}</strong>
                        <span>°C</span>
                    </div>

                    <div class="metrics" aria-label="מדדי מזג אוויר">
                        {% for metric in metrics %}
                        <article class="metric">
                            <span><span class="metric-icon">{{ metric.icon or 'ℹ️' }}</span>{{ metric.label }}</span>
                            <strong>{{ metric.value }}</strong>
                        </article>
                        {% endfor %}
                    </div>
                    {% elif error %}
                    <div class="notice error">
                        <strong>שגיאה:</strong> {{ error }}
                    </div>
                    {% else %}
                    <div class="empty-cities" aria-label="ערים נתמכות">
                        {% for key, option in city_options.items() %}
                        <div class="empty-city">
                            <span>{{ option.timezone }}</span>
                            <strong>{{ option.emoji }} {{ option.name_he }}</strong>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </section>
        </div>
    </main>
    <script>
        (function() {
            var cityClock = document.getElementById('city-clock');
            var userClock = document.getElementById('user-clock');
            if (!cityClock) return;
            var tz = '{{ city.timezone }}';
            var offset = 0;
            var match = tz.match(/UTC\s*([+-]?\d+)(?:\.(\d+))?/i);
            if (match) {
                offset = parseFloat(match[1] + (match[2] ? '.' + match[2] : ''));
            }
            var userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
            if (userClock) {
                userClock.setAttribute('title', userTimeZone);
            }
            function formatTime(date) {
                var hours = String(date.getHours()).padStart(2, '0');
                var minutes = String(date.getMinutes()).padStart(2, '0');
                var seconds = String(date.getSeconds()).padStart(2, '0');
                return hours + ':' + minutes + ':' + seconds;
            }
            function updateClock() {
                var now = new Date();
                var utc = now.getTime() + (now.getTimezoneOffset() * 60000);
                var local = new Date(utc + offset * 3600000);
                cityClock.textContent = formatTime(local);
                if (userClock) {
                    userClock.textContent = formatTime(now);
                }
            }
            updateClock();
            setInterval(updateClock, 1000);
        })();
    </script>
</body>
</html>
"""


def normalize_city(city):
    if city in CITY_OPTIONS:
        return city
    return DEFAULT_CITY


def mood_from_description(description):
    text = (description or "").lower()

    if any(term in text for term in ("storm", "thunder", "lightning")):
        return "storm"
    if any(term in text for term in ("rain", "drizzle", "shower")):
        return "rain"
    if any(term in text for term in ("snow", "sleet", "hail")):
        return "snow"
    if any(term in text for term in ("cloud", "overcast")):
        return "clouds"
    if any(term in text for term in ("mist", "fog", "haze", "smoke")):
        return "mist"
    if any(term in text for term in ("clear", "sun")):
        return "clear"
    return "calm"


def metric_value(value, suffix=""):
    if value is None or value == "":
        return "N/A"
    return f"{value}{suffix}"


def build_metrics(weather):
    # format sunrise/sunset timestamps to HH:MM if present
    sunrise = weather.get("sunrise")
    sunset = weather.get("sunset")
    try:
        sunrise_fmt = datetime.utcfromtimestamp(int(sunrise)).strftime("%H:%M") if sunrise else None
    except Exception:
        sunrise_fmt = None
    try:
        sunset_fmt = datetime.utcfromtimestamp(int(sunset)).strftime("%H:%M") if sunset else None
    except Exception:
        sunset_fmt = None

    return [
        {"label": "מרגיש כמו", "value": metric_value(weather.get("feels_like"), "°C"), "icon": "🌡️"},
        {"label": "טמפרטורה מינימלית", "value": metric_value(weather.get("temp_min"), "°C"), "icon": "❄️"},
        {"label": "טמפרטורה מקסימלית", "value": metric_value(weather.get("temp_max"), "°C"), "icon": "🔥"},
        {"label": "לחות", "value": metric_value(weather.get("humidity"), "%"), "icon": "💧"},
        {"label": "רוח", "value": metric_value(weather.get("wind_speed"), " m/s"), "icon": "💨"},
        {"label": "כיוון רוח", "value": metric_value(weather.get("wind_deg"), "°"), "icon": "🧭"},
        {"label": "גלים/שבירות רוח", "value": metric_value(weather.get("wind_gust"), " m/s"), "icon": "🌬️"},
        {"label": "לחץ", "value": metric_value(weather.get("pressure"), " hPa"), "icon": "🧪"},
        {"label": "ראות", "value": metric_value(weather.get("visibility"), " km"), "icon": "🌁"},
        {"label": "עננות", "value": metric_value(weather.get("cloudiness"), "%"), "icon": "☁️"},
        {"label": "זריחה", "value": metric_value(sunrise_fmt), "icon": "🌅"},
        {"label": "שקיעה", "value": metric_value(sunset_fmt), "icon": "🌇"},
    ]


def render_dashboard(selected_city=DEFAULT_CITY, weather=None, error=None):
    selected_city = normalize_city(selected_city)
    city = CITY_OPTIONS[selected_city]
    description = "בחר עיר כדי להציג תחזית עדכנית."
    temperature_value = "N/A"
    metrics = []
    mood = "calm"

    if weather:
        description = metric_value(weather.get("description"))
        temperature_value = metric_value(weather.get("temperature"))
        metrics = build_metrics(weather)
        mood = mood_from_description(weather.get("description"))
    elif error:
        description = "שירות הנתונים אינו זמין כרגע."

    return render_template_string(
        HTML_TEMPLATE,
        city=city,
        city_count=len(CITY_OPTIONS),
        city_options=CITY_OPTIONS,
        description=description,
        error=error,
        metrics=metrics,
        mood=mood,
        selected_city=selected_city,
        temperature_value=temperature_value,
        visual=WEATHER_VISUALS.get(mood, WEATHER_VISUALS["calm"]),
        weather=weather,
    )


@app.route("/")
def home():
    return render_dashboard()


@app.route("/weather")
def get_weather():
    city = normalize_city(request.args.get("city"))

    try:
        response = requests.get(f"{BACKEND_URL}/weather/{city}", timeout=6)
    except requests.RequestException:
        return render_dashboard(
            selected_city=city,
            error="לא ניתן להתחבר לשירות מזג האוויר.",
        )

    if response.status_code == 200:
        weather = response.json()
        if isinstance(weather, dict):
            return render_dashboard(selected_city=city, weather=weather)

        return render_dashboard(
            selected_city=city,
            error="שירות מזג האוויר החזיר מבנה נתונים לא צפוי.",
        )

    return render_dashboard(
        selected_city=city,
        error="לא ניתן לטעון נתוני מזג אוויר עבור העיר שנבחרה.",
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
