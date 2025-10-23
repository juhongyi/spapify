import os
import base64
import argparse
import logging
import json
from datetime import datetime

import psycopg

from apis import (
    get_access_token,
    send_discord_alert,
    get_new_released_albums,
    get_top_tracks_from_chart,
    insert_data_from_top_tracks,
)


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    handlers=[logging.FileHandler("main.log")],
)


def refresh_access_token(
    client_id: str,
    client_secret: str,
    discord_webhook_id: str,
    discord_webhook_token: str,
) -> None:
    """Refresh Spotify access_token and save to access_token.txt.

    If failed to refresh access_token, it will send alert to Discord webhook.

    Args:
        client_id (str): Spotify Client ID.
        client_secret (str): Spotify Client Secret.
        discord_webhook_id (str): The ID of the Discord webhook.
        discord_webhook_token (str): The token of the Discord webhook.
    """

    try:
        access_token = get_access_token(
            client_string=base64.b64encode(
                f"{client_id}:{client_secret}".encode()
            ).decode()
        )

        with open("access_token.txt", "w") as f:
            f.write(access_token)
            logging.info(
                "access_token refreshed to '%s' and saved to access_token.txt",
                access_token,
            )
    except ValueError:
        logging.error("Failed to get access_token from Spotify after max retries")
        send_discord_alert(
            message="Failed to refresh access_token from Spotify. This job will retry in the next scheduled run (approx. 20 mins).",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )


def get_new_releases(
    access_token: str, discord_webhook_id: str, discord_webhook_token: str
) -> None:
    """Get new released albums from Spotify and save to ./data/get_new_releases.

    Args:
        access_token (str): Spotify access_token.
        discord_webhook_id (str): The ID of the Discord webhook.
        discord_webhook_token (str): The token of the Discord webhook.

    Raises:
        ValueError: If failed to get any new released albums after max retries.
        JSONDecodeError: If failed to save new released albums data to json.
    """

    try:
        # TODO: handle alerts for partial success
        albums = get_new_released_albums(access_token=access_token)

        for etag, data in albums.items():
            os.makedirs("./data/get_new_releases", exist_ok=True)
            with open(f"./data/get_new_releases/{etag}.json", "w") as f:
                json.dump(data, f, indent=2)
                logging.info("Saved new released albums data to %s.json", etag)

            send_discord_alert(
                message=f"Successfully got new released albums from Spotify and saved to ./data/get_new_releases/{etag}.json.",
                discord_webhook_id=discord_webhook_id,
                discord_webhook_token=discord_webhook_token,
            )
    except ValueError:
        logging.error(
            "Failed to get any new released albums from Spotify after max retries"
        )
        send_discord_alert(
            message="Failed to get any new released albums from Spotify.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    except json.JSONDecodeError as e:
        logging.error("Failed to save new released albums data to json: %s", e)
        send_discord_alert(
            message="Failed to save new released albums data to json.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )


def chart_get_top_tracks(
    api_key: str, discord_webhook_id: str, discord_webhook_token: str
) -> None:
    """Get top tracks from Last.fm chart and insert into database.

    Args:
        api_key (str): Last.fm API key.
        discord_webhook_id (str): The ID of the Discord webhook.
        discord_webhook_token (str): The token of the Discord webhook.
    """

    try:
        tracks = get_top_tracks_from_chart(api_key=api_key)
        now = datetime.now().isoformat(timespec="minutes")

        os.makedirs("./data/chart/get_top_tracks", exist_ok=True)
        with open(f"./data/chart/get_top_tracks/{now}.json", "w") as f:
            json.dump(tracks, f, indent=2)
            logging.info("Saved top tracks from Last.fm chart to %s.json", now)

        insert_data_from_top_tracks(top_tracks=tracks["tracks"]["track"])

        logging.info(
            "Successfully got top tracks from Last.fm chart and inserted into database."
        )
        send_discord_alert(
            message="Successfully got top tracks from Last.fm chart and inserted into database.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    except ValueError as e:
        logging.error(e)
        send_discord_alert(
            message="Failed to get top tracks from Last.fm chart.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    except json.JSONDecodeError as e:
        logging.error("Failed to save top tracks data to json: %s", e)
        send_discord_alert(
            message="Failed to save top tracks data to json.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    except KeyError as e:
        logging.error("KeyError from chart.getTopTracks data: %s", e)
        send_discord_alert(
            message="KeyError from chart.getTopTracks data.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    except psycopg.DatabaseError as e:
        logging.error("Database error when inserting data from top tracks: %s", e)
        send_discord_alert(
            message="Database error when inserting data from top tracks.",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )


def main():
    """Main function to parse arguments and execute corresponding job."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--job",
        type=str,
        required=True,
        help="specify the job to run",
        metavar="",
    )
    args = parser.parse_args()

    try:
        client_id = os.environ["SPTFY_CLIENT_ID"]
        client_secret = os.environ["SPTFY_CLIENT_SECRET"]
        lastfm_api_key = os.environ["LSTFM_API_KEY"]
        discord_webhook_id = os.environ["DSCRD_WEBHOOK_ID"]
        discord_webhook_token = os.environ["DSCRD_WEBHOOK_TOKEN"]
    except KeyError as e:
        logging.error("Environment variable not set")
        raise e

    if args.job == "refresh_access_token":
        refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )

    try:
        with open("access_token.txt", "r") as f:
            access_token = f.read()
    except FileNotFoundError as e:
        logging.error("access_token.txt file not found")
        raise e

    if args.job == "get_new_releases":
        get_new_releases(
            access_token=access_token,
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )
    if args.job == "chart_get_top_tracks":
        chart_get_top_tracks(
            api_key=lastfm_api_key,
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )


if __name__ == "__main__":
    main()
