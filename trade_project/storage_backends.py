import os
from django.core.files.storage import Storage
from supabase import create_client
from whitenoise.storage import CompressedManifestStaticFilesStorage

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
        # supabase-py may return dict-like {"data": {"publicUrl": "..."}}
        try:
            if isinstance(ret, str):
                return ret
            if hasattr(ret, 'get'):
                data = ret.get('data')
                if isinstance(data, dict):
                    return data.get('publicUrl') or data.get('public_url') or f"{self._url}/storage/v1/object/public/{self._bucket}/{name}"
        except Exception:
            pass
        # Fallback to manual URL build
        return f"{self._url}/storage/v1/object/public/{self._bucket}/{name}"


class ForgivingManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    自定义静态文件存储，设置 manifest_strict = False
    这样即使某些文件不在清单中也不会报错（例如 CDN 回退文件）
    """
    manifest_strict = False