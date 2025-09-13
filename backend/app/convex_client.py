import os
from typing import Any, Dict, Optional
import httpx

class ConvexClient:
    """Lightweight HTTP client for Convex Functions API.

    Docs: https://docs.convex.dev/http-api/
    - POST {CONVEX_URL}/api/query with JSON { path, args, format: 'json' }
    - POST {CONVEX_URL}/api/mutation with JSON { path, args, format: 'json' }
    - POST {CONVEX_URL}/api/run/{functionIdentifier} with JSON { args, format: 'json' }
    """

    def __init__(self, base_url: Optional[str] = None, deploy_key: Optional[str] = None, user_bearer: Optional[str] = None):
        self.base_url = (base_url or os.getenv('CONVEX_URL') or '').rstrip('/')
        self.deploy_key = deploy_key or os.getenv('CONVEX_DEPLOY_KEY')
        self.user_bearer = user_bearer or os.getenv('CONVEX_USER_BEARER')

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def _headers(self, admin: bool = False) -> Dict[str, str]:
        headers = { 'Content-Type': 'application/json' }
        if admin and self.deploy_key:
            headers['Authorization'] = f'Convex {self.deploy_key}'
        elif self.user_bearer:
            headers['Authorization'] = f'Bearer {self.user_bearer}'
        return headers

    async def query(self, path: str, args: Dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        url = f"{self.base_url}/api/query"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(url, headers=self._headers(False), json={'path': path, 'args': args or {}, 'format': 'json'})
            res.raise_for_status()
            return res.json()

    async def mutation(self, path: str, args: Dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        url = f"{self.base_url}/api/mutation"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(url, headers=self._headers(False), json={'path': path, 'args': args or {}, 'format': 'json'})
            res.raise_for_status()
            return res.json()

    async def run(self, function_identifier: str, args: Dict[str, Any] | None = None, *, admin: bool = False) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        url = f"{self.base_url}/api/run/{function_identifier}"
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(url, headers=self._headers(admin), json={'args': args or {}, 'format': 'json'})
            res.raise_for_status()
            return res.json()
