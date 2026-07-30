// YT-DLP Web — frontend logic (v2)
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  // ---- State ------------------------------------------------------------
  let formatType = "video";
  let currentInfo = null;

  // ---- Elements ---------------------------------------------------------
  const infoForm = $("info-form");
  const infoBtn = $("info-btn");
  const urlInput = $("url");
  const infoBox = $("info");
  const thumb = $("thumb");
  const titleEl = $("title");
  const channelEl = $("channel");
  const durationEl = $("duration");
  const viewsEl = $("views");
  const descEl = $("desc");

  const downloadForm = $("download-form");
  const downloadBtn = $("download-btn");
  const qualitySel = $("quality");
  const qualityField = $("quality-field");
  const statusEl = $("status");

  const segBtns = document.querySelectorAll(".seg-btn");
  const serverStatus = $("server-status");

  const cookieFileInput = $("cookie-file");
  const cookieUploadBtn = $("cookie-upload-btn");
  const cookieClearBtn = $("cookie-clear-btn");
  const cookieBadge = $("cookie-badge");
  const cookieStatus = $("cookie-status");

  // ---- Helpers ----------------------------------------------------------
  function setBusy(btn, busy) {
    const label = btn.querySelector(".btn-label");
    const spinner = btn.querySelector(".spinner");
    btn.disabled = busy;
    if (label) label.style.opacity = busy ? "0.7" : "1";
    if (spinner) spinner.hidden = !busy;
  }

  function setStatus(text, kind = "") {
    statusEl.textContent = text || "";
    statusEl.className = "status" + (kind ? " " + kind : "");
  }

  function setCookieStatus(text, kind = "") {
    cookieStatus.textContent = text || "";
    cookieStatus.className = "status" + (kind ? " " + kind : "");
  }

  function fmtNumber(n) {
    if (n == null) return "";
    try { return new Intl.NumberFormat("en-US").format(n); } catch { return String(n); }
  }

  function fmtDuration(seconds) {
    if (!seconds || seconds < 0) return "";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function isYouTube(url) {
    return /youtube\.com|youtu\.be/.test(url || "");
  }

  // ---- Health check -----------------------------------------------------
  async function checkHealth() {
    try {
      const r = await fetch("/api/health");
      if (!r.ok) throw new Error(r.statusText);
      const d = await r.json();
      const flags = [
        `yt-dlp ${d.yt_dlp_version}`,
        d.ffmpeg ? "ffmpeg" : null,
        d.node ? "node" : null,
        d.pot_server ? "POT" : null,
      ].filter(Boolean).join(" · ");
      serverStatus.textContent = flags;
      serverStatus.className = "server-status ok";
    } catch (e) {
      serverStatus.textContent = "offline";
      serverStatus.className = "server-status err";
    }
  }

  // ---- Cookie status ----------------------------------------------------
  async function refreshCookieBadge() {
    try {
      const r = await fetch("/api/cookies/status");
      const d = await r.json();
      if (d.configured) {
        cookieBadge.textContent = "loaded";
        cookieBadge.className = "badge ok";
      } else {
        cookieBadge.textContent = "not set";
        cookieBadge.className = "badge warn";
      }
    } catch {
      cookieBadge.textContent = "?";
      cookieBadge.className = "badge";
    }
  }

  cookieUploadBtn.addEventListener("click", async () => {
    const file = cookieFileInput.files[0];
    if (!file) { setCookieStatus("Pick a cookies.txt file first.", "warn"); return; }
    setCookieStatus("Uploading…", "busy");
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch("/api/cookies/upload", { method: "POST", body: fd });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || `HTTP ${r.status}`);
      }
      const d = await r.json();
      setCookieStatus(`Cookies loaded (${d.size_bytes} bytes). Try YouTube again.`, "ok");
      refreshCookieBadge();
    } catch (e) {
      setCookieStatus(`Upload failed: ${e.message}`, "err");
    }
  });

  cookieClearBtn.addEventListener("click", async () => {
    try {
      await fetch("/api/cookies/clear", { method: "POST" });
      setCookieStatus("Cookies removed.", "");
      cookieFileInput.value = "";
      refreshCookieBadge();
    } catch (e) {
      setCookieStatus(`Could not clear: ${e.message}`, "err");
    }
  });

  // ---- Format switch ----------------------------------------------------
  function setFormat(type) {
    formatType = type;
    segBtns.forEach((b) => b.classList.toggle("active", b.dataset.format === type));
    if (type === "audio") {
      qualitySel.innerHTML = `
        <option value="320">320 kbps</option>
        <option value="192">192 kbps</option>
        <option value="128">128 kbps</option>
        <option value="96">96 kbps</option>
      `;
      qualityField.querySelector("label").textContent = "Bitrate";
    } else {
      qualitySel.innerHTML = `
        <option value="best">Best available</option>
        <option value="1080">1080p</option>
        <option value="720">720p</option>
        <option value="480">480p</option>
        <option value="360">360p</option>
      `;
      qualityField.querySelector("label").textContent = "Quality";
    }
  }
  segBtns.forEach((b) => b.addEventListener("click", () => setFormat(b.dataset.format)));

  // ---- Info fetch -------------------------------------------------------
  infoForm.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    setBusy(infoBtn, true);
    setStatus("");
    try {
      const r = await fetch(`/api/info?url=${encodeURIComponent(url)}&cookies=auto`);
      if (!r.ok) {
        let msg = `Request failed (${r.status})`;
        try { const body = await r.json(); if (body && body.detail) msg = body.detail; } catch {}
        throw new Error(msg);
      }
      const data = await r.json();
      currentInfo = data;

      thumb.src = data.thumbnail || "";
      thumb.alt = data.title || "thumbnail";
      titleEl.textContent = data.title || "(untitled)";
      channelEl.textContent = data.channel || data.uploader || "";
      durationEl.textContent = fmtDuration(data.duration);
      viewsEl.textContent = data.view_count != null ? `${fmtNumber(data.view_count)} views` : "";
      descEl.textContent = data.description || "";

      infoBox.hidden = false;
      downloadForm.hidden = false;
      if (isYouTube(url)) {
        setStatus("Ready. If YouTube returns a bot-check, upload cookies below and retry.", "warn");
      } else {
        setStatus("Ready. Choose a format and hit Download.", "");
      }
    } catch (e) {
      infoBox.hidden = true;
      downloadForm.hidden = true;
      currentInfo = null;
      setStatus(`Could not fetch info: ${e.message}`, "err");
    } finally {
      setBusy(infoBtn, false);
    }
  });

  // ---- Download ---------------------------------------------------------
  downloadForm.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    setBusy(downloadBtn, true);
    setStatus("Downloading… this can take a moment.", "busy");

    try {
      const r = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          format_type: formatType,
          quality: qualitySel.value,
          cookies: "auto",
        }),
      });

      if (!r.ok) {
        let msg = `Request failed (${r.status})`;
        try { const body = await r.json(); if (body && body.detail) msg = body.detail; } catch {}
        throw new Error(msg);
      }

      const cd = r.headers.get("Content-Disposition") || "";
      const m = cd.match(/filename="?([^"]+)"?/);
      const filename = (m && m[1]) || (formatType === "audio" ? "audio.mp3" : "video.mp4");

      const blob = await r.blob();
      const sizeMB = (blob.size / (1024 * 1024)).toFixed(2);
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);

      setStatus(`Done — ${filename} (${sizeMB} MB)`, "ok");
    } catch (e) {
      setStatus(`Download failed: ${e.message}`, "err");
    } finally {
      setBusy(downloadBtn, false);
    }
  });

  // ---- Init -------------------------------------------------------------
  checkHealth();
  refreshCookieBadge();
  setFormat("video");
})();
