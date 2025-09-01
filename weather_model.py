import requests
import config
def predict_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},in&appid={config.WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status() # raises error if API fails
        data = response.json()
        weather = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"]
        }
        return weather
    except requests.exceptions.RequestException as e:
        raise Exception(f"Weather API error: {str(e)}")
