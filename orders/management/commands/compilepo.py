from django.core.management.base import BaseCommand
from pathlib import Path
import os
import polib


class Command(BaseCommand):
    help = "Compile .po files to .mo using polib (no GNU gettext required)"

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        locale_dir = base_dir / 'locale'
        if not locale_dir.exists():
            self.stdout.write(self.style.WARNING(f"[skip] {locale_dir} not found"))
            return

        langs = []
        for lang_dir in locale_dir.iterdir():
            if lang_dir.is_dir():
                langs.append(lang_dir.name)

        for lang in langs:
            po_path = locale_dir / lang / 'LC_MESSAGES' / 'django.po'
            mo_path = locale_dir / lang / 'LC_MESSAGES' / 'django.mo'
            if not po_path.exists():
                self.stdout.write(self.style.WARNING(f"[skip] {po_path} not found"))
                continue
            try:
                po = polib.pofile(str(po_path))
                os.makedirs(mo_path.parent, exist_ok=True)
                po.save_as_mofile(str(mo_path))
                self.stdout.write(self.style.SUCCESS(f"[ok] Compiled {po_path} -> {mo_path}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[err] {po_path}: {e}"))