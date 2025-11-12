from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import polib
except ImportError:  # pragma: no cover
    polib = None


class Command(BaseCommand):
    help = "Compile .po files to .mo using polib (no GNU gettext needed)."

    def handle(self, *args, **options):
        if polib is None:
            self.stderr.write(
                "polib is not installed. Run 'pip install polib' and retry."
            )
            return

        languages = [code for code, _name in getattr(settings, 'LANGUAGES', [])]
        if not languages:
            languages = ['en', 'ja']

        compiled_any = False
        for locale_path in getattr(settings, 'LOCALE_PATHS', []):
            root = Path(locale_path)
            for lang in languages:
                po_path = root / lang / 'LC_MESSAGES' / 'django.po'
                if po_path.exists():
                    mo_path = po_path.with_suffix('.mo')
                    try:
                        pofile = polib.pofile(str(po_path))
                        pofile.save_as_mofile(str(mo_path))
                        self.stdout.write(f"Compiled {po_path} -> {mo_path}")
                        compiled_any = True
                    except Exception as e:  # pragma: no cover
                        self.stderr.write(f"Failed to compile {po_path}: {e}")

        if not compiled_any:
            self.stdout.write("No .po files found to compile.")