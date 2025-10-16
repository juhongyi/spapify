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
        except KeyError:
            logging.warning(
                "access_token not found in response from '/api/token' Spotify endpoint"
            )
        except requests.RequestException as e:
            logging.warning(
                "RequestException when calling '/api/token' Spotify endpoint: %s", e
            )
        finally:
            logging.warning("Failed to call '/api/token' Spotify endpoint")
            retries += 1

            if retries < MAX_RETRIES:
                time.sleep(2**retries)  # 2, 4, 8, 16, ...

    logging.error("Failed to get access_token from Spotify after max retries")
    raise ValueError("Failed to get access_token from Spotify after max retries")


def send_discord_alert(
    discord_webhook_id: str, discord_webhook_token: str, message: str
) -> None:
    """Send alert message to Discord webhook with retries.

    If failed to send alert after max retries, it will just 'log' an error.

    Args:
        discord_webhook_id (str): The ID of the Discord webhook.
        discord_webhook_token (str): The token of the Discord webhook.
        message (str): The alert message to send.
    """

    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.post(
                f"https://discord.com/api/webhooks/{discord_webhook_id}/{discord_webhook_token}",
                json={"content": message},
            )

            if response.status_code == 200:
                logging.info(
                    "Successfully sent Discord alert with message: %s", message
                )
                return  # Early return
        except requests.RequestException as e:
            logging.warning("RequestException when calling Discord webhook: %s", e)
        finally:
            logging.warning("Failed to send Discord alert with message: %s", message)
            retries += 1

            if retries < MAX_RETRIES:
                time.sleep(2**retries)  # 2, 4, 8, 16, ...

    logging.error("Failed to send Discord alert after max retries")
