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

    def _save(self, name, content):
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read()
        self._client.storage.from_(self._bucket).upload(path=name, file=data, file_options={"contentType": getattr(content, 'content_type', 'application/octet-stream'), "upsert": True})
        return name

    def exists(self, name):
        try:
            files = self._client.storage.from_(self._bucket).list(path=os.path.dirname(name) or '')
            return any(f.get('name') == os.path.basename(name) for f in files)
        except Exception:
            return False

    def url(self, name):
        return self._client.storage.from_(self._bucket).get_public_url(name)