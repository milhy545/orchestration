# Mega security gateway operator guide

The gateway admin surface is a Unix socket. The wrappers in `scripts/mega_security`
and `scripts/mega_funnel` send one JSON request and read one JSON response per
connection. The socket path is `MEGA_GATEWAY_ADMIN_SOCKET`, defaulting to
`/run/mega-gateway/admin.sock`; `--socket` overrides it for maintenance and tests.

Use `scripts/mega_security status` first. Other actions are:

```text
pairing pending
pairing approve <pairing-id>
pairing reject <pairing-id>
profile list [profile-id]
profile grant <profile-id> <tool>
profile revoke <profile-id> <tool>
connections list
connections revoke <connection-id>
audit
backup-check
funnel-off
```

The `audit` display is currently a placeholder: the gateway does not yet persist
audit events, tokens, or command arguments. Authentication and policy checks
still apply. IDs are supplied by the gateway; do not guess or reuse an ID from
another environment.

`scripts/mega_funnel` is deliberately narrower:

```text
scripts/mega_funnel status   # default, read-only
scripts/mega_funnel off      # emergency disable
```

It manages only the gateway-owned Funnel configuration. It has no `on` action,
does not expose port 7000, and never invokes Docker Compose. Funnel is not
enabled or deployed by these scripts.

The current transport contract is `{"action": "...", "payload": {...}}` as a
newline terminated JSON object. A successful response may be either a JSON
object or `{"ok": true, "data": ...}`. Rejection uses `{"ok": false,
"error": "..."}`. The gateway implementation is the authority for the exact
action policy and response fields.
