from flask import Flask, render_template, request
import requests
from os import environ
from datetime import datetime
import urllib.parse

app = Flask(__name__)

API_KEY = '8770eb080a4e03b0eb4cdcbb9bb6deee'
WEATHER_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
HISTORY_BASE_URL = 'http://api.openweathermap.org/data/2.5/forecast'

def get_weather_icon(code):
    """Map weather codes to weather icons"""
    icons = {
        '01': 'sun',
        '02': 'cloud-sun',
        '03': 'cloud',
        '04': 'clouds',
        '09': 'cloud-rain',
        '10': 'cloud-showers-heavy',
        '11': 'cloud-bolt',
        '13': 'snowflake',
        '50': 'smog'
    }
    return icons.get(code[:2], 'question')

def get_historical_weather(lat, lon, units):
    """Fetch 5-day forecast data and use it for historical visualization"""
    try:
        url = f"{HISTORY_BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units={units}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        historical_data = []
        daily_data = {}
        
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'humidity': [],
                    'wind_speed': [],
                    'descriptions': [],
                    'icons': []
                }
            
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['humidity'].append(item['main']['humidity'])
            daily_data[date]['wind_speed'].append(item['wind']['speed'])
            daily_data[date]['descriptions'].append(item['weather'][0]['description'])
            daily_data[date]['icons'].append(item['weather'][0]['icon'])
        
        # Calculate daily averages
        for date, day_data in daily_data.items():
            if day_data['temps']:  # Check if we have data for this day
                historical_data.append({
                    'date': date,
                    'temp': round(sum(day_data['temps']) / len(day_data['temps']), 1),
                    'temp_min': round(min(day_data['temps']), 1),
                    'temp_max': round(max(day_data['temps']), 1),
                    'humidity': round(sum(day_data['humidity']) / len(day_data['humidity'])),
                    'wind_speed': round(sum(day_data['wind_speed']) / len(day_data['wind_speed']), 1),
                    'description': max(set(day_data['descriptions']), key=day_data['descriptions'].count),
                    'icon': get_weather_icon(max(set(day_data['icons']), key=day_data['icons'].count))
                })
        
        # Sort by date and limit to 5 days
        historical_data.sort(key=lambda x: x['date'])
        return historical_data[:5]
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    if request.method == "POST":
        try:
            if not API_KEY:
                raise ValueError("API key not configured")
            
            temperature_unit = request.form.get('unit', 'Celsius')
            units = 'metric' if temperature_unit == 'Celsius' else 'imperial'
            location = request.form.get('location')
            
            if not location:
                raise ValueError("Please enter a location")
            
            # URL encode the location and construct the URL properly
            encoded_location = urllib.parse.quote(location)
            url = f"{WEATHER_BASE_URL}?q={encoded_location}&appid={API_KEY}&units={units}"
            
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            # Get historical data using coordinates from the response
            lat = data['coord']['lat']
            lon = data['coord']['lon']
            historical_data = get_historical_weather(lat, lon, units)
            
            weather_data = {
                "current": {
                    "temperature": round(data['main']['temp']),
                    "feels_like": round(data['main']['feels_like']),
                    "humidity": data['main']['humidity'],
                    "wind_speed": data['wind']['speed'],
                    "description": data['weather'][0]['description'].capitalize(),
                    "icon": get_weather_icon(data['weather'][0]['icon']),
                    "location": data['name'],
                    "unit": temperature_unit,
                    "pressure": data['main']['pressure'],
                    "visibility": data.get('visibility', 0) / 1000,
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                "historical": historical_data
            }
                
        except requests.exceptions.RequestException as e:
            weather_data = {"error": "Unable to fetch weather data. Please try again."}
        except KeyError as e:
            weather_data = {"error": "Invalid data received from weather service."}
        except Exception as e:
            weather_data = {"error": f"An error occurred: {str(e)}"}
    
    return render_template("index.html", weather_data=weather_data)

if __name__ == '__main__':
    app.run(debug=True)