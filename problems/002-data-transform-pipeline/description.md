# Data Transform Pipeline

The data API serves paginated records.

Your script must:

1. Read `page_size` from `TEST_INPUT` if present.
2. Fetch every page from `DATA_API_URL/data/items`.
3. Deduplicate records by `email`.
4. Build a summary payload with:
   - `status`
   - `unique_records`
   - `active_records`
   - `domains` (sorted unique email domains)
   - `null_name_count`
5. `POST` the summary to `DATA_API_URL/data/results`.
6. Print the same payload as JSON.

