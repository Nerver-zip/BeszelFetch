# Security

## Threat Model

The direct client-to-hub architecture eliminates intermediate proxies, but places authentication credentials on the Android device running KWGT.

Primary security risks:
1. Exporting or sharing presets containing live credentials;
2. Unencrypted cleartext HTTP traffic across untrusted networks;
3. Using an administrative account with write/delete capabilities;
4. Leaking tokens into UI debug text strings or crash reports;
5. Device compromise / physical access;
6. Exposing Beszel Hub to the public internet without proper access control.

## Recommended Security Practices

### Dedicated Non-Admin User

Create an account strictly dedicated to the widget:
- Role: Read-only;
- Restricted scope: Access limited only to monitored systems;
- Unique, high-entropy password;
- No password reuse.

### Transport Security

Mandatory transport standards:
- HTTPS with valid TLS certificates;
- Tailscale / WireGuard or private VPN tunnel;
- Existing trusted reverse proxy (e.g., Caddy, Traefik, Nginx).

Never send credentials over unencrypted HTTP.

### Global Variables

Utilize Kustom Secret Globals for:
- `bz_email`
- `bz_pass`
- `bz_token`

`bz_url` can remain a standard text global unless the internal domain itself is considered sensitive.

### Logging & Diagnostics

Permitted debug outputs:
```text
HTTP 401
system=<sanitized-id>
cache_age=7m
view=overview
```

Strictly prohibited in debug strings or UI elements:
```text
password=...
Authorization=...
token=...
```

### Preset Sanitization

Before publishing or sharing a `.kwgt` file:
- Flush all credential globals;
- Clear JWT tokens;
- Scrub internal IP addresses and hostnames;
- Flush cached JSON payloads;
- Review any exported screenshots for confidential information.

## Credential Storage Trade-offs

### Option A: Email + Password + Token (Recommended Default)
The widget stores credentials and requests new JWT tokens upon expiry.
- Advantage: Fully autonomous background operation without user intervention.
- Risk: Password persists on the mobile device (mitigated via read-only dedicated user).

### Option B: Token Only
The user manually pastes a pre-generated PocketBase auth token into KWGT.
- Advantage: Password never touches the mobile device.
- Disadvantage: Requires manual renewal whenever the token expires or is revoked.

## Out of Scope / Anti-Patterns

This blueprint explicitly advises against:
- Bypassing PocketBase authentication rules;
- Publicly exposing unauthenticated metrics endpoints;
- Storing admin/root credentials on mobile;
- Disabling SSL/TLS certificate validation;
- Opening firewall ports directly to the public internet solely for widget access.
