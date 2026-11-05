'use strict';
const app = document.getElementById('app');
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const store = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} }
};
const state = { token: store.get('al_token'), user: null };

/* ---------- icons ---------- */
const ic = d => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICON = {
  feed: ic('<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>'),
  upload: ic('<path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>'),
  user: ic('<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>'),
  sun: '<svg class="i i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/></svg>',
  moon: '<svg class="i i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/></svg>',
  trash: ic('<path d="M4 7h16M10 11v6m4-6v6M6 7l1 13h10l1-13M9 7V4h6v3"/>'),
  logout: ic('<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 8l-4 4 4 4M6 12h10"/>')
};
const LOGO = '<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><circle cx="12" cy="16" r="8"/><circle cx="20" cy="16" r="8"/></svg>';

/* ---------- helpers ---------- */
const handle = e => String(e || '?').split('@')[0];
const ini = n => { const p = String(n || '?').split(/[._\s-]+/).filter(Boolean); return ((p[0]?.[0] || '?') + (p[1]?.[0] || p[0]?.[1] || '')).toUpperCase(); };
const hue = n => [...String(n)].reduce((a, c) => a + c.charCodeAt(0) * 7, 0) % 360;
const avatar = (n, cls = '') => `<div class="av ${cls}" style="--c:hsl(${hue(n)} 55% 42%)">${esc(ini(n))}</div>`;
function ago(iso) {
  const d = new Date(/(Z|[+-]\d\d:?\d\d)$/i.test(iso) ? iso : iso + 'Z');
  const s = (d - Date.now()) / 1000, rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  for (const [u, n] of [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]])
    if (Math.abs(s) >= n) return rtf.format(Math.round(s / n), u);
  return 'just now';
}
// ImageKit: https://ik.imagekit.io/<id>/<path>  ->  .../<id>/tr:w-<w>/<path>
const resize = (url, w) => { const p = url.split('/'); return p.length > 4 ? `${p.slice(0, 4).join('/')}/tr:w-${w}/${p.slice(4).join('/')}` : url; };

function toast(msg, bad = false) {
  const t = document.createElement('div');
  t.className = 'toast' + (bad ? ' bad' : ''); t.textContent = msg;
  $('#toasts').append(t); setTimeout(() => t.remove(), 3800);
}
async function busy(btn, fn) {
  const label = btn.textContent; btn.disabled = true;
  try { return await fn(); } finally { btn.disabled = false; btn.textContent = label; }
}
function confirmBox(title, text, ok) {
  return new Promise(res => {
    const d = document.createElement('dialog');
    d.innerHTML = `<div class="dlg"><h3>${esc(title)}</h3><p>${esc(text)}</p><div class="row end"><button class="btn ghost" value="no">Cancel</button><button class="btn danger" value="yes">${esc(ok)}</button></div></div>`;
    document.body.append(d);
    d.addEventListener('click', e => { const b = e.target.closest('button'); if (b) d.close(b.value); });
    d.addEventListener('close', () => { res(d.returnValue === 'yes'); d.remove(); });
    d.showModal();
  });
}
function lightbox(url) {
  const d = document.createElement('dialog');
  d.innerHTML = `<div class="lb"><img src="${esc(url)}" alt=""><button aria-label="Close">×</button></div>`;
  document.body.append(d);
  d.addEventListener('click', e => { if (e.target.tagName !== 'IMG') d.close(); });
  d.addEventListener('close', () => d.remove());
  d.showModal();
}

/* ---------- theme ---------- */
const themeSwitch = () => `<button class="tswitch" role="switch" aria-label="Dark mode" aria-checked="${document.documentElement.dataset.theme === 'dark'}" data-theme-toggle><span class="knob">${ICON.sun}${ICON.moon}</span></button>`;
function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next; store.set('al_theme', next);
  document.querySelectorAll('[data-theme-toggle]').forEach(b => b.setAttribute('aria-checked', next === 'dark'));
}

/* ---------- api ---------- */
async function api(path, { method = 'GET', json, form, auth = true } = {}) {
  const headers = {}; let body;
  if (auth && state.token) headers.Authorization = 'Bearer ' + state.token;
  if (json) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); } else if (form) body = form;
  let res;
  try { res = await fetch(path, { method, headers, body }); }
  catch { throw new Error('Can’t reach the server. Check that FastAPI is running.'); }
  if (res.status === 401 && auth && state.token) { await signOut(false); throw new Error('Your session expired. Log in again.'); }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? (d[0]?.msg || 'Check the form and try again.') : `Request failed (${res.status})`);
  }
  return data;
}
async function signOut(callApi = true) {
  if (callApi && state.token) { try { await api('/users/logout', { method: 'POST' }); } catch {} }
  state.token = null; state.user = null; store.set('al_token', null);
  location.hash = '#/feed'; route();
}
function uploadFile(file, caption, onProgress) {
  return new Promise((resolve, reject) => {
    const x = new XMLHttpRequest(), f = new FormData();
    f.append('file', file); f.append('caption', caption);
    x.open('POST', '/posts/'); x.setRequestHeader('Authorization', 'Bearer ' + state.token);
    x.upload.onprogress = e => e.lengthComputable && onProgress(e.loaded / e.total);
    x.onload = () => { let d = null; try { d = JSON.parse(x.responseText); } catch {} x.status < 300 ? resolve(d) : reject(new Error(typeof d?.detail === 'string' ? d.detail : 'Upload failed')); };
    x.onerror = () => reject(new Error('Can’t reach the server. Check that FastAPI is running.'));
    x.send(f);
  });
}

/* ---------- auth view ---------- */
function renderAuth() {
  let mode = 'login';
  const draw = () => {
    app.innerHTML = `<div class="auth">${themeSwitch()}<div class="auth-box">
      <div class="logo">${LOGO}<span>Auralink</span></div>
      <h1>Photos and videos, shared.</h1>
      <p>Log in to see what everyone posted, or create an account to add your own.</p>
      <div class="panel">
        <div class="seg" role="tablist"><button role="tab" data-mode="login" aria-selected="${mode === 'login'}">Log in</button><button role="tab" data-mode="signup" aria-selected="${mode === 'signup'}">Create account</button></div>
        ${mode === 'login' ? `
        <form id="f" novalidate>
          <label class="field">Username<input name="username" autocomplete="username" required></label>
          <label class="field">Password<input name="password" type="password" autocomplete="current-password" required></label>
          <div class="err" role="alert"></div><button class="btn block">Log in</button>
        </form>` : `
        <form id="f" novalidate>
          <div class="two"><label class="field">First name<input name="first" autocomplete="given-name" required></label><label class="field">Last name<input name="last" autocomplete="family-name" required></label></div>
          <label class="field">Username<input name="username" autocomplete="username" required></label>
          <label class="field">Email<input name="email" type="email" autocomplete="email" required></label>
          <label class="field">Password (6+ characters)<input name="password" type="password" minlength="6" autocomplete="new-password" required></label>
          <div class="err" role="alert"></div><button class="btn block">Create account</button>
        </form>`}
      </div></div></div>`;
    $('[data-mode]', app) && app.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => { mode = b.dataset.mode; draw(); });
    $('#f').onsubmit = async e => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target)), err = $('.err'), btn = $('.btn.block');
      err.textContent = '';
      if (Object.values(f).some(v => !v.trim())) { err.textContent = 'Fill in every field.'; return; }
      try {
        await busy(btn, async () => {
          if (mode === 'signup') {
            if (f.password.length < 6) throw new Error('Use a password with at least 6 characters.');
            await api('/auth/', { method: 'POST', auth: false, json: { first_name: f.first, last_name: f.last, user_name: f.username, email: f.email, hash_password: f.password, role: 'user' } });
            toast('Account created. Logging you in…');
          }
          const t = await api('/auth/token', { method: 'POST', auth: false, form: new URLSearchParams({ username: f.username, password: f.password }) });
          state.token = t.access_token; store.set('al_token', state.token);
          state.user = await api('/users/');
          location.hash = '#/feed'; route();
        });
      } catch (x) { err.textContent = x.message; }
    };
  };
  draw();
}

/* ---------- shell ---------- */
function shell(active) {
  const u = state.user;
  const nav = [['feed', 'Feed', ICON.feed], ['upload', 'New post', ICON.upload], ['profile', 'Profile', ICON.user]]
    .map(([k, l, i]) => `<a href="#/${k}" ${k === active ? 'aria-current="page"' : ''}>${i}<span>${l}</span></a>`).join('');
  app.innerHTML = `<div class="shell">
    <aside class="rail">
      <a class="logo" href="#/feed">${LOGO}<span>Auralink</span></a>
      <nav aria-label="Main">${nav}</nav>
      <div class="rail-foot">
        <div class="me">${avatar(u.user_name)}<div><b>${esc(u.user_name)}</b><small>${esc(u.email)}</small></div></div>
        <div class="row">${themeSwitch()}<button class="btn ghost" data-logout style="flex:1">${ICON.logout}Log out</button></div>
      </div>
    </aside>
    <div><header class="topbar"><a class="logo" href="#/feed">${LOGO}<span>Auralink</span></a>${themeSwitch()}</header><main class="main" id="view"></main></div>
  </div>`;
  return $('#view');
}
const head = (t, s) => `<div class="head"><h1>${t}</h1><p>${s}</p></div>`;

/* ---------- feed ---------- */
function card(p) {
  const n = handle(p.email), mine = p.email === state.user.email;
  const media = p.file_type === 'video'
    ? `<video src="${esc(p.url)}" controls preload="metadata" playsinline></video>`
    : `<button class="media" data-zoom="${esc(p.url)}" aria-label="View larger"><img src="${esc(resize(p.url, 720))}" alt="${esc(p.caption || 'Photo by ' + n)}" loading="lazy"></button>`;
  return `<article class="card"><header>${avatar(n)}<div class="who"><b>${esc(n)}</b><time datetime="${esc(p.created_at)}">${ago(p.created_at)}</time></div>
    ${mine ? `<button class="icon-btn" data-del="${esc(p.id)}" aria-label="Delete post">${ICON.trash}</button>` : ''}</header>
    ${media}${p.caption ? `<p class="cap">${esc(p.caption)}</p>` : ''}</article>`;
}
async function renderFeed(v) {
  v.innerHTML = head('Feed', 'The latest from everyone on Auralink.') + `<div class="chips" id="chips"></div><div class="grid" id="grid">${'<div class="skel"></div>'.repeat(6)}</div>`;
  const grid = $('#grid'); let posts, filter = 'all';
  try { posts = (await api('/posts/feed', { auth: false })).posts; }
  catch (e) { grid.innerHTML = `<div class="empty"><h2>Couldn’t load the feed</h2><p>${esc(e.message)}</p><button class="btn" onclick="route()">Try again</button></div>`; return; }
  const draw = () => {
    const count = t => posts.filter(p => t === 'all' || p.file_type === t).length;
    $('#chips').innerHTML = [['all', 'All'], ['image', 'Photos'], ['video', 'Videos']]
      .map(([k, l]) => `<button class="chip" data-f="${k}" aria-pressed="${filter === k}">${l}<b>${count(k)}</b></button>`).join('');
    const list = posts.filter(p => filter === 'all' || p.file_type === filter);
    grid.innerHTML = list.length ? list.map(card).join('')
      : `<div class="empty"><h2>${filter === 'all' ? 'Nothing here yet' : 'No ' + (filter === 'image' ? 'photos' : 'videos') + ' yet'}</h2><p>Be the first to share something.</p><a class="btn" href="#/upload">Add a post</a></div>`;
  };
  draw();
  $('#chips').onclick = e => { const b = e.target.closest('[data-f]'); if (b) { filter = b.dataset.f; draw(); } };
  grid.onclick = async e => {
    const z = e.target.closest('[data-zoom]'), d = e.target.closest('[data-del]');
    if (z) return lightbox(z.dataset.zoom);
    if (d && await confirmBox('Delete this post?', 'It will be removed from the feed for everyone.', 'Delete post')) {
      try { await api('/posts/delete/' + d.dataset.del, { method: 'DELETE' }); posts = posts.filter(p => String(p.id) !== d.dataset.del); draw(); toast('Post deleted.'); }
      catch (x) { toast(x.message, true); }
    }
  };
}

/* ---------- upload ---------- */
function renderUpload(v) {
  v.innerHTML = head('New post', 'Add a photo or video. It shows up in the feed as soon as it uploads.') + `
  <form class="upload" id="uf">
    <label class="drop" id="drop">${ICON.upload}<strong>Choose a file or drop it here</strong><span>JPG, PNG, GIF, MP4, MOV or WebM</span>
      <input class="sr" type="file" name="file" accept="image/*,video/*"></label>
    <label class="field">Caption<textarea name="caption" placeholder="Say something about it (optional)"></textarea></label>
    <div class="bar" hidden><i></i></div>
    <button class="btn" disabled>Post</button>
  </form>`;
  const form = $('#uf'), drop = $('#drop'), input = $('input', form), btn = $('.btn', form), bar = $('.bar', form);
  let file = null;
  const pick = f => {
    if (!f) return;
    if (!/^(image|video)\//.test(f.type)) return toast('Pick an image or video file.', true);
    file = f; btn.disabled = false; drop.classList.add('has');
    const u = URL.createObjectURL(f);
    drop.innerHTML = (f.type.startsWith('video/') ? `<video src="${u}" controls></video>` : `<img src="${u}" alt="Preview">`) + '<input class="sr" type="file" accept="image/*,video/*">';
    $('input', drop).onchange = e => pick(e.target.files[0]);
  };
  input.onchange = () => pick(input.files[0]);
  ['dragenter', 'dragover'].forEach(t => drop.addEventListener(t, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(t => drop.addEventListener(t, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => pick(e.dataTransfer.files[0]));
  form.onsubmit = async e => {
    e.preventDefault(); if (!file) return;
    btn.disabled = true; btn.textContent = 'Uploading…'; bar.hidden = false;
    try {
      await uploadFile(file, form.caption.value.trim(), r => $('i', bar).style.width = Math.round(r * 100) + '%');
      toast('Posted.'); location.hash = '#/feed';
    } catch (x) { toast(x.message, true); btn.disabled = false; btn.textContent = 'Post'; bar.hidden = true; }
  };
}

/* ---------- profile ---------- */
function renderProfile(v) {
  const u = state.user, full = `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.user_name;
  v.innerHTML = head('Profile', 'Your account details and security.') + `<div class="profile">
    <div class="panel id-card">${avatar(u.user_name, 'lg')}<div><h2>${esc(full)}</h2><div class="muted">@${esc(u.user_name)}<span class="tag">${esc(u.role)}</span></div><div class="muted">${esc(u.email)}</div></div></div>
    <form class="panel" id="pw" novalidate><h3>Change password</h3>
      <label class="field">Current password<input name="password" type="password" autocomplete="current-password"></label>
      <label class="field">New password (6+ characters)<input name="new_password" type="password" autocomplete="new-password"></label>
      <div class="err" role="alert"></div><button class="btn">Update password</button></form>
    <div class="panel"><h3>Session</h3><button class="btn ghost" data-logout>${ICON.logout}Log out</button></div>
    <div class="panel warn"><h3>Delete account</h3><p class="muted" style="margin-bottom:1rem">This removes your account permanently. It can’t be undone.</p><button class="btn danger" id="del">Delete my account</button></div></div>`;
  $('#pw').onsubmit = async e => {
    e.preventDefault(); const f = e.target, err = $('.err', f); err.textContent = '';
    if (!f.password.value || f.new_password.value.length < 6) { err.textContent = 'Enter your current password and a new one with 6+ characters.'; return; }
    try {
      await busy($('.btn', f), () => api('/users/password', { method: 'PUT', json: { password: f.password.value, new_password: f.new_password.value } }));
      f.reset(); toast('Password updated.');
    } catch (x) { err.textContent = x.message; }
  };
  $('#del').onclick = async () => {
    if (!await confirmBox('Delete your account?', 'Your account will be removed permanently.', 'Delete account')) return;
    try { await api('/users/', { method: 'DELETE' }); toast('Account deleted.'); await signOut(false); }
    catch (x) { toast(x.message, true); }
  };
}

/* ---------- router ---------- */
async function route() {
  if (state.token && !state.user) { try { state.user = await api('/users/'); } catch { state.token = null; store.set('al_token', null); } }
  if (!state.user) return renderAuth();
  const views = { feed: renderFeed, upload: renderUpload, profile: renderProfile };
  const page = location.hash.replace('#/', '');
  const key = views[page] ? page : 'feed';
  await views[key](shell(key));
  window.scrollTo(0, 0);
}
document.addEventListener('click', e => {
  if (e.target.closest('[data-theme-toggle]')) toggleTheme();
  if (e.target.closest('[data-logout]')) signOut();
});
window.addEventListener('hashchange', route);
route();
