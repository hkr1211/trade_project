import os
from django.core.files.storage import Storage
from supabase import create_client

class SupabaseStorage(Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = os.environ.get('SUPABASE_URL')
        self._key = os.environ.get('SUPABASE_SERVICE_KEY')
        self._bucket = os.environ.get('SUPABASE_BUCKET', 'media')
        self._client = create_client(self._url, self._key)

    def _normalize_path(self, name: str) -> str:
        name = name.lstrip('/')
        return name

    def _save(self, name, content):
        name = self._normalize_path(name)
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()
        resp = self._client.storage.from_(self._bucket).upload(
            path=name,
            file=data,
            file_options={
                "contentType": getattr(content, 'content_type', 'application/octet-stream'),
                "upsert": True,
            },
        )
        return name

    def exists(self, name):
        try:
            name = self._normalize_path(name)
            files = self._client.storage.from_(self._bucket).list(path=os.path.dirname(name) or '')
            return any(f.get('name') == os.path.basename(name) for f in files)
        except Exception:
            return False

    def url(self, name):
        name = self._normalize_path(name)
        ret = self._client.storage.from_(self._bucket).get_public_url(name)

        # Try to extract URL from various response formats
        url = None
        try:
            if isinstance(ret, str):
                url = ret
            elif hasattr(ret, 'get'):
                # Handle dict-like response: {"data": {"publicUrl": "..."}}
                data = ret.get('data')
                if isinstance(data, dict):
                    url = data.get('publicUrl') or data.get('public_url')
        except Exception:
            pass

        # If we got a URL from API, validate it's absolute
        if url:
            # If it's a relative path, convert to absolute
            if url.startswith('/'):
                if self._url:
                    # Remove trailing slash from _url and leading slash from path
                    base = self._url.rstrip('/')
                    return f"{base}{url}"
            elif url.startswith('http'):
                # Already absolute URL
                return url

        # Fallback to manual URL construction
        if self._url:
            base = self._url.rstrip('/')
            return f"{base}/storage/v1/object/public/{self._bucket}/{name}"

        # Last resort: return relative path with bucket prefix
        return f"/media/{name}"