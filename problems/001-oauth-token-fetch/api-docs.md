# API Docs

## OAuth Mock

- `POST {OAUTH_SERVER_URL}/oauth/token`
- Body: `grant_type=client_credentials`, `client_id`, `client_secret`
- Response: `{"access_token": "...", "token_type": "Bearer"}`

## Data API

- `GET {DATA_API_URL}/data/items`
- `POST {DATA_API_URL}/data/results`

Environment variables:

- `OAUTH_SERVER_URL`
- `DATA_API_URL`
- `CLIENT_ID`
- `CLIENT_SECRET`

