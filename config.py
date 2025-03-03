import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

API_ID = 28811345
API_HASH = "8df803a8832e85ddddcd8c05fe840a05"
BOT_TOKEN = "8176772993:AAFvggynJgPPGBtZpegWn9JdaIusQ4ljC7E"
SESSION_STRING = "BQEM0NgAibaOmefjpSb2Wv2J6zpvM_DgWJFSkpSKWsvvKYNOXtzc1IM0LtFecYEVYPJdzb2AhH4hTcot0AscbQWa1EGrcDbz8gatR0MvOUasVusqnYy3yjmqtMEUqDw8i8YMNxc0yMlpQ0YuP1cCxURWqsBQDfk1A10wJojquQcYsV1R6cxmYBDVFC1NGGj-rmAeicOLwJ4g0oQsgj6cUi0Zpz2wf33Y7ZX4hNDZydheI1c9Cxc5JWmc6o-0aUTVK78QBSqjFeTTtQBqqKg4ZPityyfVc2UMx3s3qACgM1Jq-YB0vJ04NImcFmPe0FyUjZQLrsaNkT9clFZ2tqVt9H_1FQJMrgAAAAHKv59eAA"

SPOTIFY_CLIENT_ID = "1c21247d714244ddbb09925dac565aed"
SPOTIFY_CLIENT_SECRET = "709e1a2969664491b58200860623ef19"

# Function to validate required variables
def check_config():
    required_vars = {
        "API_ID": API_ID,
        "API_HASH": API_HASH,
        "BOT_TOKEN": BOT_TOKEN,
        "SESSION_STRING": SESSION_STRING,
        "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
        "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
    }

    for var, value in required_vars.items():
        if not value:
            raise ValueError(f"Missing required environment variable: {var}")

    print("All required environment variables are set!")

check_config()
