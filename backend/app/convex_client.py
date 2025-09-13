import os
from typing import Any, Dict, Optional, List
import httpx

class ConvexClient:
    """Lightweight HTTP client for Convex Functions API.

    Docs: https://docs.convex.dev/http-api/
    - POST {CONVEX_URL}/api/query with JSON { path, args, format: 'json' }
    - POST {CONVEX_URL}/api/mutation with JSON { path, args, format: 'json' }
    - POST {CONVEX_URL}/api/run/{functionIdentifier} with JSON { args, format: 'json' }
    """

    def __init__(self, base_url: Optional[str] = None, deploy_key: Optional[str] = None, user_bearer: Optional[str] = None):
        bu = (base_url or os.getenv('CONVEX_URL') or '').rstrip('/')
        # Normalize accidental '/api' suffix in provided URL
        if bu.endswith('/api'):
            bu = bu[:-4]
        self.base_url = bu
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

    def _base_candidates(self) -> List[str]:
        """Return candidate base URLs to try, accounting for convex.site vs convex.cloud.

        Many Convex deployments are under *.convex.cloud. Some dashboards show *.convex.site,
        which may not serve the HTTP Functions API at /api/query. We try sensible fallbacks.
        """
        bases = []
        if not self.base_url:
            return bases
        bases.append(self.base_url.rstrip('/'))
        # If user configured *.convex.site, also try *.convex.cloud
        if self.base_url.endswith('.convex.site'):
            bases.append(self.base_url[:-12] + '.convex.cloud')  # replace suffix
        return list(dict.fromkeys(bases))  # dedupe

    async def _post_with_fallbacks(self, paths: List[str], payload: Dict[str, Any], *, admin: bool = False) -> Any:
        """Try multiple (base_url, path) combinations until one works.

        Paths are relative like '/api/query'.
        """
        last_exc: Optional[Exception] = None
        headers = self._headers(admin)
        for base in self._base_candidates():
            for path in paths:
                url = f"{base}{path}"
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                        res = await client.post(url, headers=headers, json=payload)
                        res.raise_for_status()
                        body = res.json()
                        # Convex may return 200 with { status: 'error', error: {...} }
                        if isinstance(body, dict) and body.get('status') == 'error':
                            # Normalize error raising so callers go to fallback
                            err = body.get('error')
                            raise RuntimeError(f"Convex error: {err}")
                        return body
                except Exception as e:
                    last_exc = e
                    continue
        if last_exc:
            raise last_exc
        raise RuntimeError('Convex base URL not configured')

    async def query(self, path: str, args: Dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        payload = {'path': path, 'args': args or {}, 'format': 'json'}
        return await self._post_with_fallbacks(['/api/query'], payload, admin=False)

    async def mutation(self, path: str, args: Dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        payload = {'path': path, 'args': args or {}, 'format': 'json'}
        return await self._post_with_fallbacks(['/api/mutation'], payload, admin=False)

    async def run(self, function_identifier: str, args: Dict[str, Any] | None = None, *, admin: bool = False) -> Any:
        if not self.enabled:
            raise RuntimeError('Convex base URL not configured')
        # Convert 'namespace:function' to 'namespace/function' as required by Convex HTTP API
        fid = (function_identifier or '').replace(':', '/')
        # Only use the documented /api/run endpoint
        paths = [f"/api/run/{fid}"]
        payload = {'args': args or {}, 'format': 'json'}
        return await self._post_with_fallbacks(paths, payload, admin=admin)
