# API Docs

- `GET {DATA_API_URL}/data/items?page=1&page_size=3`
- `POST {DATA_API_URL}/data/results`

The response from `/data/items` is:

```json
{
  "items": [],
  "page": 1,
  "page_size": 3,
  "total": 8,
  "has_more": true
}
```

