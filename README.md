# Translator

A final-year-project web app that translates text between 45+ languages
using a free, open-source pretrained model, with automatic source-language
detection and a saved history of past translations.

## Stack

- **Model**: [facebook/nllb-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M)
  -- Meta AI's "No Language Left Behind" model, open source, free, supports
  200 languages (this app exposes a curated 45 of them in the dropdown --
  see `models.py` to add more, it's just a list entry each).
- **Language detection**: [`langdetect`](https://pypi.org/project/langdetect/),
  a free, lightweight library (no extra model download).
- **Backend**: Flask + SQLite (no setup required, the database file is
  created automatically on first run).
- **Frontend**: plain HTML/CSS/JS, no build step.

## Setup

Requires Python 3.9+.

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

> **First request is slow.** The model (~2.4 GB) downloads from Hugging
> Face the first time you translate, then loads into memory. After that,
> every translation in the same server session is fast (a few seconds on
> CPU, near-instant on GPU). If you have a CUDA GPU, `torch` will use it
> automatically once you install the CUDA build of PyTorch.

## How it works

- **Translate**: type text, pick a "From" language (or leave it on
  *Detect language*) and a "To" language, then press Translate
  (or `Ctrl + Enter`). The request hits `POST /api/translate`, which runs
  detection (if needed) and the NLLB model, then saves the pair to SQLite.
- **History**: the clock icon opens a panel listing every translation
  you've made (original text, translation, language pair, time). Clicking
  an entry reloads it into the main view. `GET /api/history` and
  `DELETE /api/history` back this.
- **Database**: `translations.db` (SQLite) is created next to `app.py`.
  Schema: `id, original_text, translated_text, source_lang, target_lang,
  auto_detected, created_at`.

## Project structure

```
translator-app/
├── app.py              # Flask routes + API
├── models.py            # NLLB translation + langdetect auto-detect
├── database.py           # SQLite helpers
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── style.css
    ├── script.js
    └── watermark.svg
```

## Notes for your write-up

- NLLB-200-distilled-600M was chosen over alternatives like M2M-100
  (100 languages, MIT license) because it covers twice the languages and
  has notably stronger quality on low-resource languages, including
  Bengali and other South Asian languages -- worth mentioning if your
  project discussion touches on model selection trade-offs. NLLB's
  license is CC-BY-NC 4.0 (non-commercial), which fits an academic
  project; swap to M2M-100 if you need a permissive license for other
  reasons.
- `langdetect` supports ~55 languages, which is fewer than the 200 NLLB
  knows. If a user picks *Detect language* on a script it can't
  recognize confidently, the app falls back to English and shows a note
  in the UI rather than guessing wrong silently -- a reasonable
  limitation to call out in a "future work" section. A drop-in upgrade
  path is Meta's `fasttext` language-identification model (`lid.176`),
  which covers more languages at the cost of a small extra download.
- Everything here runs on CPU. If your demo machine is slow, consider
  switching `MODEL_NAME` in `models.py` to a smaller distilled checkpoint
  or pre-warming the model (call `translate()` once at startup) so the
  first live demo translation isn't the slow one.
