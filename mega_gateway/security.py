"""State and security primitives for the Mega MCP gateway.

The module deliberately stores digests of bearer credentials and authorisation
codes.  Plaintext values exist only while a response is being constructed.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


PAIR_TTL_SECONDS = 10 * 60
AUTH_CODE_TTL_SECONDS = 60
ACCESS_TTL_SECONDS = 15 * 60
REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60
PROVISIONAL_CLIENT_TTL_SECONDS = 10 * 60
APPROVED_CLIENT_TTL_SECONDS = 31 * 24 * 60 * 60
MAX_PENDING_DYNAMIC_CLIENTS = 32
MAX_PENDING_PAIRINGS = 64
RESERVATION_WINDOW_SECONDS = 10 * 60
DCR_RESERVATION_LIMIT = 16
PAIRING_RESERVATION_LIMIT = 32
DEFAULT_TOOL_NAMES = frozenset(
    {
        "get_context",
        "search_memories",
        "list_memories",
        "memory_stats",
        "skills_list",
        "registry_search",
        "registry_get_server",
    }
)
VALID_PROFILES = frozenset({"chatgpt", "gemini-spark"})


class OAuthError(ValueError):
    """An OAuth request failed validation."""


class ReservationLimiter:
    """Bound short-lived, global reservations without trusting client identity.

    This is intentionally in-process: it prevents one process from filling the
    durable pending tables during a ten-minute window, while SQLite limits
    remain the restart-safe backstop.  A clock can be injected for tests.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float = RESERVATION_WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.reservations: deque[float] = deque()

    def reserve(self) -> bool:
        now = self.clock()
        while self.reservations and now - self.reservations[0] >= self.window_seconds:
            self.reservations.popleft()
        if len(self.reservations) >= self.limit:
            return False
        self.reservations.append(now)
        return True


def _now() -> int:
    return int(time.time())


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _token(prefix: str) -> str:
    return prefix + secrets.token_urlsafe(32)


def pkce_s256(verifier: str) -> str:
    """Return the RFC 7636 S256 challenge for a code verifier."""
    encoded = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")


def _valid_verifier(value: str) -> bool:
    return 43 <= len(value) <= 128 and all(c.isalnum() or c in "-._~" for c in value)


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int = ACCESS_TTL_SECONDS

    def response(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "token_type": "Bearer",
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
        }


class GatewayStore:
    """Small synchronous SQLite store protected by the aiohttp event loop.

    This is intentionally stdlib-only for the Alpine runtime.  Every durable
    credential column contains a SHA-256 digest, never a bearer value.
    """

    def __init__(self, database: Path):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS pairings (
              id TEXT PRIMARY KEY,
              client_id TEXT NOT NULL,
              redirect_uri TEXT NOT NULL,
              profile TEXT NOT NULL,
              code_challenge TEXT NOT NULL,
              state TEXT,
              status TEXT NOT NULL,
              created_at INTEGER NOT NULL,
              expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_codes (
              code_hash TEXT PRIMARY KEY,
              pairing_id TEXT NOT NULL REFERENCES pairings(id),
              client_id TEXT NOT NULL,
              redirect_uri TEXT NOT NULL,
              code_challenge TEXT NOT NULL,
              expires_at INTEGER NOT NULL,
              consumed_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS tokens (
              token_hash TEXT PRIMARY KEY,
              kind TEXT NOT NULL CHECK(kind IN ('access', 'refresh')),
              client_id TEXT NOT NULL,
              profile TEXT NOT NULL,
              expires_at INTEGER NOT NULL,
              revoked_at INTEGER,
              replaced_by_hash TEXT,
              family_id TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS tokens_lookup ON tokens(token_hash, kind, expires_at);
            CREATE TABLE IF NOT EXISTS profile_tools (
              profile TEXT NOT NULL,
              tool_name TEXT NOT NULL,
              enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
              PRIMARY KEY(profile, tool_name)
            );
            CREATE TABLE IF NOT EXISTS oauth_clients (
              client_id TEXT NOT NULL,
              profile TEXT NOT NULL,
              redirect_uri TEXT NOT NULL,
              created_at INTEGER NOT NULL,
              expires_at INTEGER NOT NULL,
              paired_at INTEGER,
              PRIMARY KEY(client_id, redirect_uri)
            );
            """
        )
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(tokens)")}
        if "family_id" not in columns:
            # Existing pre-family credentials cannot be safely correlated, so
            # migration revokes them rather than retaining partial grants.
            self.connection.execute("ALTER TABLE tokens ADD COLUMN family_id TEXT")
        # This repair is deliberately unconditional.  ALTER TABLE can have
        # committed before a process crash, leaving a nullable family_id.
        self.connection.execute(
            "UPDATE tokens SET revoked_at = COALESCE(revoked_at, ?), family_id = token_hash "
            "WHERE family_id IS NULL",
            (_now(),),
        )
        self.connection.execute("CREATE INDEX IF NOT EXISTS tokens_family ON tokens(family_id, revoked_at)")
        client_columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(oauth_clients)")}
        if "expires_at" not in client_columns:
            self.connection.execute("ALTER TABLE oauth_clients ADD COLUMN expires_at INTEGER")
            self.connection.execute(
                "UPDATE oauth_clients SET expires_at = ? WHERE expires_at IS NULL", (_now(),)
            )
        if "paired_at" not in client_columns:
            self.connection.execute("ALTER TABLE oauth_clients ADD COLUMN paired_at INTEGER")
            # Legacy dynamic registrations have no proof of local approval.
            self.connection.execute("UPDATE oauth_clients SET expires_at = ? WHERE paired_at IS NULL", (_now(),))
        self.connection.executemany(
            "INSERT OR IGNORE INTO profile_tools(profile, tool_name, enabled) VALUES (?, ?, 1)",
            [(profile, tool) for profile in VALID_PROFILES for tool in DEFAULT_TOOL_NAMES],
        )
        self.cleanup_expired()
        self.connection.commit()

    def create_pairing(
        self, *, client_id: str, redirect_uri: str, profile: str, code_challenge: str, state: str | None
    ) -> dict[str, Any]:
        now = _now()
        self.cleanup_expired(now)
        pending = self.connection.execute(
            "SELECT COUNT(*) FROM pairings WHERE status = 'pending' AND expires_at > ?", (now,)
        ).fetchone()[0]
        if pending >= MAX_PENDING_PAIRINGS:
            self.connection.commit()
            raise OAuthError("too many pending pairing requests")
        pairing_id = _token("pair_")
        expires_at = now + PAIR_TTL_SECONDS
        self.connection.execute(
            "INSERT INTO pairings VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
            (pairing_id, client_id, redirect_uri, profile, code_challenge, state, now, expires_at),
        )
        self.connection.commit()
        return {"pairing_id": pairing_id, "profile": profile, "status": "pending", "expires_at": expires_at}

    def pending_pairing_for(
        self, *, client_id: str, redirect_uri: str, profile: str, code_challenge: str, state: str | None
    ) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT id, profile, status, expires_at FROM pairings WHERE client_id = ? AND redirect_uri = ? "
            "AND profile = ? AND code_challenge = ? AND state IS ? AND status = 'pending' "
            "AND expires_at > ? ORDER BY created_at DESC LIMIT 1",
            (client_id, redirect_uri, profile, code_challenge, state, _now()),
        ).fetchone()
        if not row:
            return None
        return {
            "pairing_id": row["id"],
            "profile": row["profile"],
            "status": row["status"],
            "expires_at": row["expires_at"],
        }

    def cleanup_expired(self, now: int | None = None) -> None:
        now = now if now is not None else _now()
        self.connection.execute(
            "DELETE FROM auth_codes WHERE expires_at <= ? OR pairing_id IN "
            "(SELECT id FROM pairings WHERE expires_at <= ?)",
            (now, now),
        )
        self.connection.execute("DELETE FROM pairings WHERE expires_at <= ?", (now,))
        self.connection.execute("DELETE FROM oauth_clients WHERE expires_at <= ?", (now,))

    def pairing(self, pairing_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM pairings WHERE id = ?", (pairing_id,)).fetchone()
        if row and row["status"] == "pending" and row["expires_at"] <= _now():
            self.connection.execute("UPDATE pairings SET status = 'expired' WHERE id = ?", (pairing_id,))
            self.connection.commit()
            row = self.connection.execute("SELECT * FROM pairings WHERE id = ?", (pairing_id,)).fetchone()
        return dict(row) if row else None

    def pending_pairings(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT id, client_id, profile, status, created_at, expires_at FROM pairings "
            "WHERE status = 'pending' AND expires_at > ? ORDER BY created_at", (_now(),)
        ).fetchall()
        return [dict(row) for row in rows]

    def decide_pairing(self, pairing_id: str, approved: bool) -> dict[str, Any] | None:
        pairing = self.pairing(pairing_id)
        if not pairing:
            return None
        if pairing["expires_at"] <= _now() and pairing["status"] == "pending":
            self.connection.execute("UPDATE pairings SET status = 'expired' WHERE id = ?", (pairing_id,))
            self.connection.commit()
            return self.pairing(pairing_id)
        if pairing["status"] != "pending":
            return pairing
        status = "approved" if approved else "denied"
        self.connection.execute("UPDATE pairings SET status = ? WHERE id = ?", (status, pairing_id))
        if approved:
            approved_at = _now()
            self.connection.execute(
                "UPDATE oauth_clients SET paired_at = ?, expires_at = ? "
                "WHERE client_id = ? AND paired_at IS NULL",
                (approved_at, approved_at + APPROVED_CLIENT_TTL_SECONDS, pairing["client_id"]),
            )
        self.connection.commit()
        return self.pairing(pairing_id)

    def issue_code(self, pairing_id: str) -> str:
        pairing = self.pairing(pairing_id)
        if not pairing or pairing["status"] != "approved" or pairing["expires_at"] <= _now():
            raise OAuthError("pairing is not approved")
        code = _token("code_")
        self.connection.execute(
            "INSERT INTO auth_codes VALUES (?, ?, ?, ?, ?, ?, NULL)",
            (
                _digest(code), pairing_id, pairing["client_id"], pairing["redirect_uri"],
                pairing["code_challenge"], _now() + AUTH_CODE_TTL_SECONDS,
            ),
        )
        self.connection.execute("UPDATE pairings SET status = 'code_issued' WHERE id = ?", (pairing_id,))
        self.connection.commit()
        return code

    def redeem_code(self, *, code: str, client_id: str, redirect_uri: str, verifier: str) -> TokenPair:
        if not _valid_verifier(verifier):
            raise OAuthError("invalid code_verifier")
        code_hash = _digest(code)
        row = self.connection.execute("SELECT * FROM auth_codes WHERE code_hash = ?", (code_hash,)).fetchone()
        if not row or row["consumed_at"] is not None or row["expires_at"] <= _now():
            raise OAuthError("invalid or expired authorisation code")
        if row["client_id"] != client_id or row["redirect_uri"] != redirect_uri:
            raise OAuthError("authorisation code client binding failed")
        if not hmac.compare_digest(row["code_challenge"], pkce_s256(verifier)):
            raise OAuthError("PKCE verification failed")
        consumed_at = _now()
        changed = self.connection.execute(
            "UPDATE auth_codes SET consumed_at = ? WHERE code_hash = ? AND consumed_at IS NULL",
            (consumed_at, code_hash),
        ).rowcount
        if changed != 1:
            self.connection.rollback()
            raise OAuthError("authorisation code already used")
        profile = self.connection.execute(
            "SELECT profile FROM pairings WHERE id = ?", (row["pairing_id"],)
        ).fetchone()["profile"]
        tokens = self._issue_tokens(client_id, profile)
        self.connection.commit()
        return tokens

    def _issue_tokens(self, client_id: str, profile: str, family_id: str | None = None) -> TokenPair:
        access, refresh = _token("mg_at_"), _token("mg_rt_")
        family_id = family_id or _token("grant_")
        now = _now()
        self.connection.executemany(
            "INSERT INTO tokens VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)",
            [
                (_digest(access), "access", client_id, profile, now + ACCESS_TTL_SECONDS, family_id),
                (_digest(refresh), "refresh", client_id, profile, now + REFRESH_TTL_SECONDS, family_id),
            ],
        )
        return TokenPair(access, refresh)

    def rotate_refresh(self, refresh_token: str, client_id: str) -> TokenPair:
        token_hash = _digest(refresh_token)
        row = self.connection.execute(
            "SELECT * FROM tokens WHERE token_hash = ? AND kind = 'refresh'", (token_hash,)
        ).fetchone()
        if not row or row["client_id"] != client_id:
            raise OAuthError("invalid or expired refresh token")
        if not row["family_id"]:
            self.connection.execute(
                "UPDATE tokens SET revoked_at = COALESCE(revoked_at, ?) WHERE token_hash = ?",
                (_now(), token_hash),
            )
            self.connection.commit()
            raise OAuthError("invalid or expired refresh token")
        if row["revoked_at"] is not None or row["expires_at"] <= _now():
            # A revoked refresh token was replayed.  Treat the whole grant as
            # compromised, including any access/refresh descendants.
            self.revoke_family(row["family_id"])
            raise OAuthError("invalid or expired refresh token")
        tokens = self._issue_tokens(row["client_id"], row["profile"], row["family_id"])
        new_hash = _digest(tokens.refresh_token)
        self.connection.execute(
            "UPDATE tokens SET revoked_at = ?, replaced_by_hash = ? WHERE token_hash = ? AND revoked_at IS NULL",
            (_now(), new_hash, token_hash),
        )
        self.connection.commit()
        return tokens

    def validate_access(self, token: str) -> dict[str, str] | None:
        row = self.connection.execute(
            "SELECT client_id, profile FROM tokens WHERE token_hash = ? AND kind = 'access' "
            "AND family_id IS NOT NULL AND revoked_at IS NULL AND expires_at > ?",
            (_digest(token), _now()),
        ).fetchone()
        return dict(row) if row else None

    def revoke(self, token: str) -> None:
        self.revoke_hash(_digest(token))

    def revoke_hash(self, token_hash: str) -> None:
        row = self.connection.execute("SELECT family_id FROM tokens WHERE token_hash = ?", (token_hash,)).fetchone()
        if row:
            if row["family_id"]:
                self.revoke_family(row["family_id"])
            else:
                self.connection.execute(
                    "UPDATE tokens SET revoked_at = COALESCE(revoked_at, ?) WHERE token_hash = ?",
                    (_now(), token_hash),
                )
                self.connection.commit()

    def revoke_family(self, family_id: str) -> None:
        self.connection.execute(
            "UPDATE tokens SET revoked_at = COALESCE(revoked_at, ?) WHERE family_id = ?",
            (_now(), family_id),
        )
        self.connection.commit()

    def active_connections(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT family_id, client_id, profile, MAX(expires_at) AS expires_at FROM tokens "
            "WHERE revoked_at IS NULL AND expires_at > ? "
            "GROUP BY family_id, client_id, profile ORDER BY expires_at DESC", (_now(),)
        ).fetchall()
        return [
            {
                "connection_id": row["family_id"],
                "client_id": row["client_id"],
                "profile": row["profile"],
                "expires_at": row["expires_at"],
            }
            for row in rows
        ]

    def revoke_connection(self, connection_id: str) -> None:
        self.revoke_family(connection_id)

    def tools_for_profile(self, profile: str) -> frozenset[str]:
        if profile not in VALID_PROFILES:
            return frozenset()
        rows = self.connection.execute(
            "SELECT tool_name FROM profile_tools WHERE profile = ? AND enabled = 1", (profile,)
        ).fetchall()
        return frozenset(row["tool_name"] for row in rows)

    def set_profile_tool(self, profile: str, tool_name: str, enabled: bool) -> None:
        if profile not in VALID_PROFILES:
            raise OAuthError("unknown profile")
        if tool_name not in DEFAULT_TOOL_NAMES:
            raise OAuthError("tool is not part of the gateway allowlist")
        self.connection.execute(
            "INSERT INTO profile_tools(profile, tool_name, enabled) VALUES (?, ?, ?) "
            "ON CONFLICT(profile, tool_name) DO UPDATE SET enabled = excluded.enabled",
            (profile, tool_name, int(enabled)),
        )
        self.connection.commit()

    def registered_chatgpt_client(self, redirect_uris: list[str]) -> tuple[str, int] | None:
        """Return the live public client for an exact redirect URI set, if any."""
        now = _now()
        placeholders = ", ".join("?" for _ in redirect_uris)
        existing = self.connection.execute(
            "SELECT client_id, MIN(created_at) AS created_at FROM oauth_clients "
            "WHERE profile = 'chatgpt' AND expires_at > ? GROUP BY client_id "
            f"HAVING COUNT(*) = ? AND SUM(CASE WHEN redirect_uri IN ({placeholders}) THEN 1 ELSE 0 END) = ?",
            (now, len(redirect_uris), *redirect_uris, len(redirect_uris)),
        ).fetchone()
        if existing:
            return str(existing["client_id"]), int(existing["created_at"])
        return None

    def register_chatgpt_client(self, redirect_uris: list[str]) -> tuple[str, int]:
        """Persist one public ChatGPT client with exact redirect URI matching."""
        now = _now()
        self.cleanup_expired(now)
        existing = self.registered_chatgpt_client(redirect_uris)
        if existing:
            self.connection.commit()
            return existing
        active_count = self.connection.execute(
            "SELECT COUNT(DISTINCT client_id) FROM oauth_clients "
            "WHERE profile = 'chatgpt' AND paired_at IS NULL AND expires_at > ?",
            (now,),
        ).fetchone()[0]
        if active_count >= MAX_PENDING_DYNAMIC_CLIENTS:
            self.connection.commit()
            raise OAuthError("dynamic client registration limit reached")
        client_id = _token("chatgpt_")
        issued_at = now
        expires_at = now + PROVISIONAL_CLIENT_TTL_SECONDS
        self.connection.executemany(
            "INSERT INTO oauth_clients(client_id, profile, redirect_uri, created_at, expires_at, paired_at) "
            "VALUES (?, 'chatgpt', ?, ?, ?, NULL)",
            [(client_id, redirect_uri, issued_at, expires_at) for redirect_uri in redirect_uris],
        )
        self.connection.commit()
        return client_id, issued_at

    def registered_profile_for(self, client_id: str, redirect_uri: str) -> str | None:
        row = self.connection.execute(
            "SELECT profile FROM oauth_clients WHERE client_id = ? AND redirect_uri = ? AND expires_at > ?",
            (client_id, redirect_uri, _now()),
        ).fetchone()
        return str(row["profile"]) if row else None
