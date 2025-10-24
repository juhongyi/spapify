import os
import time
import logging
from datetime import datetime

import requests
import psycopg


MAX_RETRIES = 5

DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]


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

            if response.ok:
                response_data = response.json()
                return response_data["access_token"]  # Early return

            logging.warning("Response not OK from '/api/token' Spotify endpoint")
        except KeyError:
            logging.warning(
                "access_token not found in response from '/api/token' Spotify endpoint"
            )
        except requests.RequestException as e:
            logging.warning(
                "RequestException when calling '/api/token' Spotify endpoint: %s", e
            )

        retries += 1
        if retries < MAX_RETRIES:
            time.sleep(2**retries)  # 2, 4, 8, 16, ...

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

            if response.ok:
                logging.info(
                    "Successfully sent Discord alert with message: %s", message
                )
                return  # Early return

            logging.warning("Response not OK when sending Discord webhook alert")
        except requests.RequestException as e:
            logging.warning("RequestException when calling Discord webhook: %s", e)

        retries += 1
        if retries < MAX_RETRIES:
            time.sleep(2**retries)  # 2, 4, 8, 16, ...

    logging.error("Failed to send Discord alert after max retries")


def get_new_released_albums(
    access_token: str,
) -> dict[str, dict]:
    """Get new released albums from Spotify API with retries.

    Args:
        access_token (str): Spotify access_token.

    Returns:
        A dictionary mapping ETag to the albums data from Spotify API.
        Possibly partially complete if some page(s) failed after max retries.
        Typically, the pages are limited to two pages, and items per page is 50.
        For example: {
            "etag1": {albums data 1},
            "etag2": {albums data 2},
        }

    Raises:
        ValueError: If failed to get any new released albums after max retries.
    """

    retries = 0
    entire_albums = {}
    url = "https://api.spotify.com/v1/browse/new-releases?limit=50"  # Max limit is 50

    while retries < MAX_RETRIES:
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.ok:
                response_data = response.json()
                albums = response_data["albums"]
                etag = response.headers["ETag"]  # Case insensitive
                etag = etag.strip('"')
                entire_albums[etag] = albums

                next_url = albums.get("next")
                if next_url is None:
                    return entire_albums  # Happy path: entire url calls succeeded

                url = next_url
                retries = 0  # Reset retries for the next url page
                continue

            logging.warning(
                "Response not OK from '/browse/new-releases' Spotify endpoint"
            )
        except KeyError as e:
            logging.warning("KeyError when parsing response from Spotify: %s", e)
        except requests.RequestException as e:
            logging.warning(
                "RequestException when calling '/browse/new-releases' Spotify endpoint: %s",
                e,
            )

        retries += 1
        if retries < MAX_RETRIES:
            time.sleep(2**retries)  # 2, 4, 8, 16, ...

    if entire_albums:
        logging.error(
            "Partially succeeded to get new released albums from Spotify after max retries. Failed at url: %s",
            url,
        )
        return entire_albums

    raise ValueError(
        "Failed to get any new released albums from Spotify after max retries"
    )


def get_top_tracks_from_chart(
    api_key: str,
) -> dict[str, dict]:
    """Get top tracks from Last.fm chart.gettoptracks endpoint with retries.

    Args:
        api_key (str): Last.fm API key.

    Returns:
        A dictionary containing the top tracks data from Last.fm API.
        For example: {
            "tracks": {
                "track": [
                    {track data 0},
                    {track data 1},
                    ...
                ],
                "@attr": {
                    "page": "1",
                    "perPage": "1000",
                    "totalPages": "10",
                    "total": "10000"
                }
            }
        }
    Raises:
        ValueError: If failed to get top tracks from chart after max retries.
    """

    retries = 0

    while retries < MAX_RETRIES:
        if 0 < retries:
            time.sleep(2**retries)  # 2, 4, 8, 16, ...

        try:
            response = requests.get(
                f"https://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key={api_key}&format=json&limit=1000"  # Max limit is 1000
            )

            if response.status_code == 200:
                return response.json()  # Early return

            logging.warning(
                "Response not OK when calling 'chart.gettoptracks' endpoint. Status code: %s",
                response.status_code,
            )
        except requests.RequestException:
            logging.warning(
                "RequestException when calling 'chart.gettoptracks' endpoint"
            )

        retries += 1

    raise ValueError("Failed to get top tracks from chart after max retries")


def insert_data_from_top_tracks(top_tracks: list[dict[str, str | dict | list]]) -> None:
    """Insert data from top tracks into main (PostgreSQL) database.

    Args:
        top_tracks (list[dict]): List of track data from chart.getTopTracks API.

    Raises:
        psycopg.DatabaseError: If failed to insert data after max retries.
    """

    retries = 0

    while retries < MAX_RETRIES:
        if 0 < retries:
            time.sleep(2**retries)  # 2, 4, 8, 16, ...

        try:
            with psycopg.connect(
                f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST}"
            ) as conn:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO artists (name, lastfm_url)
                        SELECT %s, %s
                        WHERE NOT EXISTS (
                            SELECT * FROM artists WHERE lastfm_url = %s
                        )
                        """,
                        [
                            (
                                track["artist"]["name"],
                                track["artist"]["url"],
                                track["artist"]["url"],  # for 'WHERE NOT EXISTS' clause
                            )
                            for track in top_tracks
                        ],
                    )
                    cur.executemany(
                        """
                        INSERT INTO tracks (name, artist_id, lastfm_url)
                        SELECT %s, (SELECT id FROM artists WHERE lastfm_url = %s), %s
                        WHERE NOT EXISTS (
                            SELECT * FROM tracks WHERE lastfm_url = %s
                        )
                        """,
                        [
                            (
                                track["name"],
                                track["artist"]["url"],  # to identify artist_id FK
                                track["url"],
                                track["url"],  # for 'WHERE NOT EXISTS' clause
                            )
                            for track in top_tracks
                        ],
                    )
                    cur.executemany(
                        """
                        INSERT INTO chart_histories (track_id, playcount, listener, chart_date, rank)
                        VALUES ((SELECT id FROM tracks WHERE lastfm_url = %s), %s, %s, %s, %s)
                        """,
                        [
                            (
                                track["url"],  # to identify track_id FK
                                track["playcount"],
                                track["listeners"],
                                datetime.now().isoformat(timespec="minutes"),
                                index + 1,  # rank starts from 1
                            )
                            for index, track in enumerate(top_tracks)
                        ],
                    )
        except psycopg.OperationalError as e:
            logging.warning(
                "Database operational error when inserting data from top tracks: %s", e
            )
        else:
            return

        retries += 1

    raise psycopg.DatabaseError(
        "Failed to insert data from top tracks into database after max retries"
    )
