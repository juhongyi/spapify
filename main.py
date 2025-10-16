import os
import base64
import argparse

import requests


def poc_get_access_token() -> str:
    client_id = os.getenv("SPTFY_CLIENT_ID")
    client_secret = os.getenv("SPTFY_CLIENT_SECRET")
    client_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {client_string}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    return response.json().get("access_token")


def poc_get_new_releases_etag():
    # entire_albums = []
    etags = []
    url = "https://api.spotify.com/v1/browse/new-releases?limit=50"  # max limit is 50

    while True:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {poc_get_access_token()}"},
        )
        albums = response.json().get("albums")
        # entire_albums.append(albums)

        etags.append(response.headers.get("ETag"))

        next_url = albums.get("next")
        if next_url is None:
            break
        url = next_url

    webhook_id = os.getenv("DSCRD_WEBHOOK_ID")
    webhook_token = os.getenv("DSCRD_WEBHOOK_TOKEN")
    webhook_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}"

    for etag in etags:
        response = requests.post(
            webhook_url,
            json={"content": etag.strip('"')},
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

    if args.job == "refresh_access_token":
        ...  # refresh_access_token()
    elif args.job == "get_new_releases":
        ...  # get_new_releases()


if __name__ == "__main__":
    main()
