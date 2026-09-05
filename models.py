"""
Translation engine for the app.

Uses facebook/nllb-200-distilled-600M (Meta AI, open source, free) via
Hugging Face transformers for translation across 200 languages, and the
lightweight `langdetect` library for automatic source-language detection.

The model is loaded once and cached in memory (see load_model()) so the
first request after starting the server will be slow (downloading +
loading weights), and every request after that will be fast.
"""

from langdetect import detect, DetectorFactory
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Make langdetect deterministic (it's probabilistic by default).
DetectorFactory.seed = 0

MODEL_NAME = "facebook/nllb-200-distilled-600M"

_tokenizer = None
_model = None


def load_model():
    """Lazily load and cache the tokenizer + model (first call only)."""
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model


# Languages available in the UI. "code" is the FLORES-200 / NLLB code,
# "iso" is the ISO 639-1 code used by langdetect for auto-detection.
# Add more rows here to extend the dropdown -- NLLB-200 supports ~200
# languages in total, this is a practical, curated subset.
LANGUAGES = [
    {"code": "eng_Latn", "name": "English", "native": "English", "iso": "en"},
    {"code": "ben_Beng", "name": "Bengali", "native": "বাংলা", "iso": "bn"},
    {"code": "hin_Deva", "name": "Hindi", "native": "हिन्दी", "iso": "hi"},
    {"code": "urd_Arab", "name": "Urdu", "native": "اردو", "iso": "ur"},
    {"code": "spa_Latn", "name": "Spanish", "native": "Español", "iso": "es"},
    {"code": "fra_Latn", "name": "French", "native": "Français", "iso": "fr"},
    {"code": "deu_Latn", "name": "German", "native": "Deutsch", "iso": "de"},
    {"code": "ita_Latn", "name": "Italian", "native": "Italiano", "iso": "it"},
    {"code": "por_Latn", "name": "Portuguese", "native": "Português", "iso": "pt"},
    {"code": "rus_Cyrl", "name": "Russian", "native": "Русский", "iso": "ru"},
    {"code": "zho_Hans", "name": "Chinese (Simplified)", "native": "中文", "iso": "zh-cn"},
    {"code": "jpn_Jpan", "name": "Japanese", "native": "日本語", "iso": "ja"},
    {"code": "kor_Hang", "name": "Korean", "native": "한국어", "iso": "ko"},
    {"code": "arb_Arab", "name": "Arabic", "native": "العربية", "iso": "ar"},
    {"code": "tur_Latn", "name": "Turkish", "native": "Türkçe", "iso": "tr"},
    {"code": "vie_Latn", "name": "Vietnamese", "native": "Tiếng Việt", "iso": "vi"},
    {"code": "tha_Thai", "name": "Thai", "native": "ไทย", "iso": "th"},
    {"code": "ind_Latn", "name": "Indonesian", "native": "Indonesia", "iso": "id"},
    {"code": "nld_Latn", "name": "Dutch", "native": "Nederlands", "iso": "nl"},
    {"code": "pol_Latn", "name": "Polish", "native": "Polski", "iso": "pl"},
    {"code": "ukr_Cyrl", "name": "Ukrainian", "native": "Українська", "iso": "uk"},
    {"code": "swe_Latn", "name": "Swedish", "native": "Svenska", "iso": "sv"},
    {"code": "pes_Arab", "name": "Persian", "native": "فارسی", "iso": "fa"},
    {"code": "tam_Taml", "name": "Tamil", "native": "தமிழ்", "iso": "ta"},
    {"code": "tel_Telu", "name": "Telugu", "native": "తెలుగు", "iso": "te"},
    {"code": "mal_Mlym", "name": "Malayalam", "native": "മലയാളം", "iso": "ml"},
    {"code": "mar_Deva", "name": "Marathi", "native": "मराठी", "iso": "mr"},
    {"code": "guj_Gujr", "name": "Gujarati", "native": "ગુજરાતી", "iso": "gu"},
    {"code": "pan_Guru", "name": "Punjabi", "native": "ਪੰਜਾਬੀ", "iso": "pa"},
    {"code": "npi_Deva", "name": "Nepali", "native": "नेपाली", "iso": "ne"},
    {"code": "sin_Sinh", "name": "Sinhala", "native": "සිංහල", "iso": "si"},
    {"code": "mya_Mymr", "name": "Burmese", "native": "မြန်မာ", "iso": "my"},
    {"code": "khm_Khmr", "name": "Khmer", "native": "ខ្មែរ", "iso": "km"},
    {"code": "lao_Laoo", "name": "Lao", "native": "ລາວ", "iso": "lo"},
    {"code": "ell_Grek", "name": "Greek", "native": "Ελληνικά", "iso": "el"},
    {"code": "heb_Hebr", "name": "Hebrew", "native": "עברית", "iso": "he"},
    {"code": "ces_Latn", "name": "Czech", "native": "Čeština", "iso": "cs"},
    {"code": "ron_Latn", "name": "Romanian", "native": "Română", "iso": "ro"},
    {"code": "hun_Latn", "name": "Hungarian", "native": "Magyar", "iso": "hu"},
    {"code": "fin_Latn", "name": "Finnish", "native": "Suomi", "iso": "fi"},
    {"code": "dan_Latn", "name": "Danish", "native": "Dansk", "iso": "da"},
    {"code": "nob_Latn", "name": "Norwegian", "native": "Norsk", "iso": "no"},
    {"code": "swh_Latn", "name": "Swahili", "native": "Kiswahili", "iso": "sw"},
    {"code": "amh_Ethi", "name": "Amharic", "native": "አማርኛ", "iso": "am"},
    {"code": "som_Latn", "name": "Somali", "native": "Soomaali", "iso": "so"},
    {"code": "tgl_Latn", "name": "Filipino", "native": "Tagalog", "iso": "tl"},
]

# langdetect's ISO 639-1 code -> our NLLB code, built from LANGUAGES above.
_ISO_TO_NLLB = {row["iso"]: row["code"] for row in LANGUAGES}
_ISO_TO_NAME = {row["iso"]: row["name"] for row in LANGUAGES}


def detect_language(text):
    """
    Detect the language of `text`.
    Returns (nllb_code, iso_code, display_name).
    Falls back to English if detection fails or the detected language
    isn't one of the languages this app supports (langdetect covers
    ~55 languages; NLLB covers 200, so a few exotic scripts may not
    be auto-detectable -- they can still be picked manually).
    """
    try:
        iso = detect(text)
    except Exception:
        return "eng_Latn", "en", "English"

    if iso not in _ISO_TO_NLLB:
        return "eng_Latn", "en", "English (couldn't confidently detect)"

    return _ISO_TO_NLLB[iso], iso, _ISO_TO_NAME[iso]


def translate(text, src_code, tgt_code):
    """Translate `text` from src_code to tgt_code (both NLLB/FLORES-200 codes)."""
    tokenizer, model = load_model()
    tokenizer.src_lang = src_code
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_code)
    generated = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_length=512,
        num_beams=4,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
