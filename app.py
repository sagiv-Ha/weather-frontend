from flask import Flask, render_template_string, request
import requests
import os

app = Flask(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Weather Dashboard</title>
</head>
<body>
    <h1>Weather Dashboard</h1>
    <form method="get" action="/weather">
        <label for="city">Choose a city:</label>
        <select name="city" id="city">
            <option value="newyork">New York</option>
            <option value="sydney">Sydney</option>
            <option value="capetown">Cape Town</option>
            <option value="bangkok">Bangkok</option>
        </select>
        <button type="submit">Get Weather</button>
    </form>

    {% if weather %}
        <h2>Weather Result</h2>
        <p><strong>Temperature:</strong> {{ weather.temperature }} °C</p>
        <p><strong>Description:</strong> {{ weather.description }}</p>
        <p><strong>Humidity:</strong> {{ weather.humidity }}%</p>
        <p><strong>Wind Speed:</strong> {{ weather.wind_speed }} m/s</p>
    {% endif %}

    {% if error %}
        <p><strong>Error:</strong> {{ error }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/weather")
def get_weather():
    city = request.args.get("city")
    response = requests.get(f"{BACKEND_URL}/weather/{city}")

    if response.status_code == 200:
        weather = response.json()
        return render_template_string(HTML_TEMPLATE, weather=weather)

    return render_template_string(HTML_TEMPLATE, error="Could not fetch weather data")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)