from flask import Flask, jsonify, render_template, request

from database import clear_history, get_history, init_db, save_translation
from models import LANGUAGES, detect_language, translate

app = Flask(__name__)
init_db()

# Quick lookup so the API can return a clean display name for any code.
_CODE_TO_NAME = {row["code"]: row["name"] for row in LANGUAGES}


@app.route("/")
def index():
    return render_template("index.html", languages=LANGUAGES)


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    source_lang = data.get("source_lang")
    target_lang = data.get("target_lang")

    if not text:
        return jsonify({"error": "Type something to translate."}), 400
    if not target_lang:
        return jsonify({"error": "Choose a language to translate into."}), 400

    auto_detected = source_lang == "auto"
    detected_name = None

    if auto_detected:
        src_code, iso, detected_name = detect_language(text)
    else:
        src_code = source_lang
        # New: check the manually picked source language against what's
        # actually in the text. Catches cases like Hindi text + French selected.
        actual_code, iso, actual_name = detect_language(text)
        if actual_code != src_code:
            selected_name = _CODE_TO_NAME.get(src_code, src_code)
            return jsonify({
                "error": f"This text looks like {actual_name}, not {selected_name}. "
                         f"Pick the correct source language or edit the text."
            }), 400

    if src_code == target_lang:
        return jsonify({"error": "Source and target languages are the same."}), 400

    try:
        translated_text = translate(text, src_code, target_lang)
    except Exception as exc:
        return jsonify({"error": f"Translation failed: {exc}"}), 500

    save_translation(text, translated_text, src_code, target_lang, auto_detected)

    return jsonify(
        {
            "translated_text": translated_text,
            "resolved_source_lang": src_code,
            "resolved_source_name": _CODE_TO_NAME.get(src_code, src_code),
            "auto_detected": auto_detected,
            "detected_label": detected_name,
        }
    )


@app.route("/api/history", methods=["GET"])
def api_history():
    rows = get_history()
    for row in rows:
        row["source_name"] = _CODE_TO_NAME.get(row["source_lang"], row["source_lang"])
        row["target_name"] = _CODE_TO_NAME.get(row["target_lang"], row["target_lang"])
    return jsonify(rows)


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    clear_history()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
