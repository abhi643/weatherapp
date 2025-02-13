from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# API configurations
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
    url = f"{HISTORY_BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units={units}"
    historical_data = []
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            # Group data by day
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
            historical_data = historical_data[:5]
            
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        
    return historical_data

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    if request.method == "POST":
        location = request.form['location']
        temperature_unit = request.form['unit']
        units = 'metric' if temperature_unit == 'Celsius' else 'imperial'

        # Get current weather
        url = f"{WEATHER_BASE_URL}?q={location}&appid={API_KEY}&units={units}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if data.get('cod') == 200:
                # Get historical data using coordinates
                lat, lon = data['coord']['lat'], data['coord']['lon']
                historical_data = get_historical_weather(lat, lon, units)
                
                weather_data = {
                    "current": {
                        "temperature": round(data['main']['temp']),
                        "feels_like": round(data['main']['feels_like']),
                        "humidity": data['main']['humidity'],
                        "wind_speed": data['wind']['speed'],
                        "description": data['weather'][0]['description'].capitalize(),
                        "icon": get_weather_icon(data['weather'][0]['icon']),
                        "location": location,
                        "unit": temperature_unit,
                        "pressure": data['main']['pressure'],
                        "visibility": data.get('visibility', 0) / 1000,  # Convert to km
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                    },
                    "historical": historical_data
                }
            else:
                weather_data = {"error": "Location not found!"}
                
        except Exception as e:
            weather_data = {"error": f"An error occurred: {str(e)}"}
    
    return render_template("index.html", weather_data=weather_data)

if __name__ == "__main__":
    app.run(debug=True)