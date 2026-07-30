:root {
  --bg: #0b0d12;
  --bg-soft: #11141b;
  --card: #161a23;
  --card-2: #1c2230;
  --border: #2a3142;
  --text: #e8ecf3;
  --text-dim: #97a0b3;
  --primary: #ff3b3b;
  --primary-2: #ff6b6b;
  --accent: #4f8cff;
  --ok: #2ecc71;
  --err: #ff5c5c;
  --warn: #ffb84d;
  --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  --radius: 14px;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(255, 59, 59, 0.18), transparent 60%),
    radial-gradient(1000px 500px at -10% 30%, rgba(79, 140, 255, 0.18), transparent 60%),
    var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, "Helvetica Neue", Arial, sans-serif;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

.app {
  max-width: 880px;
  margin: 0 auto;
  padding: 48px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero { text-align: center; margin-bottom: 8px; }
.hero h1 {
  font-size: 40px;
  margin: 0 0 8px;
  background: linear-gradient(90deg, #fff, #ffb3b3 60%, #ff6b6b);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: -0.02em;
}
.tagline { margin: 0; color: var(--text-dim); font-size: 15px; }

.card {
  background: linear-gradient(180deg, var(--card), var(--card-2));
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
}

.form { display: block; }

.label {
  display: block;
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 8px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

input[type="url"], input[type="file"], select {
  flex: 1 1 280px;
  min-width: 0;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input[type="file"] {
  padding: 9px 14px;
  font-size: 14px;
}

input[type="url"]:focus, input[type="file"]:focus, select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(255, 59, 59, 0.18);
}

.btn {
  appearance: none;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  padding: 12px 18px;
  border-radius: 10px;
  background: var(--card-2);
  color: var(--text);
  border: 1px solid var(--border);
  transition: transform 0.05s ease, background 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.btn:hover { border-color: #3a4356; }
.btn:active { transform: translateY(1px); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn.primary {
  background: linear-gradient(180deg, var(--primary-2), var(--primary));
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 18px rgba(255, 59, 59, 0.28);
}
.btn.primary:hover { filter: brightness(1.05); }
.btn.big { width: 100%; justify-content: center; padding: 14px 18px; font-size: 16px; margin-top: 16px; }
.btn.danger { color: #ffb0b0; border-color: #5a2a2a; }
.btn.danger:hover { background: #2a1414; }

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hint { margin: 10px 0 0; font-size: 12px; color: var(--text-dim); }
.hint code { background: var(--bg-soft); padding: 1px 5px; border-radius: 4px; }

/* Info */
.info {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed var(--border);
}
.info-media img {
  width: 100%; border-radius: 10px; display: block;
  background: #000; aspect-ratio: 16 / 9; object-fit: cover;
}
.info-body h2 { margin: 0 0 6px; font-size: 18px; line-height: 1.3; }
.meta { margin: 0 0 8px; color: var(--text-dim); font-size: 13px; }
.meta .dot { margin: 0 6px; opacity: 0.5; }
.desc {
  margin: 6px 0 0; color: var(--text-dim); font-size: 13px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed var(--border);
}
.field label {
  display: block; font-size: 13px; color: var(--text-dim); margin-bottom: 8px;
  text-transform: uppercase; letter-spacing: 0.02em;
}

.seg {
  display: inline-flex; background: var(--bg-soft);
  border: 1px solid var(--border); border-radius: 10px; padding: 4px; gap: 4px; width: 100%;
}
.seg-btn {
  flex: 1; appearance: none; background: transparent; border: 0; color: var(--text-dim);
  padding: 9px 12px; font-weight: 600; border-radius: 8px; cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.seg-btn.active {
  background: linear-gradient(180deg, var(--primary-2), var(--primary));
  color: #fff; box-shadow: 0 4px 12px rgba(255, 59, 59, 0.25);
}

select {
  width: 100%; appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, var(--text-dim) 50%),
    linear-gradient(135deg, var(--text-dim) 50%, transparent 50%);
  background-position: calc(100% - 18px) 50%, calc(100% - 13px) 50%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  padding-right: 36px;
}

.status { margin: 12px 0 0; font-size: 13px; min-height: 18px; }
.status.ok    { color: var(--ok); }
.status.err   { color: var(--err); }
.status.warn  { color: var(--warn); }
.status.busy  { color: var(--accent); }

/* Cookies card */
.cookies-card details > summary {
  list-style: none;
  cursor: pointer;
  display: flex; align-items: center; justify-content: space-between;
  font-weight: 600;
  user-select: none;
}
.cookies-card details > summary::-webkit-details-marker { display: none; }
.cookies-card details[open] > summary { margin-bottom: 14px; }

.badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  font-weight: 600;
  background: var(--bg-soft);
  color: var(--text-dim);
  border: 1px solid var(--border);
}
.badge.ok   { background: rgba(46, 204, 113, 0.15); color: var(--ok); border-color: rgba(46, 204, 113, 0.4); }
.badge.warn { background: rgba(255, 184, 77, 0.15); color: var(--warn); border-color: rgba(255, 184, 77, 0.4); }

.cookies-body { display: block; }
.howto {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 12px 0;
}
.howto summary { cursor: pointer; color: var(--accent); font-weight: 600; font-size: 13px; }
.howto ol { margin: 10px 0 4px; padding-left: 22px; font-size: 13px; color: var(--text-dim); }
.howto li { margin-bottom: 4px; }
.howto a { color: var(--accent); }

.cookies-row { margin-top: 8px; }

.footer {
  margin-top: 8px;
  display: flex; justify-content: space-between;
  font-size: 12px; color: var(--text-dim);
}
.server-status::before { content: "● "; color: var(--text-dim); }
.server-status.ok::before  { color: var(--ok); }
.server-status.err::before { color: var(--err); }

@media (max-width: 640px) {
  .app { padding: 28px 14px 18px; }
  .hero h1 { font-size: 30px; }
  .info { grid-template-columns: 1fr; }
  .grid { grid-template-columns: 1fr; }
  .cookies-row { flex-direction: column; align-items: stretch; }
  .cookies-row .btn { width: 100%; justify-content: center; }
}
