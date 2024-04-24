from aiohttp import ClientSession

from .exception import OWMException
from .weather import HourlyWeather, DailyWeather, WeatherReport

API_URL = 'https://api.openweathermap.org/data/3.0/onecall'
WEATHER_TYPES = {'current', 'minutely', 'hourly', 'daily', 'alerts'}


class OWMClient:
    session: ClientSession | None = None
    request_timeout: int = 10

    def __init__(self, api_key, units):
        self.api_key = api_key
        self.units = units

    async def one_call(self, lat, lon, weather_types=None):
        if weather_types is None:
            exclude_weather_types = {}
        else:
            exclude_weather_types = WEATHER_TYPES - set(weather_types)

        url = self._get_url(lat, lon, exclude_weather_types)
        json_response = await self._request(url)

        current, hourly, daily = None, None, None
        if json_response.get('current') is not None:
            current = HourlyWeather.from_dict(json_response['current'])
        if json_response.get('hourly') is not None:
            hourly = [HourlyWeather.from_dict(item) for item in json_response['hourly']]
        if json_response.get('daily') is not None:
            daily = [DailyWeather.from_dict(item) for item in json_response['daily']]

        return WeatherReport(current, hourly, daily)

    async def validate_key(self):
        url = self._get_url(50.06, 14.44, WEATHER_TYPES)
        await self._request(url)

    async def _request(self, url):
        print(url)
        async with ClientSession() as session:
            try:
                async with session.get(url=url, timeout=self.request_timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise OWMException("Unauthorized")
                    elif response.status == 404:
                        raise OWMException("Not Found")
                    elif response.status == 429:
                        raise OWMException("Too Many Requests")
                    else:
                        raise OWMException("Unknown Error")
            except TimeoutError:
                raise OWMException("Request timeout")

    def _get_url(self, lat, lon, exclude):
        return (f"{API_URL}?"
                f"lat={lat}&"
                f"lon={lon}&"
                f"appid={self.api_key}&"
                f"units={self.units}&"
                f"exclude={','.join(exclude)}")
