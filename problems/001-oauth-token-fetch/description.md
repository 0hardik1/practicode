# OAuth Token Fetch & Data Retrieval

An OAuth server and a data API are running for this challenge.

Your script must:

1. Request an access token from `OAUTH_SERVER_URL`.
2. Fetch the dataset from `DATA_API_URL`.
3. Keep only active items.
4. If `TEST_INPUT` contains a `category`, keep only items from that category.
5. Convert the remaining item names to uppercase, sort them alphabetically, and sum their `value`.
6. `POST` the result payload to `DATA_API_URL/data/results`.
7. Print the same payload as JSON.

The expected payload shape is:

```json
{
  "status": "success",
  "filtered_count": 0,
  "total_value": 0,
  "item_names": []
}
```

