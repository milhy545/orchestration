from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class VaultClient:
    def __init__(
        self,
        base_url: str,
        token_file: Path,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_file = token_file
        self.timeout = timeout

    def headers(self) -> dict[str, str]:
        token = self.token_file.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("Vault token file is empty")
        return {"X-Vault-Token": token}

    async def read_secret(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.get(
                f"{self.base_url}/v1/secret/data/{path}",
                headers=self.headers(),
            )
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json().get("data", {}).get("data", {})

    async def write_secret(self, path: str, data: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.post(
                f"{self.base_url}/v1/secret/data/{path}",
                headers=self.headers(),
                json={"data": data},
            )
        response.raise_for_status()

    async def probe(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                response = await client.get(
                    f"{self.base_url}/v1/sys/health",
                    headers=self.headers(),
                )
            return response.status_code < 500
        except (OSError, ValueError, httpx.HTTPError):
            return False
