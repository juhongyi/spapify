# Spapify: Insight from music data

## Jobs

### Chart

- `get_top_tracks` Get top tracks from Last.fm chart

## Deployment

```bash
# Example to run a specific job
bash run.sh --job=JOB_NAME
```

```bash
# Example to run Docker services
docker compose --env-file .env up -d
```

## Tech stack

- Python 3.13
- uv
- dotenvx
- cron
- PostgreSQL
- Docker Compose
