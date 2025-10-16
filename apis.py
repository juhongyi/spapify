import time
import logging

import requests


MAX_RETRIES = 5


def get_access_token(client_string: str) -> str:
    """Get access_token from Spotify API with retries.

    Args:
        client_string (str): Base64 encoded "client_id:client_secret".

    Returns:
        access_token str from Spotify API.

    Raises:
        ValueError: If failed to get access_token after max retries.
    """

    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers={
                    "Authorization": f"Basic {client_string}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )

            if response.status_code == 200:
                response_data = response.json()
                return response_data["access_token"]  # Early return

            logging.warning("Failed to call '/api/token' Spotify endpoint")
            retries += 1

            if retries < MAX_RETRIES:
                time.sleep(2**retries)  # 2, 4, 8, 16, ...
        except KeyError:
            logging.error(
                "access_token not found in response from '/api/token' Spotify endpoint"
            )
        except requests.RequestException as e:
            logging.error(
                "RequestException when calling '/api/token' Spotify endpoint: %s", e
            )

    logging.error("Failed to get access_token from Spotify after max retries")
    raise ValueError("Failed to get access_token from Spotify after max retries")
