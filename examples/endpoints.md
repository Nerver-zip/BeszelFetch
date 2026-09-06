# Reference Endpoints

Replace:
- `{BASE}` with `https://your-beszel-instance.com`
- `{TOKEN}` with the authentication token
- `{SYSTEM_ID}` with the target system record ID.

## Health Check

```http
GET {BASE}/api/health
```

## Authentication

```http
POST {BASE}/api/collections/users/auth-with-password
Content-Type: application/json

{
  "identity": "widget@example.invalid",
  "password": "REDACTED"
}
```

## Systems (Overview)

```http
GET {BASE}/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name
Authorization: {TOKEN}
```

## System History (Charts)

```http
GET {BASE}/api/collections/system_stats/records?page=1&perPage=500&skipTotal=1&filter=system='{SYSTEM_ID}'%20%26%26%20created%20%3E%20'2026-09-05T00%3A00%3A00Z'%20%26%26%20type='20m'&fields=created,stats&sort=created
Authorization: {TOKEN}
```

In Kustom, let the WebGet action handle URL encoding whenever possible rather than manually encoding strings.

## Container Stats

```http
GET {BASE}/api/collections/container_stats/records
Authorization: {TOKEN}
```

Configure `filter`, `fields`, and `sort` parameters after verifying the actual schema of your installed Beszel version.

## Containers Collection (Metadata)

```http
GET {BASE}/api/collections/containers/records
Authorization: {TOKEN}
```

Do not rely on this endpoint for health/image status before verifying your Beszel deployment.
