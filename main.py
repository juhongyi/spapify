import os
import base64
import argparse
import logging

from apis import get_access_token, send_discord_alert


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
        send_discord_alert(
            message="Failed to refresh access_token from Spotify. This job will retry in the next scheduled run (approx. 20 mins).",
            discord_webhook_id=discord_webhook_id,
            discord_webhook_token=discord_webhook_token,
        )


# def poc_get_new_releases_etag():
#     # entire_albums = []
#     etags = []
#     url = "https://api.spotify.com/v1/browse/new-releases?limit=50"  # max limit is 50

#     while True:
#         response = requests.get(
#             url,
#             headers={"Authorization": f"Bearer {poc_get_access_token()}"},
#         )
#         albums = response.json().get("albums")
#         # entire_albums.append(albums)

#         etags.append(response.headers.get("ETag"))

#         next_url = albums.get("next")
#         if next_url is None:
#             break
#         url = next_url

#     webhook_id = os.getenv("DSCRD_WEBHOOK_ID")
#     webhook_token = os.getenv("DSCRD_WEBHOOK_TOKEN")
#     webhook_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}"

#     for etag in etags:
#         response = requests.post(
#             webhook_url,
#             json={"content": etag.strip('"')},
#         )


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
    elif args.job == "get_new_releases":
        ...  # get_new_releases()


if __name__ == "__main__":
    main()
