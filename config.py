import os


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# Expressed in km/hr
WALKING_SPEED = 5.0
BUS_SPEED = 40.0
# time taken in minutes for bus to arrive
BUS_ARRIVAL_WAIT_TIME = 3.0
# Time taken in minutes for traffic-light,
# passengers alighting/boarding
STOP_TIME = 1.0

HEAVY_TRAFFIC = 30.0
MODERATE_TRAFFIC = 40.0
NO_TRAFFIC = 60.0

# Application settings
SECRET_KEY = _required_env("SECRET_KEY")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Database
USER = _required_env("POSTGRES_USER")
PASSWORD = _required_env("POSTGRES_PASSWORD")
HOST = _required_env("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE = _required_env("POSTGRES_DATABASE")

# Telegram API
TELEGRAM_API_TOKEN = _required_env("TELEGRAM_API_TOKEN")
TELEGRAM_CHAT_ID = _required_env("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"

# OpenRouteService API
ORS_API_TOKEN = _required_env("ORS_API_TOKEN")

# TomTom traffic API
TOMTOM_API_TOKEN = _required_env("TOMTOM_API_TOKEN")
