import os
from django.core.management.base import BaseCommand
from django.conf import settings
from supabase import create_client
from orders.models import InquiryItem, OrderAttachment

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY')
        bucket = os.environ.get('SUPABASE_BUCKET', 'media')
        client = create_client(url, key)
        count = 0
        for item in InquiryItem.objects.exclude(drawing_file=''):
            path = str(item.drawing_file)
            local_path = os.path.join(settings.MEDIA_ROOT, path)
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    data = f.read()
                client.storage.from_(bucket).upload(path=path, file=data, file_options={"upsert": True})
                count += 1
        for att in OrderAttachment.objects.all():
            path = str(att.file)
            local_path = os.path.join(settings.MEDIA_ROOT, path)
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    data = f.read()
                client.storage.from_(bucket).upload(path=path, file=data, file_options={"upsert": True})
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Uploaded {count} files to Supabase bucket '{bucket}'."))