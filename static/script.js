(() => {
  const inputText = document.getElementById("inputText");
  const outputText = document.getElementById("outputText");
  const charCount = document.getElementById("charCount");
  const fromLang = document.getElementById("fromLang");
  const toLang = document.getElementById("toLang");
  const swapBtn = document.getElementById("swapBtn");
  const translateBtn = document.getElementById("translateBtn");
  const translateBtnLabel = document.getElementById("translateBtnLabel");
  const errorMsg = document.getElementById("errorMsg");
  const detectedTag = document.getElementById("detectedTag");
  const copyBtn = document.getElementById("copyBtn");

  const historyBtn = document.getElementById("historyBtn");
  const drawer = document.getElementById("drawer");
  const drawerOverlay = document.getElementById("drawerOverlay");
  const drawerClose = document.getElementById("drawerClose");
  const drawerList = document.getElementById("drawerList");
  const clearHistoryBtn = document.getElementById("clearHistory");

  const OUTPUT_PLACEHOLDER = "Translation will appear here.";

  // ---------- character count ----------
  inputText.addEventListener("input", () => {
    charCount.textContent = `${inputText.value.length} / 2000`;
  });

  // ---------- swap languages ----------
  function syncSwapState() {
    swapBtn.disabled = fromLang.value === "auto";
  }
  fromLang.addEventListener("change", syncSwapState);
  syncSwapState();

  swapBtn.addEventListener("click", () => {
    if (swapBtn.disabled) return;
    const tmp = fromLang.value;
    fromLang.value = toLang.value;
    toLang.value = tmp;
    syncSwapState();
    swapBtn.classList.add("spin");
    setTimeout(() => swapBtn.classList.remove("spin"), 250);
  });

  // ---------- translate ----------
  function setLoading(isLoading) {
    translateBtn.disabled = isLoading;
    translateBtnLabel.textContent = isLoading ? "Translating\u2026" : "Translate";
  }

  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.add("show");
  }

  function clearError() {
    errorMsg.textContent = "";
    errorMsg.classList.remove("show");
  }

  async function runTranslate() {
    const text = inputText.value.trim();
    clearError();
    detectedTag.classList.remove("show");

    if (!text) {
      showError("Type something to translate.");
      return;
    }

    setLoading(true);
    outputText.classList.remove("placeholder");
    outputText.textContent = "Translating\u2026";

    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          source_lang: fromLang.value,
          target_lang: toLang.value,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Something went wrong.");
      }

      outputText.textContent = data.translated_text;

      if (data.auto_detected) {
        detectedTag.textContent = `Detected: ${data.resolved_source_name}`;
        detectedTag.classList.add("show");
      }
    } catch (err) {
      outputText.classList.add("placeholder");
      outputText.textContent = OUTPUT_PLACEHOLDER;
      showError(err.message || "Couldn't reach the translation server.");
    } finally {
      setLoading(false);
    }
  }

  translateBtn.addEventListener("click", runTranslate);

  inputText.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      runTranslate();
    }
  });

  // ---------- copy output ----------
  copyBtn.addEventListener("click", async () => {
    const text = outputText.textContent;
    if (!text || outputText.classList.contains("placeholder")) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = copyBtn.innerHTML;
      copyBtn.lastChild.textContent = " Copied";
      setTimeout(() => {
        copyBtn.innerHTML = original;
      }, 1200);
    } catch (err) {
      // Clipboard API unavailable -- fail silently, copy isn't critical.
    }
  });

  // ---------- history drawer ----------
  function openDrawer() {
    drawer.classList.add("open");
    drawerOverlay.classList.add("open");
    loadHistory();
  }

  function closeDrawer() {
    drawer.classList.remove("open");
    drawerOverlay.classList.remove("open");
  }

  historyBtn.addEventListener("click", openDrawer);
  drawerClose.addEventListener("click", closeDrawer);
  drawerOverlay.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });

  function timeAgo(isoString) {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  function buildHistoryItem(row) {
    const item = document.createElement("div");
    item.className = "history-item";

    const meta = document.createElement("div");
    meta.className = "history-item-meta";

    const pair = document.createElement("span");
    pair.className = "lang-pair";
    pair.textContent = `${row.source_name} \u2192 ${row.target_name}`;

    const time = document.createElement("span");
    time.className = "history-time";
    time.textContent = timeAgo(row.created_at);

    meta.appendChild(pair);
    meta.appendChild(time);

    const original = document.createElement("p");
    original.className = "history-original";
    original.textContent = row.original_text;

    const translated = document.createElement("p");
    translated.className = "history-translated";
    translated.textContent = row.translated_text;

    item.appendChild(meta);
    item.appendChild(original);
    item.appendChild(translated);

    item.addEventListener("click", () => {
      inputText.value = row.original_text;
      charCount.textContent = `${row.original_text.length} / 2000`;
      outputText.classList.remove("placeholder");
      outputText.textContent = row.translated_text;
      if ([...fromLang.options].some((o) => o.value === row.source_lang)) {
        fromLang.value = row.source_lang;
      }
      if ([...toLang.options].some((o) => o.value === row.target_lang)) {
        toLang.value = row.target_lang;
      }
      syncSwapState();
      detectedTag.classList.remove("show");
      closeDrawer();
    });

    return item;
  }

  async function loadHistory() {
    drawerList.innerHTML = '<p class="drawer-empty">Loading\u2026</p>';
    try {
      const res = await fetch("/api/history");
      const rows = await res.json();

      drawerList.innerHTML = "";
      if (!rows.length) {
        drawerList.innerHTML = '<p class="drawer-empty">No translations yet.</p>';
        return;
      }
      rows.forEach((row) => drawerList.appendChild(buildHistoryItem(row)));
    } catch (err) {
      drawerList.innerHTML = '<p class="drawer-empty">Couldn\u2019t load history.</p>';
    }
  }

  clearHistoryBtn.addEventListener("click", async () => {
    if (!confirm("Clear all translation history? This can't be undone.")) return;
    await fetch("/api/history", { method: "DELETE" });
    loadHistory();
  });
})();
