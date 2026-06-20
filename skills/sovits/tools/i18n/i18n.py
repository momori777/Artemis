"""Minimal I18n stub for GPT-SoVITS inference (no WebUI needed)."""

def scan_language_list():
    return []

class I18nAuto:
    """Stub: always returns the original key (no translation)."""
    def __init__(self, language=None):
        pass

    def __call__(self, key):
        return key
