import os
import re
import json
import time
import base64
import hashlib
from urllib.parse import quote, urlparse

import requests
from flask import Flask, request, make_response
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

API_BASE = 'https://api.mydot.one/mydot/api/v1'
ORIGIN = 'https://mydot.one'
REFERER = 'https://mydot.one/'
COOKIE = 'mydot_sess'
TOKEN_SKEW = 60
SESSION_MAX_AGE = 60 * 60 * 24 * 30
SECRET = os.environ.get('APP_SECRET') or 'change-me-please-set-APP_SECRET'
COOKIE_SECURE = os.environ.get('COOKIE_SECURE', '1') != '0'
UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
AUTHOR_NAME = 'Nima'
AUTHOR_URL = 'https://mydot.one/profile/nimaa'

HTML = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<meta name="color-scheme" content="dark light" />
<meta name="author" content="Nima" />
<title>MyDot • مدیریت فالوورها</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
:root {
  --bg: #05060f;
  --bg2: #0a0c1c;
  --text: #e8ecff;
  --muted: #8b93c4;
  --neon1: #4d7cff;
  --neon2: #b14dff;
  --neon3: #00e5ff;
  --danger: #ff3d7f;
  --ok: #2bff9e;
  --glass-bg: rgba(20, 24, 52, 0.5);
  --glass-brd: rgba(120, 140, 255, 0.22);
  --glow: 0 0 0 1px rgba(120,140,255,0.12), 0 0 22px rgba(77,124,255,0.18);
  --radius: clamp(14px, 2vw, 18px);
  --font: 'Vazirmatn', 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Orbitron', 'Vazirmatn', sans-serif;
}
body[data-theme="light"] {
  --bg: #eef1fb;
  --bg2: #e2e7fb;
  --text: #141a33;
  --muted: #5b647e;
  --glass-bg: rgba(255, 255, 255, 0.66);
  --glass-brd: rgba(90, 110, 220, 0.28);
  --glow: 0 0 0 1px rgba(90,110,220,0.12), 0 10px 30px rgba(80,100,200,0.16);
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  font-family: var(--font);
  color: var(--text);
  background:
    radial-gradient(1100px 700px at 82% -10%, rgba(177,77,255,0.18), transparent 60%),
    radial-gradient(900px 700px at 10% 110%, rgba(0,229,255,0.14), transparent 60%),
    radial-gradient(1200px 900px at 50% 50%, var(--bg2), var(--bg));
  background-attachment: fixed;
  min-height: 100dvh;
  overflow-x: hidden;
  -webkit-text-size-adjust: 100%;
  transition: color 0.4s ease;
}
.aurora { position: fixed; inset: 0; z-index: 0; filter: blur(80px); opacity: 0.5; pointer-events: none; }
.aurora span { position: absolute; border-radius: 50%; display: block; mix-blend-mode: screen; }
.aurora span:nth-child(1) { width: 42vmax; height: 42vmax; background: var(--neon1); top: -12vmax; right: -8vmax; animation: float1 16s ease-in-out infinite; }
.aurora span:nth-child(2) { width: 34vmax; height: 34vmax; background: var(--neon2); bottom: -12vmax; left: -6vmax; animation: float2 19s ease-in-out infinite; }
.aurora span:nth-child(3) { width: 28vmax; height: 28vmax; background: var(--neon3); top: 42%; left: 52%; animation: float1 22s ease-in-out infinite; }
@keyframes float1 { 50% { transform: translate(-4vmax, 4vmax) scale(1.12); } }
@keyframes float2 { 50% { transform: translate(4vmax, -3vmax) scale(1.1); } }
@media (prefers-reduced-motion: reduce) { .aurora span, .brand-dot, .loader span { animation: none !important; } }
.glass {
  background: var(--glass-bg);
  border: 1px solid var(--glass-brd);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  backdrop-filter: blur(20px) saturate(150%);
  box-shadow: var(--glow), inset 0 1px 0 rgba(255,255,255,0.08);
  border-radius: var(--radius);
}
.hidden { display: none !important; }
.muted { color: var(--muted); }
.view { position: relative; z-index: 1; }
.login-view { min-height: 100dvh; display: grid; place-items: center; padding: clamp(16px, 4vw, 28px); }
.login-card { width: min(420px, 100%); padding: clamp(26px, 5vw, 38px) clamp(20px, 4vw, 32px); position: relative; overflow: hidden; }
.login-card::before {
  content: ''; position: absolute; inset: -1px; border-radius: inherit; padding: 1px;
  background: linear-gradient(135deg, var(--neon1), var(--neon2), var(--neon3));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude; opacity: 0.6; pointer-events: none;
}
.brand { text-align: center; margin-bottom: 22px; }
.brand-dot {
  width: 60px; height: 60px; margin: 0 auto 14px; border-radius: 18px;
  background: linear-gradient(135deg, var(--neon1), var(--neon2));
  box-shadow: 0 0 30px rgba(77,124,255,0.7), 0 0 60px rgba(177,77,255,0.4);
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse { 50% { box-shadow: 0 0 42px rgba(77,124,255,0.9), 0 0 80px rgba(177,77,255,0.6); } }
.brand h1 { margin: 0; font-family: var(--font-mono); font-size: clamp(1.3rem, 4vw, 1.55rem); font-weight: 800; letter-spacing: 1px; text-shadow: 0 0 18px rgba(77,124,255,0.5); }
.field { display: block; margin-bottom: 16px; }
.field > span { display: block; font-size: 0.86rem; margin-bottom: 7px; color: var(--muted); }
input, .search {
  width: 100%; padding: 13px 15px; border-radius: 13px; font: inherit; color: var(--text);
  background: rgba(10,12,30,0.55); border: 1px solid var(--glass-brd); outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
body[data-theme="light"] input, body[data-theme="light"] .search { background: rgba(255,255,255,0.6); }
input:focus, .search:focus { border-color: var(--neon1); box-shadow: 0 0 0 3px rgba(77,124,255,0.22), 0 0 18px rgba(77,124,255,0.35); }
.pwd-wrap { position: relative; display: block; }
.pwd-toggle { position: absolute; inset-inline-end: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1.05rem; opacity: 0.8; color: inherit; }
.btn {
  border: 1px solid var(--glass-brd); color: var(--text); cursor: pointer;
  padding: 12px 18px; border-radius: 13px; font: inherit; font-weight: 600;
  background: var(--glass-bg); -webkit-tap-highlight-color: transparent;
  transition: transform 0.12s ease, box-shadow 0.25s ease, border-color 0.25s, opacity 0.2s;
}
.btn:hover { transform: translateY(-1px); border-color: var(--neon1); box-shadow: 0 0 18px rgba(77,124,255,0.4); }
.btn:active { transform: translateY(0) scale(0.98); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-primary {
  width: 100%; color: #fff; border-color: transparent;
  background: linear-gradient(135deg, var(--neon1), var(--neon2));
  box-shadow: 0 0 22px rgba(77,124,255,0.55), 0 0 40px rgba(177,77,255,0.3);
}
.btn-primary:hover { box-shadow: 0 0 30px rgba(77,124,255,0.8), 0 0 60px rgba(177,77,255,0.5); }
.danger-ghost { color: var(--danger); }
.danger-ghost:hover { border-color: var(--danger); box-shadow: 0 0 18px rgba(255,61,127,0.4); }
.error { color: var(--danger); min-height: 18px; margin: 10px 0 0; font-size: 0.86rem; text-align: center; text-shadow: 0 0 10px rgba(255,61,127,0.4); }
.hint { font-size: 0.78rem; text-align: center; margin-top: 16px; }
.credit { text-align: center; font-size: 0.78rem; color: var(--muted); margin-top: 18px; line-height: 1.9; }
.author { display: inline-flex; align-items: center; gap: 7px; margin-top: 8px; padding: 6px 14px; border-radius: 99px; text-decoration: none; font-weight: 700; color: var(--text); border: 1px solid var(--glass-brd); background: var(--glass-bg); transition: border-color 0.25s, box-shadow 0.25s, transform 0.12s; }
.author::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: linear-gradient(135deg, var(--neon1), var(--neon2)); box-shadow: 0 0 8px rgba(77,124,255,0.75); }
.author:hover { border-color: var(--neon1); box-shadow: 0 0 16px rgba(77,124,255,0.4); transform: translateY(-1px); }
.app-credit { padding: 14px; text-align: center; }
.theme-toggle { position: fixed; top: max(16px, env(safe-area-inset-top)); inset-inline-start: 16px; z-index: 5; width: 44px; height: 44px; padding: 0; border-radius: 13px; cursor: pointer; font-size: 1.15rem; color: inherit; }
.app-view { max-width: 940px; margin: 0 auto; padding: clamp(16px, 3vw, 24px) clamp(12px, 3vw, 18px) 70px; display: flex; flex-direction: column; gap: 16px; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; gap: 12px; flex-wrap: wrap; }
.profile { display: flex; align-items: center; gap: 12px; min-width: 0; }
.avatar {
  width: 46px; height: 46px; flex: 0 0 auto; border-radius: 50%;
  display: grid; place-items: center; font-weight: 700; font-family: var(--font-mono);
  color: #fff; letter-spacing: 0.5px;
  background: linear-gradient(135deg, hsl(var(--h, 220) 82% 60%), hsl(calc(var(--h, 220) + 42) 82% 54%));
  border: 1px solid rgba(255,255,255,0.22); box-shadow: 0 0 14px rgba(77,124,255,0.32);
}
.profile-meta { display: flex; flex-direction: column; min-width: 0; }
.profile-meta strong { font-size: 1rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.profile-meta span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topbar-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat { padding: 16px; text-align: center; }
.stat span { display: block; font-family: var(--font-mono); font-size: clamp(1.4rem, 5vw, 1.7rem); font-weight: 800; line-height: 1; color: var(--neon3); text-shadow: 0 0 16px rgba(0,229,255,0.55); }
.stat label { display: block; margin-top: 8px; font-size: 0.76rem; color: var(--muted); }
.stat.danger span { color: var(--danger); text-shadow: 0 0 16px rgba(255,61,127,0.55); }
.tabs { display: flex; padding: 6px; gap: 6px; }
.tab { flex: 1; border: 1px solid transparent; background: transparent; color: var(--muted); padding: 10px; border-radius: 12px; cursor: pointer; font: inherit; font-weight: 600; transition: all 0.22s; white-space: nowrap; }
.tab:hover { color: var(--text); }
.tab.active { color: #fff; background: linear-gradient(135deg, var(--neon1), var(--neon2)); box-shadow: 0 0 20px rgba(77,124,255,0.55); }
.toolbar { display: flex; gap: 10px; flex-wrap: wrap; }
.search { flex: 1; min-width: 180px; }
.toolbar .btn-primary { width: auto; flex: 0 0 auto; }
.bulk-bar { display: flex; align-items: center; gap: 12px; padding: 12px 16px; flex-wrap: wrap; }
.bulk-progress { flex: 1; min-width: 140px; height: 8px; border-radius: 99px; background: rgba(120,140,255,0.14); overflow: hidden; }
.bulk-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--neon3), var(--neon1), var(--neon2)); box-shadow: 0 0 14px rgba(0,229,255,0.6); transition: width 0.3s ease; }
.cards { display: flex; flex-direction: column; gap: 10px; }
.card { display: flex; align-items: center; gap: 14px; padding: 12px 16px; animation: rise 0.3s ease both; transition: border-color 0.25s, box-shadow 0.25s, transform 0.35s, opacity 0.35s; }
.card:hover { border-color: var(--neon1); box-shadow: 0 0 20px rgba(77,124,255,0.3); }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } }
.card.removing { opacity: 0; transform: translateX(40px); }
.card .avatar { width: 48px; height: 48px; font-size: 0.95rem; }
.card .who { flex: 1; min-width: 0; }
.card .who b { display: flex; align-items: center; gap: 6px; overflow: hidden; }
.card .who b > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card .who .uname { color: var(--muted); font-size: 0.84rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
.badge { font-size: 0.64rem; padding: 2px 8px; border-radius: 99px; background: rgba(177,77,255,0.18); color: #d9b6ff; border: 1px solid rgba(177,77,255,0.35); flex: 0 0 auto; }
.verified { color: var(--neon3); font-size: 0.85rem; text-shadow: 0 0 8px rgba(0,229,255,0.6); flex: 0 0 auto; }
.act { padding: 9px 16px; border-radius: 11px; font-weight: 600; min-width: 92px; flex: 0 0 auto; }
.act.unfollow { color: var(--danger); border-color: rgba(255,61,127,0.4); background: rgba(255,61,127,0.1); }
.act.unfollow:hover { box-shadow: 0 0 18px rgba(255,61,127,0.45); border-color: var(--danger); }
.act.follow { color: var(--ok); border-color: rgba(43,255,158,0.4); background: rgba(43,255,158,0.1); }
.act.follow:hover { box-shadow: 0 0 18px rgba(43,255,158,0.45); border-color: var(--ok); }
.empty { text-align: center; padding: 40px 0; }
.loader { display: grid; place-items: center; padding: 30px; }
.loader span { width: 36px; height: 36px; border-radius: 50%; border: 3px solid rgba(120,140,255,0.18); border-top-color: var(--neon3); box-shadow: 0 0 18px rgba(0,229,255,0.45); animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.toast { position: fixed; bottom: max(22px, env(safe-area-inset-bottom)); left: 50%; transform: translateX(-50%) translateY(30px); z-index: 9; padding: 12px 20px; border-radius: 13px; background: var(--glass-bg); border: 1px solid var(--glass-brd); -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px); box-shadow: var(--glow); opacity: 0; pointer-events: none; transition: all 0.3s ease; max-width: 90vw; text-align: center; }
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.toast.ok { border-color: rgba(43,255,158,0.55); box-shadow: 0 0 22px rgba(43,255,158,0.35); }
.toast.err { border-color: rgba(255,61,127,0.55); box-shadow: 0 0 22px rgba(255,61,127,0.35); }
@media (max-width: 560px) {
  .topbar { justify-content: center; text-align: center; }
  .profile { width: 100%; justify-content: center; }
  .topbar-actions { width: 100%; justify-content: center; }
  .toolbar .btn-primary { width: 100%; }
}
</style>
</head>
<body data-theme="dark">
<div class="aurora"><span></span><span></span><span></span></div>
<button id="themeToggle" class="theme-toggle glass" type="button" aria-label="تغییر تم">☀️</button>
<main id="loginView" class="view login-view">
  <section class="glass login-card">
    <div class="brand">
      <div class="brand-dot"></div>
      <h1>MyDot Manager</h1>
      <p class="muted">ورود با حساب mydot.one</p>
    </div>
    <form id="loginForm" autocomplete="on">
      <label class="field">
        <span>نام کاربری یا ایمیل</span>
        <input id="identifier" name="identifier" type="text" required autocomplete="username" placeholder="username" />
      </label>
      <label class="field">
        <span>گذرواژه</span>
        <span class="pwd-wrap">
          <input id="password" name="password" type="password" required autocomplete="current-password" placeholder="••••••••" />
          <button type="button" id="pwdToggle" class="pwd-toggle" aria-label="نمایش گذرواژه">👁️</button>
        </span>
      </label>
      <button id="loginBtn" type="submit" class="btn btn-primary glass">ورود</button>
      <p id="loginError" class="error" role="alert"></p>
    </form>
    <p class="hint muted">اطلاعات ورود به‌صورت رمزنگاری‌شده فقط روی سرور خودت ذخیره می‌شود.</p>
    <p class="credit">طراحی و توسعه توسط <br><a class="author" href="__AUTHOR_URL__" target="_blank" rel="noopener noreferrer">__AUTHOR_NAME__</a></p>
  </section>
</main>
<main id="appView" class="view app-view hidden">
  <header class="topbar glass">
    <div class="profile">
      <div id="meAvatar" class="avatar" aria-hidden="true"></div>
      <div class="profile-meta">
        <strong id="meName">—</strong>
        <span id="meUsername" class="muted">@—</span>
      </div>
    </div>
    <div class="topbar-actions">
      <button id="refreshBtn" class="btn glass" type="button">بازخوانی</button>
      <button id="logoutBtn" class="btn glass danger-ghost" type="button">خروج</button>
    </div>
  </header>
  <section class="stats">
    <div class="glass stat"><span id="statFollowers">0</span><label>دنبال‌کننده</label></div>
    <div class="glass stat"><span id="statFollowing">0</span><label>دنبال‌شده</label></div>
    <div class="glass stat danger"><span id="statNotBack">0</span><label>فالوبک نکرده</label></div>
    <div class="glass stat"><span id="statFans">0</span><label>فالو نکردی</label></div>
  </section>
  <nav class="tabs glass">
    <button class="tab active" data-tab="notback">فالوبک نکرده</button>
    <button class="tab" data-tab="fans">فالو نکردی</button>
    <button class="tab" data-tab="mutuals">دوطرفه</button>
  </nav>
  <section class="toolbar">
    <input id="searchBox" class="glass search" type="search" placeholder="جستجوی نام یا یوزرنام…" />
    <button id="bulkBtn" class="btn btn-primary glass" type="button">عملیات گروهی</button>
  </section>
  <div id="bulkBar" class="glass bulk-bar hidden">
    <div class="bulk-progress"><div id="bulkFill" class="bulk-fill"></div></div>
    <span id="bulkLabel" class="muted">آماده</span>
    <button id="bulkCancel" class="btn glass" type="button">توقف</button>
  </div>
  <section id="list" class="cards"></section>
  <p id="emptyState" class="muted empty hidden">چیزی برای نمایش نیست.</p>
  <div id="loader" class="loader hidden"><span></span></div>
  <footer class="glass app-credit credit">ساخته‌شده توسط <a class="author" href="__AUTHOR_URL__" target="_blank" rel="noopener noreferrer">__AUTHOR_NAME__</a></footer>
</main>
<div id="toast" class="toast"></div>
<script>
const state = { active: 'notback', data: { notback: [], fans: [], mutuals: [] }, bulkRunning: false, bulkCancel: false }
const headers = { 'Content-Type': 'application/json', 'X-Requested-With': 'mydot-tool' }
const $ = sel => document.querySelector(sel)
const el = (tag, cls) => { const n = document.createElement(tag); if (cls) n.className = cls; return n }
const sleep = ms => new Promise(r => setTimeout(r, ms))
const escapeHtml = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
function initials(name) {
  const s = String(name == null ? '' : name).trim()
  if (!s) return '?'
  const parts = s.split(/\s+/)
  if (parts.length > 1) return (parts[0][0] + parts[1][0]).toUpperCase()
  return s.slice(0, 2).toUpperCase()
}
function hueFrom(str) {
  const s = String(str == null ? '' : str)
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360
  return h
}
function fillAvatar(node, label, seed) {
  node.textContent = initials(label)
  node.style.setProperty('--h', String(hueFrom(seed || label)))
}
let toastTimer = null
function toast(message, kind) {
  const t = $('#toast')
  t.textContent = message
  t.className = 'toast show ' + (kind || '')
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { t.className = 'toast ' + (kind || '') }, 3200)
}
async function api(path, options) {
  const res = await fetch(path, options)
  let body = {}
  try { body = await res.json() } catch (e) {}
  if (!res.ok) {
    const error = new Error((body && body.error) || 'request_failed')
    error.status = res.status
    throw error
  }
  return body
}
function setTheme(theme) {
  document.body.dataset.theme = theme
  $('#themeToggle').textContent = theme === 'dark' ? '☀️' : '🌙'
  try { localStorage.setItem('mydot-theme', theme) } catch (e) {}
}
function showView(name) {
  $('#loginView').classList.toggle('hidden', name !== 'login')
  $('#appView').classList.toggle('hidden', name !== 'app')
}
function setProfile(profile) {
  $('#meName').textContent = profile.display_name || profile.username || '—'
  $('#meUsername').textContent = '@' + (profile.username || '')
  fillAvatar($('#meAvatar'), profile.display_name || profile.username, profile.username)
}
function currentList() { return state.data[state.active] || [] }
function actionFor(tab) {
  if (tab === 'notback') return { type: 'unfollow', label: 'آنفالو', cls: 'unfollow' }
  if (tab === 'fans') return { type: 'follow', label: 'فالو', cls: 'follow' }
  return null
}
function renderList() {
  const list = $('#list')
  list.innerHTML = ''
  const term = ($('#searchBox').value || '').trim().toLowerCase()
  const action = actionFor(state.active)
  const items = currentList().filter(u =>
    !term || (u.username || '').toLowerCase().includes(term) || (u.display_name || '').toLowerCase().includes(term)
  )
  $('#emptyState').classList.toggle('hidden', items.length > 0)
  $('#bulkBtn').classList.toggle('hidden', !action || items.length === 0)
  for (const u of items) list.appendChild(renderCard(u, action))
}
function renderCard(u, action) {
  const card = el('article', 'card glass')
  card.dataset.id = u.id
  const av = el('div', 'avatar')
  fillAvatar(av, u.display_name || u.username, u.username)
  const who = el('div', 'who')
  const name = el('b')
  const nameText = el('span')
  nameText.textContent = u.display_name || u.username || ''
  name.appendChild(nameText)
  if (u.is_verified) {
    const v = el('span', 'verified')
    v.textContent = '✔'
    name.appendChild(v)
  }
  if (u.account_type && u.account_type !== 'standard') {
    const b = el('span', 'badge')
    b.textContent = u.account_type
    name.appendChild(b)
  }
  const uname = el('span', 'uname')
  uname.textContent = '@' + u.username
  who.appendChild(name)
  who.appendChild(uname)
  card.appendChild(av)
  card.appendChild(who)
  if (action) {
    const btn = el('button', 'btn act ' + action.cls)
    btn.type = 'button'
    btn.textContent = action.label
    btn.addEventListener('click', () => runSingle(u, action, btn, card))
    card.appendChild(btn)
  }
  return card
}
async function runSingle(user, action, btn, card) {
  if (btn.disabled) return
  btn.disabled = true
  btn.textContent = '…'
  try {
    await api('/api/' + action.type, { method: 'POST', headers, body: JSON.stringify({ target_id: user.id }) })
    removeFromState(user.id)
    card.classList.add('removing')
    setTimeout(() => { card.remove(); refreshCountsUi(); if (currentList().length === 0) $('#emptyState').classList.remove('hidden') }, 350)
    toast('@' + user.username + ' ' + (action.type === 'unfollow' ? 'آنفالو شد' : 'فالو شد'), 'ok')
  } catch (e) {
    btn.disabled = false
    btn.textContent = action.label
    toast('خطا در عملیات (' + (e.status || '?') + ')', 'err')
  }
}
function removeFromState(id) {
  for (const key of Object.keys(state.data)) {
    state.data[key] = state.data[key].filter(u => u.id !== id)
  }
}
function refreshCountsUi() {
  $('#statNotBack').textContent = state.data.notback.length
  $('#statFans').textContent = state.data.fans.length
}
async function runBulk() {
  const action = actionFor(state.active)
  if (!action || state.bulkRunning) return
  const targets = currentList().slice()
  if (targets.length === 0) return
  if (!confirm(action.label + ' گروهی برای ' + targets.length + ' حساب؟')) return
  state.bulkRunning = true
  state.bulkCancel = false
  $('#bulkBar').classList.remove('hidden')
  $('#bulkBtn').disabled = true
  let done = 0
  let failed = 0
  for (const user of targets) {
    if (state.bulkCancel) break
    $('#bulkLabel').textContent = 'در حال ' + action.label + ': @' + user.username + ' (' + (done + 1) + '/' + targets.length + ')'
    try {
      await api('/api/' + action.type, { method: 'POST', headers, body: JSON.stringify({ target_id: user.id }) })
      removeFromState(user.id)
      const card = document.querySelector('.card[data-id="' + user.id + '"]')
      if (card) { card.classList.add('removing'); setTimeout(() => card.remove(), 350) }
    } catch (e) {
      failed += 1
    }
    done += 1
    $('#bulkFill').style.width = Math.round((done / targets.length) * 100) + '%'
    refreshCountsUi()
    if (!state.bulkCancel && done < targets.length) await sleep(900 + Math.floor(Math.random() * 800))
  }
  state.bulkRunning = false
  $('#bulkBtn').disabled = false
  $('#bulkLabel').textContent = 'تمام شد — موفق: ' + (done - failed) + (failed ? '، ناموفق: ' + failed : '')
  if (currentList().length === 0) $('#emptyState').classList.remove('hidden')
  toast('عملیات گروهی تمام شد', failed ? 'err' : 'ok')
  setTimeout(() => $('#bulkBar').classList.add('hidden'), 2500)
}
async function loadData() {
  $('#loader').classList.remove('hidden')
  $('#list').innerHTML = ''
  $('#emptyState').classList.add('hidden')
  try {
    const data = await api('/api/analyze')
    state.data.notback = data.notFollowingBack || []
    state.data.fans = data.fans || []
    state.data.mutuals = data.mutuals || []
    $('#statFollowers').textContent = data.counts.followers
    $('#statFollowing').textContent = data.counts.following
    $('#statNotBack').textContent = data.counts.notFollowingBack
    $('#statFans').textContent = data.counts.fans
    renderList()
  } catch (e) {
    if (e.status === 401) return logout()
    toast('خطا در دریافت دیتا', 'err')
  } finally {
    $('#loader').classList.add('hidden')
  }
}
async function startApp(profile) {
  setProfile(profile)
  showView('app')
  await loadData()
}
async function logout() {
  try { await api('/api/logout', { method: 'POST', headers }) } catch (e) {}
  state.data = { notback: [], fans: [], mutuals: [] }
  showView('login')
}
function bindEvents() {
  $('#themeToggle').addEventListener('click', () => setTheme(document.body.dataset.theme === 'dark' ? 'light' : 'dark'))
  $('#pwdToggle').addEventListener('click', () => {
    const p = $('#password')
    p.type = p.type === 'password' ? 'text' : 'password'
  })
  $('#loginForm').addEventListener('submit', async e => {
    e.preventDefault()
    const btn = $('#loginBtn')
    $('#loginError').textContent = ''
    btn.disabled = true
    btn.textContent = 'در حال ورود…'
    try {
      const body = JSON.stringify({ identifier: $('#identifier').value, password: $('#password').value })
      const data = await api('/api/login', { method: 'POST', headers, body })
      await startApp(data.profile)
    } catch (err) {
      $('#loginError').textContent = err.status === 401 ? 'نام کاربری یا گذرواژه اشتباه است' : 'خطا در ورود، دوباره تلاش کنید'
    } finally {
      btn.disabled = false
      btn.textContent = 'ورود'
    }
  })
  $('#logoutBtn').addEventListener('click', logout)
  $('#refreshBtn').addEventListener('click', loadData)
  $('#bulkBtn').addEventListener('click', runBulk)
  $('#bulkCancel').addEventListener('click', () => { state.bulkCancel = true })
  $('#searchBox').addEventListener('input', renderList)
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'))
      tab.classList.add('active')
      state.active = tab.dataset.tab
      renderList()
    })
  })
}
async function init() {
  try { setTheme(localStorage.getItem('mydot-theme') || 'dark') } catch (e) { setTheme('dark') }
  bindEvents()
  try {
    const data = await api('/api/me')
    await startApp(data.profile)
  } catch (e) {
    showView('login')
  }
}
init()
</script>
</body>
</html>
""".replace('__AUTHOR_NAME__', AUTHOR_NAME).replace('__AUTHOR_URL__', AUTHOR_URL)

app = Flask(__name__)


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def unb64url(text):
    pad = '=' * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def get_key():
    return hashlib.sha256(SECRET.encode('utf-8')).digest()


def seal(obj):
    iv = os.urandom(12)
    data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    ct = AESGCM(get_key()).encrypt(iv, data, None)
    return b64url(iv + ct)


def unseal(blob):
    raw = unb64url(blob)
    iv = raw[:12]
    ct = raw[12:]
    pt = AESGCM(get_key()).decrypt(iv, ct, None)
    return json.loads(pt.decode('utf-8'))


def token_exp(token):
    try:
        seg = token.split('.')[1]
        pad = '=' * (-len(seg) % 4)
        payload = json.loads(base64.urlsafe_b64decode(seg.replace('-', '+').replace('_', '/') + pad))
        return int(payload.get('exp', 0))
    except Exception:
        return 0


def csrf_ok():
    return (request.headers.get('X-Requested-With') or '') != ''


def json_response(obj, status=200, cookie=None, clear=False):
    resp = make_response(json.dumps(obj, ensure_ascii=False), status)
    resp.headers['Content-Type'] = 'application/json; charset=utf-8'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    if clear:
        resp.set_cookie(COOKIE, '', max_age=0, path='/', httponly=True, secure=COOKIE_SECURE, samesite='Strict')
    elif cookie is not None:
        resp.set_cookie(COOKIE, cookie, max_age=SESSION_MAX_AGE, path='/', httponly=True, secure=COOKIE_SECURE, samesite='Strict')
    return resp


def extract_token(res):
    token = res.cookies.get('__Secure-access_token')
    if token:
        return token
    raw = res.headers.get('set-cookie') or ''
    match = re.search(r'__Secure-access_token=([^;]+)', raw)
    return match.group(1) if match else None


def mydot_login(identifier, password):
    try:
        res = requests.post(
            API_BASE + '/auth/login/',
            json={'identifier': identifier, 'password': password},
            headers={'Accept': 'application/json', 'Origin': ORIGIN, 'Referer': REFERER},
            timeout=30,
        )
    except requests.RequestException:
        return {'ok': False, 'status': 0, 'token': None, 'body': {}}
    try:
        body = res.json()
    except ValueError:
        body = {}
    token = extract_token(res)
    return {'ok': res.ok and bool(token), 'status': res.status_code, 'token': token, 'body': body}


def mydot(method, path, token, payload=None):
    req_headers = {'Accept': 'application/json', 'Origin': ORIGIN, 'Referer': REFERER, 'Cookie': '__Secure-access_token=' + token}
    try:
        if payload is not None:
            res = requests.request(method, API_BASE + path, headers=req_headers, json=payload, timeout=30)
        else:
            res = requests.request(method, API_BASE + path, headers=req_headers, timeout=30)
    except requests.RequestException:
        return False, 0, {}
    try:
        body = res.json()
    except ValueError:
        body = {}
    return res.ok, res.status_code, body


def ensure_fresh(session):
    now = int(time.time())
    if session.get('exp', 0) - TOKEN_SKEW > now:
        return session, False, True
    result = mydot_login(session.get('id'), session.get('pw'))
    if not result['ok']:
        return session, False, False
    session['token'] = result['token']
    session['exp'] = token_exp(result['token'])
    return session, True, True


def get_session():
    raw = request.cookies.get(COOKIE)
    if not raw:
        return None
    try:
        return unseal(raw)
    except Exception:
        return None


def slim(user):
    return {
        'id': user.get('id'),
        'username': user.get('username'),
        'display_name': user.get('display_name'),
        'account_type': user.get('account_type'),
        'is_verified': user.get('is_verified'),
    }


def fetch_all(username, kind, token):
    path = '/auth/' + quote(str(username)) + '/' + kind + '/?page_size=100'
    items = []
    guard = 0
    while path and guard < 200:
        ok, status, body = mydot('GET', path, token)
        if not ok:
            break
        results = (body.get('results') if isinstance(body, dict) else None) or []
        items.extend(results)
        nxt = body.get('next') if isinstance(body, dict) else None
        if nxt:
            parsed = urlparse(nxt)
            path = parsed.path.replace('/mydot/api/v1', '')
            if parsed.query:
                path += '?' + parsed.query
        else:
            path = None
        guard += 1
    return items


@app.route('/', methods=['GET'])
def route_index():
    resp = make_response(HTML)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['X-Frame-Options'] = 'DENY'
    return resp


@app.route('/api/login', methods=['POST'])
def route_login():
    if not csrf_ok():
        return json_response({'error': 'forbidden'}, 403)
    body = request.get_json(silent=True) or {}
    identifier = (body.get('identifier') or '').strip()
    password = body.get('password') or ''
    if not identifier or not password:
        return json_response({'error': 'missing_credentials'}, 400)
    result = mydot_login(identifier, password)
    if not result['ok']:
        return json_response({'error': 'invalid_credentials'}, 401)
    ok, status, profile = mydot('GET', '/auth/profile/', result['token'])
    if not ok:
        return json_response({'error': 'profile_failed'}, 502)
    session = {
        'id': identifier,
        'pw': password,
        'token': result['token'],
        'exp': token_exp(result['token']),
        'username': profile.get('username'),
        'display_name': profile.get('display_name'),
    }
    cookie = seal(session)
    return json_response({'profile': {'username': profile.get('username'), 'display_name': profile.get('display_name')}}, 200, cookie)


@app.route('/api/logout', methods=['POST'])
def route_logout():
    return json_response({'ok': True}, 200, clear=True)


@app.route('/api/me', methods=['GET'])
def route_me():
    session = get_session()
    if not session:
        return json_response({'error': 'unauthorized'}, 401)
    session, refreshed, ok = ensure_fresh(session)
    if not ok:
        return json_response({'error': 'unauthorized'}, 401, clear=True)
    cookie = seal(session) if refreshed else None
    return json_response({'profile': {'username': session.get('username'), 'display_name': session.get('display_name')}}, 200, cookie)


@app.route('/api/analyze', methods=['GET'])
def route_analyze():
    session = get_session()
    if not session:
        return json_response({'error': 'unauthorized'}, 401)
    session, refreshed, ok = ensure_fresh(session)
    if not ok:
        return json_response({'error': 'unauthorized'}, 401, clear=True)
    token = session.get('token')
    username = session.get('username')
    following = fetch_all(username, 'following', token)
    followers = fetch_all(username, 'followers', token)
    follower_ids = {u.get('id') for u in followers}
    following_ids = {u.get('id') for u in following}
    not_back = [slim(u) for u in following if u.get('id') not in follower_ids]
    fans = [slim(u) for u in followers if u.get('id') not in following_ids]
    mutuals = [slim(u) for u in following if u.get('id') in follower_ids]
    cookie = seal(session) if refreshed else None
    return json_response({
        'counts': {
            'followers': len(followers),
            'following': len(following),
            'notFollowingBack': len(not_back),
            'fans': len(fans),
        },
        'notFollowingBack': not_back,
        'fans': fans,
        'mutuals': mutuals,
    }, 200, cookie)


def handle_act(kind):
    if not csrf_ok():
        return json_response({'error': 'forbidden'}, 403)
    session = get_session()
    if not session:
        return json_response({'error': 'unauthorized'}, 401)
    body = request.get_json(silent=True) or {}
    target = (body.get('target_id') or '').strip()
    if not UUID_RE.match(target):
        return json_response({'error': 'invalid_target'}, 400)
    session, refreshed, ok = ensure_fresh(session)
    if not ok:
        return json_response({'error': 'unauthorized'}, 401, clear=True)
    ok, status, body = mydot('POST', '/auth/' + kind + '/', session.get('token'), {'target_id': target})
    cookie = seal(session) if refreshed else None
    if not ok:
        out_status = status if 400 <= status < 600 else 502
        return json_response({'error': 'action_failed', 'status': status}, out_status, cookie)
    return json_response({'ok': True}, 200, cookie)


@app.route('/api/follow', methods=['POST'])
def route_follow():
    return handle_act('follow')


@app.route('/api/unfollow', methods=['POST'])
def route_unfollow():
    return handle_act('unfollow')


@app.errorhandler(404)
def route_not_found(_error):
    return json_response({'error': 'not_found'}, 404)


@app.errorhandler(500)
def route_server_error(_error):
    return json_response({'error': 'server_error'}, 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))
