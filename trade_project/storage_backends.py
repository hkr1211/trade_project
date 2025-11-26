import os
from django.core.files.storage import Storage
import httpx
from urllib.parse import quote
import re
import time

class SupabaseStorage(Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = os.environ.get('SUPABASE_URL')
        self._key = os.environ.get('SUPABASE_SERVICE_KEY')
        self._bucket = os.environ.get('SUPABASE_BUCKET', 'media')
        self._base = (self._url or '').rstrip('/')

    def _normalize_path(self, name: str) -> str:
        name = name.lstrip('/')
        return name

    def _sanitize_key(self, name: str) -> str:
        name = self._normalize_path(name)
        if '/' in name:
            dir_part, base = name.rsplit('/', 1)
        else:
            dir_part, base = '', name
        root, ext = os.path.splitext(base)
        safe_root = re.sub(r'[^A-Za-z0-9._-]', '_', root).strip('_')
        if not safe_root:
            safe_root = f'file_{int(time.time())}'
        safe_base = safe_root + ext.lower()
        return f'{dir_part}/{safe_base}' if dir_part else safe_base

    def _save(self, name, content):
        name = self._sanitize_key(name)
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()
        headers = {
            'Authorization': f'Bearer {self._key}',
            'apikey': self._key,
            'Content-Type': getattr(content, 'content_type', 'application/octet-stream'),
            'x-upsert': 'true',
        }
        encoded = quote(name, safe='/')
        url = f"{self._base}/storage/v1/object/{self._bucket}/{encoded}?upsert=true"
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, content=data)
            if resp.status_code >= 400:
                raise Exception(f"upload error {resp.status_code}: {resp.text}")
        return name

    def exists(self, name):
        try:
            name = self._normalize_path(name)
            url = self.url(name)
            with httpx.Client(timeout=10) as client:
                r = client.head(url)
            return r.status_code == 200
        except Exception:
            return False

    def url(self, name):
        name = self._sanitize_key(name)
        encoded = quote(name, safe='/')
        return f"{self._base}/storage/v1/object/public/{self._bucket}/{encoded}"

    def size(self, name):
        try:
            name = self._normalize_path(name)
            url = self.url(name)
            with httpx.Client(timeout=10) as client:
                r = client.head(url)
            if r.status_code == 200:
                return int(r.headers.get('Content-Length', 0))
            return 0
        except Exception:
            return 0