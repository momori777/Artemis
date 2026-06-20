# modified from https://github.com/CjangCjengh/vits/blob/main/text/japanese.py
# NOTE: pyopenjtalk replaced with pykakasi fallback for Windows compat
import re
import os
import hashlib
import warnings

# Try pyopenjtalk first, fallback to pykakasi
try:
    import pyopenjtalk as _pjt
except ImportError:
    try:
        import pykakasi
        _kks = pykakasi.kakasi()
        class _PyOpenJTalkFallback:
            """pyopenjtalk-compatible fallback using pykakasi"""
            @staticmethod
            def g2p(text):
                result = _kks.convert(text)
                phones = []
                for item in result:
                    hira = item.get("hira", item.get("orig", ""))
                    for ch in hira:
                        phones.append(ch)
                return " ".join(phones)
        _pjt = _PyOpenJTalkFallback()
        warnings.warn("pyopenjtalk not available; using pykakasi fallback for Japanese G2P. "
                      "TTS quality may be reduced.")
    except ImportError:
        _pjt = None
        warnings.warn("Neither pyopenjtalk nor pykakasi is available. Japanese TTS will not work.")

pyopenjtalk = _pjt

from text.symbols import punctuation

# Regular expression matching Japanese punctuation marks:
_japanese_marks = re.compile(
    r"[^A-Za-z\d々぀-ヿ一-鿿１-９Ａ-Ｚａ-ｚｦ-ﾟ]"
)

_japanese_characters = re.compile(r"[々぀-ヿ一-鿿ｦ-ﾟ]")

# Copied from espnet
def pyopenjtalk_g2p_prosody(text, drop_unvoiced_vowels=True):
    """Fallback: use simple g2p"""
    if pyopenjtalk is None:
        return list(text)  # char-by-char fallback
    try:
        p = pyopenjtalk.g2p(text)
        return p.split(" ")
    except Exception:
        return list(text)

def preprocess_jap(text, with_prosody=False):
    if pyopenjtalk is None:
        # Fallback: just split into characters
        text = re.sub(r"\s+", "", text)
        return list(re.sub(r"[^぀-ヿ一-鿿々]", "", text))
    
    text = text.lower()
    sentences = re.split(_japanese_marks, text)
    marks = re.findall(_japanese_marks, text)
    result = []
    for i, sentence in enumerate(sentences):
        if re.match(_japanese_characters, sentence):
            if with_prosody and hasattr(pyopenjtalk, 'make_label'):
                labels = pyopenjtalk_g2p_prosody(sentence)
                result += labels[1:-1] if len(labels) > 2 else labels
            else:
                p = pyopenjtalk.g2p(sentence)
                result += p.split(" ")
        if i < len(marks):
            if marks[i] != " ":
                result += [marks[i]]
    return result


def g2p(text):
    """Module-level G2P function expected by cleaner.py"""
    if text is None or text == "":
        return [], []
    phones = preprocess_jap(text)
    word2ph = [1] * len(phones) if phones else []
    return phones, word2ph

def text_normalize(text):
    # simple: no-op for now
    return text
