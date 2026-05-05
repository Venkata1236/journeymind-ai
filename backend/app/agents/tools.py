from crewai.tools import BaseTool
from pydantic import Field
from app.rag.retriever import search_by_city_and_category
from app.core.config import get_settings
from loguru import logger

settings = get_settings()

# ─── Mock Data ────────────────────────────────────────────────────────────────

WEATHER_MOCK = {
    "jaipur":    {"temp": "28-38°C", "condition": "Hot and dry",      "rain_risk": "Low",    "tip": "Carry sunscreen and a hat. Visit forts before 9am."},
    "jodhpur":   {"temp": "26-36°C", "condition": "Hot and sunny",    "rain_risk": "Low",    "tip": "Light cotton clothes. Blue City looks best at golden hour."},
    "udaipur":   {"temp": "25-35°C", "condition": "Pleasant",         "rain_risk": "Low",    "tip": "Evenings by the lake are cooler — carry a light jacket."},
    "jaisalmer": {"temp": "30-42°C", "condition": "Very hot and dry", "rain_risk": "Very Low","tip": "Desert safari early morning only. Avoid afternoon outdoor activity."},
    "agra":      {"temp": "27-38°C", "condition": "Hot and humid",    "rain_risk": "Medium", "tip": "Taj Mahal at sunrise — avoid midday heat and crowds."},
    "kerala":    {"temp": "24-32°C", "condition": "Humid and green",  "rain_risk": "High",   "tip": "Pack rain gear. Houseboat bookings need advance notice."},
    "goa":       {"temp": "26-33°C", "condition": "Warm and breezy",  "rain_risk": "Medium", "tip": "North Goa for nightlife, South Goa for peace and beaches."},
    "mumbai":    {"temp": "27-34°C", "condition": "Humid",            "rain_risk": "High",   "tip": "Local trains are fastest. Avoid peak hours 8-10am, 5-8pm."},
    "delhi":     {"temp": "25-40°C", "condition": "Hot and polluted", "rain_risk": "Low",    "tip": "Metro is the best way to move. Check AQI before outdoor plans."},
    "manali":    {"temp": "5-18°C",  "condition": "Cold and scenic",  "rain_risk": "Medium", "tip": "Carry heavy woolens. Road to Rohtang may be closed."},
}

CURRENCY_MOCK = {
    "usd_rate": 0.012,
    "eur_rate": 0.011,
    "gbp_rate": 0.0095,
}


# ─── Tool 1: WeatherTool ──────────────────────────────────────────────────────

class WeatherTool(BaseTool):
    name: str = "WeatherTool"
    description: str = (
        "Get weather information for an Indian travel destination. "
        "Returns temperature range, condition, rain risk, and packing tip. "
        "Input: city name e.g. 'Jaipur', 'Kerala', 'Manali'"
    )

    def _run(self, city: str) -> str:
        city_key = city.lower().strip()

        if settings.weather_api_key:
            try:
                import requests
                url = (
                    f"http://api.openweathermap.org/data/2.5/weather"
                    f"?q={city},IN&appid={settings.weather_api_key}&units=metric"
                )
                response = requests.get(url, timeout=5)
                data = response.json()
                if response.status_code == 200:
                    temp = data["main"]["temp"]
                    condition = data["weather"][0]["description"].capitalize()
                    humidity = data["main"]["humidity"]
                    logger.info(f"WeatherTool: live data for {city}")
                    return (
                        f"Weather in {city}: {temp}°C, {condition}. "
                        f"Humidity: {humidity}%."
                    )
            except Exception as e:
                logger.warning(f"WeatherTool: live API failed for {city} — falling back to mock. Error: {e}")

        data = WEATHER_MOCK.get(city_key)
        if not data:
            logger.warning(f"WeatherTool: no mock data for '{city}'")
            return (
                f"Weather in {city}: Typically 25-35°C during travel season. "
                f"Rain risk: Moderate. Tip: Check local forecast before departure."
            )

        logger.info(f"WeatherTool: mock data for {city}")
        return (
            f"Weather in {city}: {data['temp']}, {data['condition']}. "
            f"Rain risk: {data['rain_risk']}. "
            f"Packing tip: {data['tip']}"
        )


# ─── Tool 2: CurrencyTool ─────────────────────────────────────────────────────

class CurrencyTool(BaseTool):
    name: str = "CurrencyTool"
    description: str = (
        "Convert an INR amount to USD, EUR, and GBP for international reference. "
        "Input: amount in INR as a string e.g. '80000'"
    )

    def _run(self, amount_inr: str) -> str:
        try:
            amount = float(str(amount_inr).replace(",", "").strip())
        except ValueError:
            return f"Invalid amount: {amount_inr}"

        if settings.currency_api_key:
            try:
                import requests
                url = (
                    f"https://v6.exchangerate-api.com/v6/{settings.currency_api_key}"
                    f"/latest/INR"
                )
                response = requests.get(url, timeout=5)
                data = response.json()
                if response.status_code == 200:
                    rates = data["conversion_rates"]
                    usd = round(amount * rates.get("USD", CURRENCY_MOCK["usd_rate"]), 2)
                    eur = round(amount * rates.get("EUR", CURRENCY_MOCK["eur_rate"]), 2)
                    gbp = round(amount * rates.get("GBP", CURRENCY_MOCK["gbp_rate"]), 2)
                    logger.info(f"CurrencyTool: live rates used")
                    return f"₹{amount:,.0f} = ${usd} USD | €{eur} EUR | £{gbp} GBP (live rates)"
            except Exception as e:
                logger.warning(f"CurrencyTool: live API failed — falling back to mock. Error: {e}")

        usd = round(amount * CURRENCY_MOCK["usd_rate"], 2)
        eur = round(amount * CURRENCY_MOCK["eur_rate"], 2)
        gbp = round(amount * CURRENCY_MOCK["gbp_rate"], 2)
        logger.info(f"CurrencyTool: mock rates for ₹{amount}")
        return f"₹{amount:,.0f} = ${usd} USD | €{eur} EUR | £{gbp} GBP (approximate rates)"


# ─── Tool 3: AttractionTool ───────────────────────────────────────────────────

class AttractionTool(BaseTool):
    name: str = "AttractionTool"
    description: str = (
        "Find top attractions and experiences for a city and category using travel reviews. "
        "Input format: 'city|category' e.g. 'Jaipur|heritage', 'Udaipur|food', 'Jodhpur|adventure'. "
        "Categories: heritage, food, adventure, shopping, nature, culture, nightlife"
    )

    def _run(self, city_and_category: str) -> str:
        try:
            parts = city_and_category.split("|")
            if len(parts) != 2:
                return "Invalid input format. Use 'city|category' e.g. 'Jaipur|heritage'"

            city = parts[0].strip()
            category = parts[1].strip()

            logger.info(f"AttractionTool: searching {city} | {category}")
            results = search_by_city_and_category(city=city, category=category, top_k=5)

            if not results:
                logger.warning(f"AttractionTool: no results for {city}|{category}")
                return (
                    f"No specific reviews found for {category} in {city}. "
                    f"Recommend researching: top {category} spots in {city} India."
                )

            output_lines = [f"Top {category} experiences in {city} (from traveler reviews):"]
            for i, result in enumerate(results, 1):
                output_lines.append(
                    f"{i}. {result['destination']} — Category: {result['category']} "
                    f"| Rating: {result['rating']}/4 | {result['combined_text'][:200]}"
                )

            logger.info(f"AttractionTool: returned {len(results)} results for {city}|{category}")
            return "\n".join(output_lines)

        except Exception as e:
            logger.error(f"AttractionTool error: {e}")
            return f"Error retrieving attractions for {city_and_category}: {str(e)}"