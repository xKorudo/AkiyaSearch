// ── shared.js ────────────────────────────────────────────────────────────────
// Shared state and functions for the AkiyaSearch multi-page app.
// Loaded by search.html, map.html, and discover.html.
// NO ES modules — plain globals only (static site, no bundler).
// Does NOT auto-init on load; each page's own DOMContentLoaded calls what it needs.

// ── STATE ────────────────────────────────────────────────────────────────────
let ALL = [], FILTERED = [], selectedId = null;
let FX = { EUR: 0.0062, USD: 0.0067, GBP: 0.0053, AUD: 0.0103 }; // fallback rates
const CUR_SYMBOL = { EUR: '€', USD: '$', GBP: '£', AUD: 'A$', JPY: '¥' };
let userCurrency = localStorage.getItem('akiya_currency') || 'EUR';

let supa = null, currentUser = null, FAVS = new Set(), favView = false, authMode = 'signin';
let WATCHLISTS = [], NOTIFS = [], notifSeenAt = null;
let SWIPES = {};
let _lbImgs = [], _lbIdx = 0, _detailImgs = [];

// ── LOOKUP TABLES ─────────────────────────────────────────────────────────────
const AIRBNB_TOURISM = {
  '沖縄':90,'京都':88,'大阪':82,'北海道':80,'東京':78,'広島':75,'長野':72,
  '山梨':70,'静岡':68,'福岡':67,'奈良':65,'鹿児島':63,'愛媛':62,'高知':60,
  '新潟':58,'岩手':55,'秋田':54,'島根':52,'鳥取':50,'宮崎':58,
};

const PREF_EN = {
  '北海道':'Hokkaido','青森':'Aomori','岩手':'Iwate','宮城':'Miyagi','秋田':'Akita',
  '山形':'Yamagata','福島':'Fukushima','茨城':'Ibaraki','栃木':'Tochigi','群馬':'Gunma',
  '埼玉':'Saitama','千葉':'Chiba','東京':'Tokyo','神奈川':'Kanagawa','新潟':'Niigata',
  '富山':'Toyama','石川':'Ishikawa','福井':'Fukui','山梨':'Yamanashi','長野':'Nagano',
  '岐阜':'Gifu','静岡':'Shizuoka','愛知':'Aichi','三重':'Mie','滋賀':'Shiga',
  '京都':'Kyoto','大阪':'Osaka','兵庫':'Hyogo','奈良':'Nara','和歌山':'Wakayama',
  '鳥取':'Tottori','島根':'Shimane','岡山':'Okayama','広島':'Hiroshima','山口':'Yamaguchi',
  '徳島':'Tokushima','香川':'Kagawa','愛媛':'Ehime','高知':'Kochi','福岡':'Fukuoka',
  '佐賀':'Saga','長崎':'Nagasaki','熊本':'Kumamoto','大分':'Oita','宮崎':'Miyazaki',
  '鹿児島':'Kagoshima','沖縄':'Okinawa',
};

const COND_EN = {
  '要リフォーム':'Needs renovation','要修繕':'Needs repair','要大規模修繕':'Major repairs needed',
  'リノベーション済み':'Renovated','良好':'Good condition','普通':'Fair condition',
  '要確認':'Condition unknown','古民家':'Traditional kominka','移住支援':'Migration support',
};

const SOURCE_LABELS = { 'SUUMO': '🏠 SUUMO', 'LIFULL Akiya Bank': '🏚 LIFULL Akiya Bank', 'AKIYA BANK': '🏚 Municipal Akiya Bank' };

// ── CURRENCY HELPERS ─────────────────────────────────────────────────────────
// Convert a JPY price into the user's chosen display currency (string).
function convPrice(jpy) {
  if (jpy == null) return '';
  if (userCurrency === 'JPY') return '¥' + Math.round(jpy).toLocaleString('de-DE');
  return CUR_SYMBOL[userCurrency] + Math.round(jpy * FX[userCurrency]).toLocaleString('de-DE');
}

// Compact price for map pins, e.g. €30K, €1.2M, FREE (currency-aware)
function convPriceShort(jpy) {
  if (jpy === 0) return 'FREE';
  if (jpy == null) return '?';
  if (userCurrency === 'JPY') {
    const man = jpy / 10000;
    return man >= 10000 ? '¥' + (man / 10000).toFixed(1) + '億' : '¥' + Math.round(man) + '万';
  }
  const v = jpy * FX[userCurrency];
  const sym = CUR_SYMBOL[userCurrency];
  if (v >= 1000000) return sym + (v / 1000000).toFixed(1) + 'M';
  if (v >= 1000) return sym + Math.round(v / 1000) + 'K';
  return sym + Math.round(v);
}

// Google Maps link — coordinates if available, otherwise Japanese title (contains full address)
function gmapsUrl(l) {
  if (l.lat && l.lng) {
    return `https://www.google.com/maps/search/?api=1&query=${l.lat},${l.lng}`;
  }
  // Japanese titles from SUUMO/LIFULL contain the full scraped address; Akiya2 titles are English
  const hasJpTitle = l.title && /[　-鿿]/.test(l.title);
  const addr = hasJpTitle ? l.title : `${l.prefecture||''}${l.city||''}`;
  const q = encodeURIComponent(`${addr} 日本`.trim());
  return `https://www.google.com/maps/search/?api=1&query=${q}`;
}

function setCurrency(c) {
  userCurrency = c;
  localStorage.setItem('akiya_currency', c);
  document.querySelectorAll('.cur-sym').forEach(s => s.textContent = CUR_SYMBOL[c]);
  if (typeof filter === 'function') filter();           // re-render cards + map markers with new currency
  if (selectedId) openDetail(selectedId);              // refresh open detail panel
}

// ── AUTH + FAVORITES ──────────────────────────────────────────────────────────
async function initAuth() {
  // Favorites are account-only (never persisted on the device) — start empty.
  FAVS = new Set();
  updateFavCount();

  if (typeof SUPABASE_URL !== 'undefined' && typeof SUPABASE_ANON_KEY !== 'undefined' &&
      SUPABASE_URL && SUPABASE_ANON_KEY && window.supabase) {
    supa = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    const { data } = await supa.auth.getSession();
    if (data && data.session) {
      currentUser = data.session.user;
      await loadCloudFavs();
      await loadWatchlistData(); await loadNotifs(); await loadSwipes();
    }
    supa.auth.onAuthStateChange(async (event, session) => {
      currentUser = session ? session.user : null;
      updateAuthUI();
      if (event === 'SIGNED_IN' && currentUser) {
        await loadCloudFavs();
        await loadWatchlistData(); await loadNotifs(); await loadSwipes();
        renderWatchlists();
        await handleJoinLink();
      }
    });
    await handleJoinLink();   // honor ?join=<token> invite links
  }
  updateAuthUI();
}

// Returns the signed-in user, recovering the session if auth init hasn't
// finished yet (prevents a false "sign in" when a click lands too early).
async function ensureUser() {
  if (currentUser) return currentUser;
  if (!supa) return null;
  try {
    const { data } = await supa.auth.getSession();
    if (data && data.session) {
      currentUser = data.session.user;
      updateAuthUI();
      return currentUser;
    }
  } catch {}
  return null;
}

function updateAuthUI() {
  const profileBtn = document.getElementById('profile-btn');
  const btn = document.getElementById('login-btn');
  if (!btn) return;
  if (currentUser) {
    if (profileBtn) profileBtn.style.display = '';
    btn.style.display = 'none';
    const emailEl = document.getElementById('profile-email');
    if (emailEl) emailEl.textContent = currentUser.email;
  } else {
    if (profileBtn) profileBtn.style.display = 'none';
    btn.style.display = '';
    const pm = document.getElementById('profile-menu');
    if (pm) pm.classList.remove('open');
  }
}

function toggleProfile() {
  const m = document.getElementById('profile-menu');
  if (!m) return;
  const opening = !m.classList.contains('open');
  m.classList.toggle('open', opening);
  if (opening) setTimeout(() => document.addEventListener('click', _profileClose), 0);
}
function _profileClose(e) {
  if (!e.target.closest('#profile-menu') && e.target.id !== 'profile-btn') {
    const pm = document.getElementById('profile-menu');
    if (pm) pm.classList.remove('open');
    document.removeEventListener('click', _profileClose);
  }
}

// --- favorites (account-only; nothing stored on the device) ---
function isFav(id) { return FAVS.has(id); }
function updateFavCount() {
  const el = document.getElementById('fav-count');
  if (el) el.textContent = FAVS.size;
}

async function toggleFav(id, el) {
  // Favorites require an account so they never persist on a shared device.
  if (!(await ensureUser())) { openAuth(); showToast('Sign in to save favorites'); return; }

  const adding = !FAVS.has(id);
  adding ? FAVS.add(id) : FAVS.delete(id);
  updateFavCount();

  // update the clicked control's appearance
  if (el) {
    el.classList.toggle('on', adding);
    if (el.classList.contains('dp-fav-btn')) el.textContent = adding ? '♥ Saved' : '♡ Save to favorites';
    else el.textContent = adding ? '♥' : '♡';
  }
  // keep card + detail hearts in sync
  document.querySelectorAll(`.fav-btn[onclick*="'${id}'"]`).forEach(b => { b.classList.toggle('on', adding); b.textContent = adding ? '♥' : '♡'; });

  if (favView && typeof filter === 'function') filter();  // if viewing favorites, refresh the list

  let error;
  if (adding) {
    ({ error } = await supa.from('favorites')
      .upsert({ user_id: currentUser.id, listing_id: id }, { onConflict: 'user_id,listing_id', ignoreDuplicates: true }));
  } else {
    ({ error } = await supa.from('favorites').delete().eq('user_id', currentUser.id).eq('listing_id', id));
  }
  if (error) { console.error('favorite sync failed:', error); showToast('⚠ Could not save favorite: ' + error.message); }
}

async function loadCloudFavs() {
  FAVS = new Set();
  if (!supa || !currentUser) { updateFavCount(); return; }
  const { data, error } = await supa.from('favorites').select('listing_id').eq('user_id', currentUser.id);
  if (error) { console.error('load favorites failed:', error); return; }
  (data || []).forEach(r => FAVS.add(r.listing_id));
  updateFavCount();
  if (typeof renderList === 'function') renderList();
}

function toggleFavView() {
  // Kept for compatibility; the "Saved" nav section now drives this.
  if (typeof setSection === 'function') setSection(favView ? 'search' : 'saved');
}

// --- auth modal ---
function openAuth() {
  if (!supa) { showToast('Login not configured yet — add Supabase keys'); return; }
  const el = document.getElementById('auth-overlay');
  if (el) el.classList.add('open');
  const msg = document.getElementById('auth-msg');
  if (msg) msg.textContent = '';
}
function closeAuth() {
  const el = document.getElementById('auth-overlay');
  if (el) el.classList.remove('open');
}
function authClickBg(e) {
  if (e.target === document.getElementById('auth-overlay')) closeAuth();
}
function toggleAuthMode() {
  authMode = authMode === 'signin' ? 'signup' : 'signin';
  const signin = authMode === 'signin';
  const title = document.getElementById('auth-title');
  const submit = document.getElementById('auth-submit');
  const switchText = document.getElementById('auth-switch-text');
  const switchLink = document.getElementById('auth-switch-link');
  const msg = document.getElementById('auth-msg');
  if (title) title.textContent = signin ? 'Sign in' : 'Create account';
  if (submit) submit.textContent = signin ? 'Sign in' : 'Create account';
  if (switchText) switchText.textContent = signin ? 'No account?' : 'Have an account?';
  if (switchLink) switchLink.textContent = signin ? 'Create one' : 'Sign in';
  if (msg) msg.textContent = '';
}
async function submitAuth() {
  const emailEl = document.getElementById('auth-email');
  const pwEl = document.getElementById('auth-password');
  const msg = document.getElementById('auth-msg');
  if (!emailEl || !pwEl || !msg) return;
  const email = emailEl.value.trim();
  const pw = pwEl.value;
  msg.className = 'auth-msg'; msg.textContent = '…';
  if (!email || !pw) { msg.className = 'auth-msg error'; msg.textContent = 'Enter email and password.'; return; }
  try {
    if (authMode === 'signup') {
      const { error } = await supa.auth.signUp({ email, password: pw });
      if (error) throw error;
      msg.className = 'auth-msg ok'; msg.textContent = 'Account created! Check your email to confirm, then sign in.';
    } else {
      const { data, error } = await supa.auth.signInWithPassword({ email, password: pw });
      if (error) throw error;
      currentUser = data.user;
      await loadCloudFavs();
      await loadWatchlistData(); await loadNotifs();
      updateAuthUI();
      renderWatchlists();
      closeAuth();
      showToast('Signed in');
      await handleJoinLink();   // if they arrived via an invite link, join now
    }
  } catch (err) {
    msg.className = 'auth-msg error'; msg.textContent = err.message || 'Authentication failed.';
  }
}
async function signInGoogle() {
  if (!supa) { showToast('Login not configured'); return; }
  await supa.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: location.origin + location.pathname }
  });
}

async function signOut() {
  if (supa) await supa.auth.signOut();
  currentUser = null;
  WATCHLISTS = []; NOTIFS = []; FAVS = new Set(); SWIPES = {};   // clear all personal data from memory
  updateFavCount();
  updateAuthUI();
  renderWatchlists();
  updateNotifBadge();
  if (favView && typeof setSection === 'function') setSection('search');   // leave the (now empty) favorites view
  if (typeof filter === 'function') filter();                              // reset hearts on cards/map
  showToast('Signed out');
}

// ── WATCHLISTS + NOTIFICATIONS ────────────────────────────────────────────────
function listingById(id) { return ALL.find(l => l.id === id); }

async function loadWatchlistData() {
  if (!supa || !currentUser) { WATCHLISTS = []; return; }
  try {
    await acceptPendingInvites();
    const { data: wls } = await supa.from('watchlists').select('*').order('created_at');
    const ids = (wls || []).map(w => w.id);
    let items = [], members = [];
    if (ids.length) {
      const it = await supa.from('watchlist_items').select('*').in('watchlist_id', ids);
      const mb = await supa.from('watchlist_members').select('watchlist_id,user_id,role').in('watchlist_id', ids);
      items = it.data || []; members = mb.data || [];
    }
    WATCHLISTS = (wls || []).map(w => ({
      ...w,
      isOwner: w.owner_id === currentUser.id,
      items: items.filter(i => i.watchlist_id === w.id).map(i => i.listing_id),
      memberCount: members.filter(m => m.watchlist_id === w.id).length || 1,
    }));
  } catch (e) { console.warn('watchlist load', e); WATCHLISTS = []; }
}

async function acceptPendingInvites() {
  try {
    const email = currentUser.email;
    const { data: invites } = await supa.from('watchlist_invites').select('*').eq('email', email);
    for (const inv of (invites || [])) {
      await supa.from('watchlist_members').insert({ watchlist_id: inv.watchlist_id, user_id: currentUser.id, role: 'member' });
      await supa.from('watchlist_invites').delete().eq('id', inv.id);
    }
  } catch { /* ignore */ }
}

async function createWatchlist(name) {
  if (!(await requireLogin())) return;
  const { data, error } = await supa.from('watchlists').insert({ owner_id: currentUser.id, name: name || 'My Watchlist' }).select().single();
  if (error) { showToast('Could not create list'); return; }
  await supa.from('watchlist_members').insert({ watchlist_id: data.id, user_id: currentUser.id, role: 'owner' });
  await loadWatchlistData(); renderWatchlists();
}

async function deleteWatchlist(id) {
  await supa.from('watchlists').delete().eq('id', id);
  await loadWatchlistData(); renderWatchlists();
}

async function addToWatchlist(wlId, listingId) {
  await supa.from('watchlist_items').upsert({ watchlist_id: wlId, listing_id: listingId, added_by: currentUser.id });
  await loadWatchlistData();
}
async function removeFromWatchlist(wlId, listingId) {
  await supa.from('watchlist_items').delete().eq('watchlist_id', wlId).eq('listing_id', listingId);
  await loadWatchlistData(); renderWatchlists();
}

function copyInviteLink(wlId) {
  const w = WATCHLISTS.find(x => x.id === wlId);
  if (!w || !w.join_token) { showToast('Invite link unavailable — run the latest SQL'); return; }
  const link = location.origin + location.pathname + '?join=' + w.join_token;
  (navigator.clipboard ? navigator.clipboard.writeText(link) : Promise.reject())
    .then(() => showToast('Invite link copied — send it to a friend!'))
    .catch(() => prompt('Copy this invite link:', link));
}

// Join a shared watchlist from an ?join=<token> link
async function handleJoinLink() {
  const token = new URLSearchParams(location.search).get('join');
  if (!token) return;
  if (!currentUser) { openAuth(); showToast('Sign in to join the shared watchlist'); return; }
  try {
    await supa.rpc('join_watchlist', { token });
    await loadWatchlistData(); renderWatchlists();
    showToast('Joined the shared watchlist!');
    history.replaceState({}, '', location.pathname);   // clear the token from the URL
  } catch { showToast('Invite link invalid or expired'); }
}

async function requireLogin() {
  if (!(await ensureUser())) { openAuth(); showToast('Sign in to use watchlists'); return false; }
  return true;
}

// ── render watchlists section ──
function renderWatchlists() {
  const el = document.getElementById('watch-view');
  if (!el) return;
  if (!currentUser) {
    el.innerHTML = `<div class="watch-empty"><div class="empty-jp" style="font-size:48px">観</div>
      <p style="margin:12px 0">Sign in to create watchlists, share them with friends, and get notified on price changes & sales.</p>
      <button class="auth-submit" style="max-width:200px;margin:0 auto" onclick="openAuth()">Sign in</button></div>`;
    return;
  }
  let html = `<div class="watch-create">
      <input id="new-wl-name" placeholder="New watchlist name…" onkeydown="if(event.key==='Enter')createWatchlist(this.value)">
      <button class="hbtn active" onclick="createWatchlist(document.getElementById('new-wl-name').value)">+ Create watchlist</button>
    </div>`;
  if (!WATCHLISTS.length) {
    html += `<div class="watch-empty">No watchlists yet. Create one above, then add houses with the "👁 Watch" button on any listing.</div>`;
  }
  for (const w of WATCHLISTS) {
    const cards = w.items.map(id => { const l = listingById(id); return l ? wlCardHTML(w.id, l) : ''; }).join('');
    html += `<div class="wl-card">
      <div class="wl-head">
        <span class="wl-name">${w.name}</span>
        <span class="wl-meta">${w.items.length} houses · ${w.memberCount} member${w.memberCount>1?'s':''} ${w.isOwner?'· owner':'· shared'}</span>
        <div class="wl-actions">
          <button class="hbtn" onclick="copyInviteLink('${w.id}')">🔗 Copy invite link</button>
          ${w.isOwner ? `<button class="hbtn" onclick="if(confirm('Delete this watchlist?'))deleteWatchlist('${w.id}')">Delete</button>` : ''}
        </div>
      </div>
      ${w.items.length ? `<div class="wl-grid">${cards}</div>` : `<div class="watch-empty" style="padding:20px">No houses yet — open a listing and tap "👁 Watch".</div>`}
    </div>`;
  }
  el.innerHTML = html;
}

function wlCardHTML(wlId, l) {
  const img = l.image_url ? `<img src="${l.image_url}" style="width:100%;height:120px;object-fit:cover;border-radius:6px" onerror="this.style.display='none'">` : '';
  return `<div style="background:var(--surface3);border:1px solid var(--border);border-radius:8px;padding:10px;cursor:pointer" onclick="openDetail('${l.id}')">
    ${img}
    <div style="font-size:10px;color:var(--accent);font-family:var(--mono);margin-top:6px">${prefToEN(l.prefecture)}${l.city?' · '+l.city:''}</div>
    <div style="font-size:13px;font-weight:600;margin:3px 0;line-height:1.3">${(l.title_en||l.title||'').slice(0,60)}</div>
    <div style="font-family:var(--mono);color:var(--accent2);font-size:14px">${l.price_jpy?fmtYen(l.price_jpy):'要問合せ'}${l.price_jpy&&userCurrency!=='JPY'?` · ${convPrice(l.price_jpy)}`:''}</div>
    <button class="hbtn" style="margin-top:8px;width:100%" onclick="event.stopPropagation();removeFromWatchlist('${wlId}','${l.id}')">Remove</button>
  </div>`;
}

// ── add-to-watchlist menu ──
async function openAddToWatchlist(listingId, anchor) {
  if (!(await requireLogin())) return;
  document.querySelector('.atw-menu')?.remove();
  const menu = document.createElement('div');
  menu.className = 'atw-menu';
  const rows = WATCHLISTS.map(w => {
    const inIt = w.items.includes(listingId);
    return `<div class="atw-item ${inIt?'checked':''}" onclick="atwToggle('${w.id}','${listingId}',this)">${inIt?'☑':'☐'} ${w.name}</div>`;
  }).join('') || '<div style="padding:8px;color:var(--text3);font-size:12px">No watchlists yet</div>';
  menu.innerHTML = rows + `<div class="atw-item atw-new" onclick="atwCreate('${listingId}')">＋ New watchlist…</div>`;
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.top = (r.bottom + 6) + 'px';
  menu.style.left = Math.min(r.left, window.innerWidth - 240) + 'px';
  setTimeout(() => document.addEventListener('click', _atwClose), 0);
}
function _atwClose(e) {
  // Close only on a click OUTSIDE the menu; keep listening while interacting inside.
  if (!e.target.closest('.atw-menu')) {
    document.querySelector('.atw-menu')?.remove();
    document.removeEventListener('click', _atwClose);
  }
}
async function atwToggle(wlId, listingId, el) {
  const w = WATCHLISTS.find(x => x.id === wlId);
  const inIt = w.items.includes(listingId);
  if (inIt) await removeFromWatchlist(wlId, listingId); else await addToWatchlist(wlId, listingId);
  el.classList.toggle('checked'); el.textContent = (inIt?'☐':'☑') + ' ' + w.name;
  showToast(inIt ? 'Removed from ' + w.name : 'Added to ' + w.name);
}
async function atwCreate(listingId) {
  const name = prompt('New watchlist name:'); if (!name) return;
  await createWatchlist(name);
  const w = WATCHLISTS[WATCHLISTS.length - 1];
  if (w) await atwAdd(w.id, listingId);
  document.querySelector('.atw-menu')?.remove();
}
async function atwAdd(wlId, listingId) { await addToWatchlist(wlId, listingId); showToast('Added'); }

// ── notifications ──
async function loadNotifs() {
  if (!supa || !currentUser) { NOTIFS = []; updateNotifBadge(); return; }
  try {
    const { data: st } = await supa.from('user_state').select('notifications_seen_at').eq('user_id', currentUser.id).maybeSingle();
    notifSeenAt = st ? st.notifications_seen_at : '1970-01-01';
    const watched = [...new Set(WATCHLISTS.flatMap(w => w.items))];
    if (!watched.length) { NOTIFS = []; updateNotifBadge(); return; }
    const { data } = await supa.from('listing_changes').select('*').in('listing_id', watched).order('created_at', { ascending: false }).limit(50);
    NOTIFS = data || [];
    updateNotifBadge();
  } catch { NOTIFS = []; updateNotifBadge(); }
}
function unreadCount() { return NOTIFS.filter(n => !notifSeenAt || n.created_at > notifSeenAt).length; }
function updateNotifBadge() {
  const b = document.getElementById('notif-badge'); if (!b) return;
  const n = unreadCount();
  b.textContent = n; b.style.display = n > 0 ? 'flex' : 'none';
}
function toggleNotifs() {
  const p = document.getElementById('notif-panel');
  if (!p) return;
  const opening = !p.classList.contains('open');
  p.classList.toggle('open', opening);
  if (opening) renderNotifs();
}
function renderNotifs() {
  const el = document.getElementById('notif-list');
  if (!el) return;
  if (!currentUser) { el.innerHTML = `<div class="notif-empty">Sign in to get price & sale alerts on your watchlists.</div>`; return; }
  if (!NOTIFS.length) { el.innerHTML = `<div class="notif-empty">No alerts yet. Add houses to a watchlist — you'll be notified here on price changes or when one sells.</div>`; return; }
  el.innerHTML = NOTIFS.map(n => {
    const l = listingById(n.listing_id);
    const img = l && l.image_url ? `<img src="${l.image_url}" onerror="this.style.display='none'">` : '';
    const title = l ? (l.title_en || l.title) : 'A watched house';
    let msg;
    if (n.type === 'sold') msg = `🏠 <b>Sold / delisted</b>`;
    else if (n.type === 'price_drop') msg = `📉 <b>Price drop</b> ${fmtYen(n.old_price)} → ${fmtYen(n.new_price)}`;
    else msg = `📈 <b>Price rise</b> ${fmtYen(n.old_price)} → ${fmtYen(n.new_price)}`;
    const unread = !notifSeenAt || n.created_at > notifSeenAt;
    return `<div class="notif-item" style="${unread?'background:rgba(232,160,32,.06)':''}" onclick="${l?`openDetail('${n.listing_id}');toggleNotifs()`:''}">
      ${img}
      <div><div class="notif-txt">${msg}<br>${(title||'').slice(0,50)}</div>
      <div class="notif-when">${new Date(n.created_at).toLocaleDateString()}</div></div>
    </div>`;
  }).join('');
}
async function markNotifsSeen() {
  if (!supa || !currentUser) return;
  const now = new Date().toISOString();
  await supa.from('user_state').upsert({ user_id: currentUser.id, notifications_seen_at: now });
  notifSeenAt = now; updateNotifBadge(); renderNotifs();
}

// ── AIRBNB SCORE CALCULATOR ──────────────────────────────────────────────────
function calcAirbnb(l) {
  let score = 50;
  const text = ((l.title||'')+(l.description||'')+(l.tags||[]).join(' ')).toLowerCase();

  const tourism = AIRBNB_TOURISM[l.prefecture] || 45;
  score = score * 0.3 + tourism * 0.7;

  if (/海|ocean|beach|sea|coast|coastal/.test(text)) score += 12;
  if (/富士|fuji|mountain|ski|スキー|onsen|温泉/.test(text)) score += 10;
  if (/古民家|kominka|traditional|町家|machiya/.test(text)) score += 8;
  if (/リノベ|renovated|renovatio|良好/.test(text)) score += 9;
  if (/seaview|oceanview|ocean view|景色|view/.test(text)) score += 7;
  if (/大規模修繕|major repair|大規模|collapsed/.test(text)) score -= 18;
  if (/要リフォーム|needs renovation/.test(text)) score -= 5;

  if (l.size_m2 >= 100) score += 8;
  if (l.size_m2 >= 150) score += 5;
  if (l.rooms) { const rm = parseInt(l.rooms); if (rm >= 4) score += 6; if (rm >= 6) score += 4; }

  if (l.price_jpy !== null && l.price_jpy !== undefined) {
    if (l.price_jpy === 0) score += 15;
    else if (l.price_jpy < 1000000) score += 12;
    else if (l.price_jpy < 3000000) score += 7;
    else if (l.price_jpy < 8000000) score += 2;
    else score -= 3;
  }

  if (l.built_year && l.built_year < 1960) score -= 5;
  if (l.built_year && l.built_year > 1990) score += 4;

  return Math.min(99, Math.max(5, Math.round(score)));
}

function airbnbColor(s) {
  if (s >= 75) return 'var(--green)';
  if (s >= 55) return 'var(--accent)';
  if (s >= 35) return 'var(--blue)';
  return 'var(--text3)';
}

function airbnbVerdict(s, l) {
  const text = ((l.title||'')+(l.description||'')+(l.tags||[]).join(' ')).toLowerCase();
  const tourism = AIRBNB_TOURISM[l.prefecture] || 45;
  let pros = [], cons = [];

  if (tourism >= 75) pros.push('High tourist demand in this region');
  else if (tourism >= 55) pros.push('Moderate tourist traffic');
  else cons.push('Lower tourist volume in this area');

  if (/海|ocean|beach|sea/.test(text)) pros.push('Coastal/ocean proximity');
  if (/温泉|onsen/.test(text)) pros.push('Hot spring access nearby');
  if (/スキー|ski/.test(text)) pros.push('Ski resort access');
  if (/富士|fuji/.test(text)) pros.push('Mt. Fuji views attract visitors');
  if (/古民家|kominka/.test(text)) pros.push('Traditional architecture — unique stay');
  if (/リノベ|renovated/.test(text)) pros.push('Already renovated — lower setup cost');
  if (l.size_m2 >= 100) pros.push(`Large floor area (${l.size_m2}m²) fits groups`);

  if (/大規模修繕/.test(text)) cons.push('Major renovation needed before listing');
  if (/要リフォーム/.test(text)) cons.push('Renovation required — adds upfront cost');
  if (l.built_year && l.built_year < 1960) cons.push(`Very old structure (${l.built_year}) — compliance risk`);
  if (tourism < 50) cons.push('Region has limited Airbnb demand data');
  if (!l.size_m2 || l.size_m2 < 60) cons.push('Small floor area limits group bookings');

  const baseRate = { EUR: 45 };
  const tourismMult = tourism / 60;
  const sizeMult = l.size_m2 ? Math.min(2, l.size_m2 / 80) : 1;
  const nightlyEUR = Math.round(baseRate.EUR * tourismMult * sizeMult);

  // ── Minpaku (民泊) legal allowance ──────────────────────────────────────────
  // A standard private-lodging registration (住宅宿泊事業) is capped at 180
  // nights/year nationwide. Special zones (特区民泊) or a hotel/ryokan licence
  // (旅館業法) can exceed it. We cap the income estimate at the legal allowance.
  const SPECIAL_ZONES = ['大阪', '東京', '新潟', '千葉', '福岡'];
  const specialZone = SPECIAL_ZONES.includes(l.prefecture);
  const legalCapNights = 180;
  const demandNights = Math.round(120 * (tourism / 60));      // demand-based estimate
  const annualNights = Math.min(legalCapNights, demandNights); // capped by minpaku law
  const monthlyEUR = Math.round(nightlyEUR * annualNights / 12);
  const annualEUR = nightlyEUR * annualNights;
  const priceEUR = l.price_jpy ? Math.round(l.price_jpy * FX.EUR) : null;
  const roiYears = priceEUR && annualEUR ? Math.round(priceEUR / annualEUR) : null;

  const minpakuNote = specialZone
    ? 'In a special minpaku zone (特区民泊): with a licence you can operate beyond the 180-night/yr cap.'
    : 'Standard minpaku is capped at 180 nights/yr — exceeding it needs a hotel/ryokan licence (旅館業法). Always verify the local ordinance & register (届出).';

  if (annualNights >= legalCapNights)
    cons.push('Income limited by the 180-night/yr minpaku cap');

  return { pros: pros.slice(0,4), cons: cons.slice(0,4),
           nightlyEUR, monthlyEUR, roiYears, annualNights, specialZone, minpakuNote };
}

// ── FX RATES ─────────────────────────────────────────────────────────────────
async function fetchFXRates() {
  try {
    const r = await fetch('https://api.exchangerate-api.com/v4/latest/JPY');
    if (!r.ok) throw new Error();
    const d = await r.json();
    FX.EUR = d.rates.EUR; FX.USD = d.rates.USD;
    FX.GBP = d.rates.GBP; FX.AUD = d.rates.AUD;
    const rateNote = document.getElementById('yen-rate-note');
    if (rateNote) rateNote.textContent =
      `Live rates · 1¥ = €${FX.EUR.toFixed(4)} · $${FX.USD.toFixed(4)}`;
  } catch { /* use fallback */ }
}

// ── DATA LOADING ──────────────────────────────────────────────────────────────
async function loadListings() {
  setLoading(true);
  // Try the live Flask API first (local dev); fall back to the static snapshot
  // (Cloudflare Pages); finally fall back to bundled demo data.
  for (const src of ['/api/listings', './listings.json']) {
    try {
      const r = await fetch(src);
      if (!r.ok) continue;
      const d = await r.json();
      // Drop the legacy "AKIYA BANK" source — it scraped portal nav links, not houses
      ALL = (d.listings || []).filter(l => l.source !== 'AKIYA BANK');
      // A sub-¥10,000 price is a parse artifact (e.g. ¥200) → show "price on request"
      ALL.forEach(l => { if (l.price_jpy != null && l.price_jpy > 0 && l.price_jpy < 10000) l.price_jpy = null; });
      if (typeof populateSources === 'function') populateSources();
      setLoading(false);
      if (typeof onDataLoaded === 'function') onDataLoaded();
      else if (typeof filter === 'function') filter();
      if (typeof openDeepLink === 'function') openDeepLink();
      return;
    } catch { /* try next source */ }
  }
  ALL = DEMO_DATA;
  showToast('⚠ No data source — showing demo data');
  setLoading(false);
  if (typeof onDataLoaded === 'function') onDataLoaded();
  else if (typeof filter === 'function') filter();
  if (typeof openDeepLink === 'function') openDeepLink();
}

async function refreshData() {
  setLoading(true);
  try {
    await fetch('/api/refresh', { method: 'POST' });
    showToast('🔄 Scraping started… reloading in 5s');
    setTimeout(loadListings, 5000);
  } catch { showToast('⚠ Could not reach server'); setLoading(false); }
}

// ── FORMATTERS ────────────────────────────────────────────────────────────────
function fmtYen(jpy) {
  if (jpy >= 100_000_000) return `¥${(jpy / 100_000_000).toLocaleString('de-DE', {maximumFractionDigits:1})} Mrd.`;
  if (jpy >= 10_000_000)  return `¥${(jpy / 1_000_000).toLocaleString('de-DE', {maximumFractionDigits:1})} Mio.`;
  if (jpy >= 1_000_000)   return `¥${(jpy / 1_000_000).toLocaleString('de-DE', {maximumFractionDigits:2})} Mio.`;
  return `¥${jpy.toLocaleString('de-DE')}`;
}

function fmtJPY(jpy) {
  if (jpy === 0) return '<span class="lcard-price-free">FREE / 無償</span>';
  if (jpy == null) return '<span style="font-family:var(--mono);font-size:12px;color:var(--text3)">Price on request</span>';
  const conv = userCurrency === 'JPY' ? '' : `<span class="lcard-price-eur">≈ ${convPrice(jpy)}</span>`;
  return `<span class="lcard-price-jpy">${fmtYen(jpy)}</span>${conv}`;
}

// ── CARD HTML ─────────────────────────────────────────────────────────────────
function cardHTML(l) {
  const ab = calcAirbnb(l);
  const abColor = airbnbColor(ab);
  const badgeFree = l.price_jpy === 0 ? '<span class="badge badge-free">FREE</span>' : '';
  const badgeCheap = (l.price_jpy > 0 && l.price_jpy < 2000000) ? '<span class="badge badge-cheap">CHEAP</span>' : '';
  const badgeAB = ab >= 75 ? '<span class="badge badge-airbnb-hot">AIRBNB ★</span>' : ab >= 60 ? '<span class="badge badge-airbnb-ok">AIRBNB</span>' : '';

  const img = l.image_url
    ? `<img src="${l.image_url}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
    : '';
  const placeholder = `<div class="lcard-img-placeholder" ${l.image_url ? 'style="display:none"' : ''}>家</div>`;

  const seis = seismicInfo(l.built_year);
  const specs = [
    l.size_m2 ? `<span class="spec-pill"><span class="si">⬜</span>${l.size_m2}m²</span>` : '',
    l.land_m2 ? `<span class="spec-pill"><span class="si">🌿</span>${l.land_m2}m² land</span>` : '',
    l.rooms   ? `<span class="spec-pill"><span class="si">🚪</span>${l.rooms}</span>` : '',
    l.built_year ? `<span class="spec-pill"><span class="si">📅</span>${l.built_year}</span>` : '',
    l.built_year ? `<span class="spec-pill" style="border-color:${seis.color};color:${seis.color}"><span class="si">🛡</span>${seis.risk} seismic</span>` : '',
    l.condition ? `<span class="spec-pill">${conditionEN(l.condition)}</span>` : '',
  ].filter(Boolean).join('');

  const tags = (l.tags||[]).slice(0,3).map(t=>`<span class="ltag">${t}</span>`).join('');
  const prefEN = prefToEN(l.prefecture);

  return `
  <a class="lcard ${selectedId===l.id?'selected':''}" href="listing.html?id=${encodeURIComponent(l.id)}" onclick="return cardClick(event,'${l.id}')">
    <div class="lcard-img-wrap">
      ${img}${placeholder}
      <div class="lcard-badges">${badgeFree}${badgeCheap}${badgeAB}</div>
      <button class="fav-btn ${isFav(l.id)?'on':''}" onclick="event.stopPropagation();event.preventDefault();toggleFav('${l.id}',this)" title="Save to favorites">${isFav(l.id)?'♥':'♡'}</button>
    </div>
    <div class="lcard-body">
      <div class="lcard-location">${prefEN}${l.city ? ' · '+l.city : ''}</div>
      <div class="lcard-title">${l.title_en || l.title}</div>
      ${l.title_en ? `<div style="font-size:10px;color:var(--text3);font-family:var(--jp);margin-bottom:4px">${l.title}</div>` : ''}
      <div class="lcard-price-row">${fmtJPY(l.price_jpy)}</div>
      <div class="lcard-specs">${specs}</div>
      <div class="airbnb-bar">
        <span class="airbnb-label">AIRBNB</span>
        <div class="airbnb-track"><div class="airbnb-fill" style="width:${ab}%;background:${abColor}"></div></div>
        <span class="airbnb-score-val" style="color:${abColor}">${ab}/99</span>
      </div>
    </div>
    <div class="lcard-footer">
      <div class="lcard-tags">${tags}</div>
      <span class="lcard-link" onclick="event.stopPropagation();event.preventDefault();window.open('${l.source_url}','_blank')">Source →</span>
    </div>
  </a>`;
}

// ── SEISMIC STANDARD & RISK (derived from build year + condition) ─────────────
function seismicInfo(year) {
  if (!year) return { era: 'Unknown', label: 'Build year unknown', color: 'var(--text3)', risk: 'Unknown', note: 'No construction year on record — verify the seismic standard before buying.' };
  if (year < 1981) return {
    era: '旧耐震 (Pre-1981)', label: 'Old seismic standard', color: 'var(--red)', risk: 'High',
    note: 'Built before the 1981 earthquake code. May need seismic retrofitting (耐震補強); can be harder to insure/finance.'
  };
  if (year < 2000) return {
    era: '新耐震 (1981–2000)', label: 'New seismic standard (1981)', color: 'var(--accent)', risk: 'Moderate',
    note: 'Meets the 1981 earthquake code. Generally sound, but pre-2000 wood joints are weaker than the latest standard.'
  };
  return {
    era: '2000年基準 (2000+)', label: 'Current seismic standard', color: 'var(--green)', risk: 'Low',
    note: 'Built to the strengthened post-2000 code — the strongest standard for wooden houses.'
  };
}

function riskLevel(l) {
  // Combine seismic era, age and stated condition into one verdict.
  const yr = l.built_year;
  const s = seismicInfo(yr);
  let score = { 'Low': 1, 'Moderate': 2, 'High': 3, 'Unknown': 2 }[s.risk];
  const cond = (l.condition || '') + (l.description || '');
  if (/大規模修繕|要大規模/.test(cond)) score += 1;
  if (yr && (new Date().getFullYear() - yr) > 50) score += 1;
  if (score >= 4) return { label: 'High Risk', color: 'var(--red)' };
  if (score >= 3) return { label: 'Elevated', color: 'var(--accent)' };
  if (score === 2) return { label: 'Moderate', color: 'var(--blue)' };
  return { label: 'Low Risk', color: 'var(--green)' };
}

// Card is an <a href="listing.html?id=ID">. Middle-click / ctrl-click → browser opens a new
// tab natively. Plain left-click → open the in-app modal (no navigation).
function cardClick(e, id) {
  if (e.ctrlKey || e.metaKey || e.shiftKey) return true;  // let the browser open a new tab/window
  e.preventDefault();
  openDetail(id);
  return false;
}
function openDeepLink() {
  const id = new URLSearchParams(location.search).get('l');
  if (id && listingById(id)) openDetail(id);
}

// ── DETAIL PANEL ──────────────────────────────────────────────────────────────
function openDetail(id) {
  const l = FILTERED.find(x => x.id === id) || ALL.find(x => x.id === id);
  if (!l) return;
  selectedId = id;
  document.querySelectorAll('.lcard').forEach(c => c.classList.toggle('selected', c.onclick?.toString().includes(`'${id}'`)));

  const ab = calcAirbnb(l);
  const abColor = airbnbColor(ab);
  const { pros, cons, nightlyEUR, monthlyEUR, roiYears, annualNights, specialZone, minpakuNote } = airbnbVerdict(ab, l);
  const prefEN = prefToEN(l.prefecture);

  let priceBlock = '';
  if (l.price_jpy === 0) {
    priceBlock = `<div class="dp-price-row"><span class="dp-price-free">FREE — 無償譲渡</span></div><div class="dp-price-note">Property transferred at no cost</div>`;
  } else if (l.price_jpy) {
    const convNote = userCurrency === 'JPY' ? '' : `<span class="dp-price-eur">≈ ${convPrice(l.price_jpy)}</span>`;
    priceBlock = `
      <div class="dp-price-row">
        <span class="dp-price-jpy">${fmtYen(l.price_jpy)}</span>
        ${convNote}
      </div>
      <div class="dp-price-note">¥${l.price_jpy.toLocaleString('de-DE')}${userCurrency!=='JPY' ? ` · 1¥ = ${CUR_SYMBOL[userCurrency]}${FX[userCurrency].toFixed(4)}` : ''}</div>`;
  } else {
    priceBlock = `<div style="font-family:var(--mono);font-size:13px;color:var(--text3)">Price on request — 要問合せ</div>`;
  }

  const specs = [
    ['Floor Area', l.size_m2 ? l.size_m2+'m²' : '—'],
    ['Land Area', l.land_m2 ? l.land_m2+'m²' : '—'],
    ['Layout', l.rooms || '—'],
    ['Built', l.built_year ? l.built_year + ' (' + (new Date().getFullYear()-l.built_year) + ' yrs)' : '—'],
    ['Condition', conditionEN(l.condition) || '—'],
    ['Prefecture', prefEN || '—'],
  ].map(([label,val]) => `<div class="dp-spec"><div class="dp-spec-label">${label}</div><div class="dp-spec-val">${val}</div></div>`).join('');

  let calcSection = '';
  if (l.price_jpy != null && l.price_jpy > 0) {
    const yen = l.price_jpy;
    const eur = Math.round(yen * FX.EUR);
    const usd = Math.round(yen * FX.USD);
    const gbp = Math.round(yen * FX.GBP);
    const reno_low = Math.round(3000000 * FX.EUR);
    const reno_high = Math.round(8000000 * FX.EUR);
    calcSection = `
      <div class="yen-calc">
        <div class="yen-calc-title">¥ PRICE CONVERTER</div>
        <div class="yen-calc-row">
          <span class="yen-calc-label">¥ JPY</span>
          <input class="yen-calc-input" type="number" id="calc-input-${l.id}" value="${yen}" oninput="updateInlineCalc('${l.id}')">
        </div>
        <div class="yen-calc-result" id="calc-result-${l.id}">
          <div class="yen-calc-result-row"><span class="yen-calc-result-label">EUR €</span><span class="yen-calc-result-val">€${eur.toLocaleString('de-DE')}</span></div>
          <div class="yen-calc-result-row"><span class="yen-calc-result-label">USD $</span><span class="yen-calc-result-val">$${usd.toLocaleString()}</span></div>
          <div class="yen-calc-result-row"><span class="yen-calc-result-label">GBP £</span><span class="yen-calc-result-val">£${gbp.toLocaleString()}</span></div>
        </div>
        <div class="yen-calc-note">+ Renovation budget: ~€${reno_low.toLocaleString()}–€${reno_high.toLocaleString()} typical for akiya</div>
      </div>`;
  }

  const prosHTML = pros.map(p=>`<div class="airbnb-point">${p}</div>`).join('');
  const consHTML = cons.map(c=>`<div class="airbnb-point">${c}</div>`).join('');
  let roiText = roiYears ? `~${roiYears} years to break even` : 'N/A (free property)';
  if (l.price_jpy === 0) roiText = 'Immediate ROI potential — no purchase cost';

  // Build image list: use l.images if available, fall back to single image_url
  const allImgs = (l.images && l.images.length) ? l.images : (l.image_url ? [l.image_url] : []);
  // Store on a global so onclick handlers reference by index (avoids quote-escaping bugs)
  _detailImgs = allImgs;

  let galleryHTML = '';
  if (allImgs.length === 0) {
    galleryHTML = `<div class="dp-img-placeholder">家</div>`;
  } else if (allImgs.length === 1) {
    galleryHTML = `<img class="dp-img" src="${bigImg(allImgs[0])}" style="cursor:zoom-in" onclick="openDetailLightbox(0)" onerror="this.style.display='none'">`;
  } else {
    const thumbs = allImgs.slice(1, 6).map((u, i) =>
      `<img class="dp-gallery-img" src="${u}" onclick="openDetailLightbox(${i+1})" onerror="this.parentElement.removeChild(this)">`
    ).join('');
    galleryHTML = `
      <div class="dp-gallery">
        <img class="dp-gallery-img dp-gallery-main" src="${bigImg(allImgs[0])}" onclick="openDetailLightbox(0)" onerror="this.style.display='none'">
        ${thumbs}
        ${allImgs.length > 6 ? `<div style="grid-column:span 3;text-align:center;padding:6px;font-size:10px;color:var(--text3);font-family:var(--mono);cursor:pointer" onclick="openDetailLightbox(0)">+${allImgs.length-6} more photos →</div>` : ''}
      </div>`;
  }

  const dpContent = document.getElementById('dp-content');
  if (dpContent) dpContent.innerHTML = `
    ${galleryHTML}
    <div class="dp-body">
      <div class="dp-location">${prefEN}${l.city ? ' · '+l.city : ''} · ${l.source||''}</div>
      <a href="${gmapsUrl(l)}" target="_blank" style="display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--blue);text-decoration:none;margin-bottom:8px">📍 Open address in Google Maps</a>
      <div class="dp-title">${l.title_en || l.title}</div>
      ${l.title_en ? `<div style="font-family:var(--jp);font-size:12px;color:var(--text3);margin-bottom:12px">${l.title}</div>` : ''}
      <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="dp-fav-btn ${isFav(l.id)?'on':''}" onclick="toggleFav('${l.id}',this)">${isFav(l.id)?'♥ Saved':'♡ Save to favorites'}</button>
        <button class="dp-fav-btn" onclick="openAddToWatchlist('${l.id}', this)">👁 Watch</button>
      </div>
      <div class="dp-price-block">${priceBlock}</div>
      <div class="dp-specs-grid">${specs}</div>

      <div class="dp-section-title">BUILDING STANDARD & RISK</div>
      ${(() => {
        const s = seismicInfo(l.built_year);
        const rk = riskLevel(l);
        const age = l.built_year ? (new Date().getFullYear() - l.built_year) + ' years old' : 'Age unknown';
        return `
        <div class="airbnb-card">
          <div style="display:flex;gap:10px;margin-bottom:12px">
            <div style="flex:1;background:var(--surface3);border-radius:4px;padding:10px">
              <div class="dp-spec-label">SEISMIC STANDARD</div>
              <div style="font-size:13px;font-weight:700;color:${s.color}">${s.label}</div>
              <div style="font-family:var(--jp);font-size:11px;color:var(--text3)">${s.era}</div>
            </div>
            <div style="flex:1;background:var(--surface3);border-radius:4px;padding:10px">
              <div class="dp-spec-label">OVERALL RISK</div>
              <div style="font-size:13px;font-weight:700;color:${rk.color}">${rk.label}</div>
              <div style="font-size:11px;color:var(--text3)">${age}</div>
            </div>
          </div>
          <div style="font-size:11px;color:var(--text2);line-height:1.6">${s.note}</div>
          ${l.condition ? `<div style="margin-top:8px;font-size:11px;color:var(--text3)">Condition: <span style="color:var(--text2)">${conditionEN(l.condition)}</span></div>` : ''}
        </div>`;
      })()}

      ${(l.description || l.description_en) ? `
        <div class="dp-section-title">DESCRIPTION</div>
        ${l.description_en ? `<div class="dp-desc">${l.description_en}</div>` : ''}
        ${l.description && l.description_en ? `<div style="font-family:var(--jp);font-size:11px;color:var(--text3);line-height:1.7;margin-bottom:16px">${l.description}</div>` : `<div class="dp-desc">${l.description}</div>`}
      ` : ''}
      ${calcSection}
      <div class="dp-section-title">AIRBNB POTENTIAL ANALYSIS</div>
      <div class="airbnb-card">
        <div class="airbnb-score-big">
          <div class="airbnb-score-circle" style="border-color:${abColor}">
            <span class="airbnb-score-num" style="color:${abColor}">${ab}</span>
            <span class="airbnb-score-label" style="color:${abColor}">/99</span>
          </div>
          <div class="airbnb-verdict">
            <div class="airbnb-verdict-title" style="color:${abColor}">
              ${ab>=75?'Strong Airbnb Candidate':ab>=60?'Good Potential':ab>=45?'Moderate Potential':'Limited Airbnb Appeal'}
            </div>
            <div class="airbnb-verdict-sub">${ab>=75?'High tourist demand + favorable property characteristics.':ab>=60?'Solid location with good rental potential.':ab>=45?'Viable with the right renovations and marketing.':'Better suited for personal use or long-term rental.'}</div>
          </div>
        </div>
        <div class="airbnb-metrics">
          <div class="airbnb-metric"><div class="airbnb-metric-label">EST. NIGHTLY RATE</div><div class="airbnb-metric-val" style="color:var(--accent2)">€${nightlyEUR}–€${nightlyEUR+20}</div></div>
          <div class="airbnb-metric"><div class="airbnb-metric-label">EST. MONTHLY INCOME</div><div class="airbnb-metric-val" style="color:var(--accent2)">€${monthlyEUR}</div></div>
          <div class="airbnb-metric"><div class="airbnb-metric-label">MINPAKU NIGHTS/YR</div><div class="airbnb-metric-val" style="color:${specialZone?'var(--green)':'var(--accent)'}">${annualNights}${specialZone?'+':' max'}</div></div>
          <div class="airbnb-metric"><div class="airbnb-metric-label">BREAK-EVEN</div><div class="airbnb-metric-val" style="color:var(--text2);font-size:10px">${roiText}</div></div>
        </div>
        <div style="background:var(--surface3);border-left:3px solid ${specialZone?'var(--green)':'var(--accent)'};border-radius:4px;padding:10px 12px;margin-bottom:14px;font-size:12px;line-height:1.55;color:var(--text)">
          <strong style="color:${specialZone?'var(--green)':'var(--accent)'}">⚖ 民泊 Minpaku law:</strong> ${minpakuNote}
        </div>
        <div class="airbnb-pros-cons">
          <div class="airbnb-pros"><div class="airbnb-pros-title">✓ Pros</div>${prosHTML||'<div class="airbnb-point">Standard rental potential</div>'}</div>
          <div class="airbnb-cons"><div class="airbnb-cons-title">✕ Cons</div>${consHTML||'<div class="airbnb-point">No major issues identified</div>'}</div>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px">
        <a href="${l.source_url}" target="_blank" style="flex:1;display:block;padding:10px;background:var(--accent);color:#000;font-weight:700;font-size:12px;text-align:center;border-radius:var(--r);text-decoration:none;letter-spacing:.04em">→ VIEW SOURCE</a>
        <a href="https://www.airbnb.com/s/${encodeURIComponent((prefToEN(l.prefecture)||'Japan')+' Japan')}/homes" target="_blank" style="flex:1;display:block;padding:10px;background:var(--surface2);border:1px solid var(--border2);color:var(--text2);font-size:12px;text-align:center;border-radius:var(--r);text-decoration:none">🏠 Airbnb Comps</a>
      </div>
    </div>`;

  const dp = document.getElementById('detail-panel');
  const db = document.getElementById('detail-backdrop');
  if (dp) dp.classList.add('open');
  if (db) db.classList.add('open');

  // Guard map pan — map may not exist on all pages
  if (typeof map !== 'undefined' && map && l.lat && l.lng) {
    map.setView([l.lat, l.lng], 12);
    if (typeof markers !== 'undefined') {
      const mk = markers.find(m => m._akiyaId === l.id);
      if (mk) mk.openPopup();
    }
  }
}

function updateInlineCalc(id) {
  const inp = document.getElementById(`calc-input-${id}`);
  const res = document.getElementById(`calc-result-${id}`);
  if (!inp || !res) return;
  const yen = parseFloat(inp.value) || 0;
  const eur = Math.round(yen * FX.EUR);
  const usd = Math.round(yen * FX.USD);
  const gbp = Math.round(yen * FX.GBP);
  res.innerHTML = `
    <div class="yen-calc-result-row"><span class="yen-calc-result-label">EUR €</span><span class="yen-calc-result-val">€${eur.toLocaleString('de-DE')}</span></div>
    <div class="yen-calc-result-row"><span class="yen-calc-result-label">USD $</span><span class="yen-calc-result-val">$${usd.toLocaleString()}</span></div>
    <div class="yen-calc-result-row"><span class="yen-calc-result-label">GBP £</span><span class="yen-calc-result-val">£${gbp.toLocaleString()}</span></div>`;
}

function closeDetail() {
  const dp = document.getElementById('detail-panel');
  const db = document.getElementById('detail-backdrop');
  if (dp) dp.classList.remove('open');
  if (db) db.classList.remove('open');
  selectedId = null;
}

// ── MAP HELPERS ───────────────────────────────────────────────────────────────
// Stable small offset (~±1km) per listing so houses sharing one town centre
// don't pile on the exact same point — keeps pins readable.
function jitterCoord(id, lat, lng) {
  let h = 0;
  for (let i = 0; i < (id || '').length; i++) h = (Math.imul(h, 31) + id.charCodeAt(i)) | 0;
  const r1 = ((h & 0xffff) / 0xffff) - 0.5;
  const r2 = (((h >>> 16) & 0xffff) / 0xffff) - 0.5;
  return [lat + r1 * 0.02, lng + r2 * 0.026];   // ~±1.1km lat / ~±1.1km lng
}

// ── UI HELPERS ────────────────────────────────────────────────────────────────
function setLoading(v) {
  const el = document.getElementById('loading-strip');
  if (el) el.classList.toggle('on', v);
}

function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}

function toggleMobileNav() {
  const nav = document.getElementById('main-nav');
  if (nav) nav.classList.toggle('open');
}
function closeMobileNav() {
  const nav = document.getElementById('main-nav');
  if (nav) nav.classList.remove('open');
}

// ── YEN PANEL ─────────────────────────────────────────────────────────────────
function openYen() {
  const el = document.getElementById('yen-panel');
  if (el) el.classList.add('open');
}
function closeYen() {
  const el = document.getElementById('yen-panel');
  if (el) el.classList.remove('open');
}
function updateYenPanel() {
  const inp = document.getElementById('yen-global-input');
  const yen = inp ? (parseFloat(inp.value) || 0) : 0;
  const eurEl = document.getElementById('yr-eur');
  const usdEl = document.getElementById('yr-usd');
  const gbpEl = document.getElementById('yr-gbp');
  const audEl = document.getElementById('yr-aud');
  if (eurEl) eurEl.textContent = '€' + Math.round(yen * FX.EUR).toLocaleString('de-DE');
  if (usdEl) usdEl.textContent = '$' + Math.round(yen * FX.USD).toLocaleString();
  if (gbpEl) gbpEl.textContent = '£' + Math.round(yen * FX.GBP).toLocaleString();
  if (audEl) audEl.textContent = 'A$' + Math.round(yen * FX.AUD).toLocaleString();
}

// ── LIGHTBOX ─────────────────────────────────────────────────────────────────
// Open the lightbox for the currently-open detail panel's images at a given index
function openDetailLightbox(idx) {
  if (_detailImgs && _detailImgs.length) openLightbox(_detailImgs, idx);
}

// Rewrite SUUMO/homes resizeImage URLs to request a large version
function bigImg(url) {
  if (!url) return url;
  if (url.includes('resizeImage') || url.includes('w=') ) {
    return url.replace(/([?&])w=\d+/i, '$1w=1200').replace(/([?&])h=\d+/i, '$1h=900');
  }
  return url;
}

function openLightbox(imgs, idx) {
  _lbImgs = imgs; _lbIdx = idx;
  _lbRender();
  const lb = document.getElementById('lightbox');
  if (lb) lb.classList.add('open');
  document.addEventListener('keydown', _lbKey);
}

function closeLightbox() {
  const lb = document.getElementById('lightbox');
  if (lb) lb.classList.remove('open');
  document.removeEventListener('keydown', _lbKey);
}

function lbClickBg(e) {
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}

function lbNav(dir) {
  _lbIdx = (_lbIdx + dir + _lbImgs.length) % _lbImgs.length;
  _lbRender();
}

function _lbKey(e) {
  if (e.key === 'ArrowRight') lbNav(1);
  if (e.key === 'ArrowLeft')  lbNav(-1);
  if (e.key === 'Escape')     closeLightbox();
}

function _lbRender() {
  const lbImg = document.getElementById('lb-img');
  const lbCounter = document.getElementById('lb-counter');
  const thumbs = document.getElementById('lb-thumbs');
  if (lbImg) lbImg.src = bigImg(_lbImgs[_lbIdx]);
  if (lbCounter) lbCounter.textContent = `${_lbIdx + 1} / ${_lbImgs.length}`;
  if (thumbs) {
    thumbs.innerHTML = _lbImgs.map((url, i) =>
      `<img class="lightbox-thumb ${i===_lbIdx?'active':''}" src="${url}" onclick="event.stopPropagation();_lbIdx=${i};_lbRender()">`
    ).join('');
    // scroll active thumb into view
    const active = thumbs.querySelector('.active');
    if (active) active.scrollIntoView({ inline: 'center', behavior: 'smooth' });
  }
}

// ── LOOKUP HELPERS ────────────────────────────────────────────────────────────
function prefToEN(p) { return PREF_EN[p] || p || 'Japan'; }
function conditionEN(c) { return COND_EN[c] || c || ''; }

// ── DISCOVER — content-based recommender (like/dislike) ───────────────────────
const FEATS = ['price','size','land','age','airbnb','rooms','free','kominka','sea','onsen','renovated','farm','mountain','newish'];

function featurize(l) {
  const t = ((l.title_en||'')+(l.title||'')+(l.description||'')+(l.description_en||'')).toLowerCase();
  const year = l.built_year || 1980, price = (l.price_jpy == null ? 3000000 : l.price_jpy);
  return {
    price: Math.min(1, Math.log10(Math.max(price,1))/8),
    size: Math.min(1, (l.size_m2||80)/250),
    land: Math.min(1, (l.land_m2||150)/1000),
    age: Math.min(1, Math.max(0, 2025-year)/100),
    airbnb: calcAirbnb(l)/99,
    rooms: Math.min(1, (parseInt(l.rooms)||3)/8),
    free: l.price_jpy === 0 ? 1 : 0,
    kominka: /古民家|kominka|machiya|町家/.test(t) ? 1 : 0,
    sea: /海|ocean|beach|sea|coast/.test(t) ? 1 : 0,
    onsen: /温泉|onsen|hot spring/.test(t) ? 1 : 0,
    renovated: /リノベ|renovated|済み|新築/.test(t) ? 1 : 0,
    farm: /農地|farm|農業|garden|畑/.test(t) ? 1 : 0,
    mountain: /山|mountain|ski|スキー|富士|fuji/.test(t) ? 1 : 0,
    newish: year >= 2000 ? 1 : 0,
  };
}
function profileVec(ids) {
  const v = {}; FEATS.forEach(f => v[f] = 0); let n = 0;
  ids.forEach(id => { const l = listingById(id); if (!l) return; const f = featurize(l); FEATS.forEach(k => v[k] += f[k]); n++; });
  if (n) FEATS.forEach(k => v[k] /= n);
  return n ? v : null;
}
function cosineSim(a, b) {
  let d = 0, na = 0, nb = 0;
  FEATS.forEach(k => { d += a[k]*b[k]; na += a[k]*a[k]; nb += b[k]*b[k]; });
  return (na && nb) ? d / (Math.sqrt(na)*Math.sqrt(nb)) : 0;
}

async function saveSwipe(id, liked) {
  if (supa && currentUser) { try { await supa.from('swipes').upsert({ user_id: currentUser.id, listing_id: id, liked }); } catch {} }
}
async function loadSwipes() {
  SWIPES = {};
  if (supa && currentUser) {
    try { const { data } = await supa.from('swipes').select('listing_id,liked'); (data||[]).forEach(r => SWIPES[r.listing_id] = r.liked); } catch {}
  }
}

// ── DEMO DATA ─────────────────────────────────────────────────────────────────
const DEMO_DATA = [
  {id:'d01',title:'50yr Old Kominka — Wood Stove Included',prefecture:'長野',city:'Komoro',price_jpy:1500000,price_label:'150万円',size_m2:120,land_m2:280,built_year:1972,rooms:'4LDK',condition:'要リフォーム',lat:36.33,lng:138.43,image_url:'https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Nagano',source:'Akiya2.com',description:'Traditional farmhouse surrounded by Nagano nature. Wood stove included, vegetable garden space. Renovation budget required.',tags:['古民家','長野','田舎暮らし','薪ストーブ']},
  {id:'d02',title:'Ocean View Akiya — Migration Welcome',prefecture:'高知',city:'Muroto',price_jpy:500000,price_label:'50万円',size_m2:85,land_m2:150,built_year:1985,rooms:'3DK',condition:'要修繕',lat:33.29,lng:134.15,image_url:'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Kochi',source:'Akiya2.com',description:'Hilltop property with Pacific Ocean view. Traditional fishing village atmosphere. Plumbing needs work.',tags:['海景','高知','移住','格安']},
  {id:'d03',title:'Hokkaido — 1200m² Land, Single Family Home',prefecture:'北海道',city:'Shibetsu',price_jpy:3000000,price_label:'300万円',size_m2:160,land_m2:1200,built_year:1990,rooms:'5LDK',condition:'良好',lat:44.17,lng:142.39,image_url:'https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Hokkaido',source:'Akiya2.com',description:'Enormous land plot in rural Hokkaido. Suitable for farming and dairy. Move-in ready. Water and electricity connected.',tags:['北海道','広大','農業','即入居']},
  {id:'d04',title:'Kyoto Suburbs — Renovated Machiya Townhouse',prefecture:'京都',city:'Kameoka',price_jpy:8000000,price_label:'800万円',size_m2:95,land_m2:90,built_year:1960,rooms:'3LDK',condition:'リノベーション済み',lat:35.01,lng:135.57,image_url:'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Kyoto',source:'Akiya2.com',description:'30 min from Kyoto Station. Traditional townhouse aesthetic with modern amenities. Fully move-in ready.',tags:['京都','町家','リノベ済み']},
  {id:'d05',title:'Okinawa Tropical Living — Old Single House',prefecture:'沖縄',city:'Uruma',price_jpy:2000000,price_label:'200万円',size_m2:75,land_m2:120,built_year:1978,rooms:'3K',condition:'要リフォーム',lat:26.37,lng:127.86,image_url:'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Okinawa',source:'Akiya2.com',description:'Tropical island life in warm Okinawa climate. Large garden, 2-car parking. Exterior paint needed.',tags:['沖縄','南国','格安','駐車場']},
  {id:'d06',title:'Okayama — FREE Kominka + 500m² Farmland',prefecture:'岡山',city:'Maniwa',price_jpy:0,price_label:'無償譲渡',size_m2:140,land_m2:500,built_year:1955,rooms:'6K',condition:'要大規模修繕',lat:35.08,lng:133.75,image_url:'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Okayama',source:'Akiya2.com',description:'Zero cost transfer. 500m² farmland included. Major renovation required. Priority given to migrants and farmers.',tags:['無償','岡山','農地','古民家']},
  {id:'d07',title:'Niigata Snowcountry — Near Ski Resort',prefecture:'新潟',city:'Uonuma',price_jpy:4500000,price_label:'450万円',size_m2:110,land_m2:200,built_year:1982,rooms:'4LDK',condition:'普通',lat:37.21,lng:138.97,image_url:'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Niigata',source:'Akiya2.com',description:'15 min drive to Echigo-Yuzawa ski resort. Hot spring town nearby. Heavy snowfall in winter.',tags:['新潟','スキー','温泉','雪国']},
  {id:'d08',title:'Kagoshima — Sakurajima View Kominka',prefecture:'鹿児島',city:'Tarumizu',price_jpy:1000000,price_label:'100万円',size_m2:90,land_m2:180,built_year:1969,rooms:'4K',condition:'要リフォーム',lat:31.49,lng:130.71,image_url:'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Kagoshima',source:'Akiya2.com',description:'Spectacular Sakurajima volcano view. Mild climate year-round. Volcanic ash management required.',tags:['鹿児島','桜島','絶景','格安']},
  {id:'d09',title:'Shimane — Old Kominka with Kura Storehouse',prefecture:'島根',city:'Gotsu',price_jpy:800000,price_label:'80万円',size_m2:105,land_m2:320,built_year:1963,rooms:'5K',condition:'要リフォーム',lat:34.99,lng:132.22,image_url:'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Shimane',source:'Akiya2.com',description:'Quiet village in Iwami region. Large garden with traditional kura storehouse. Off the beaten path.',tags:['島根','格安','蔵付き','田舎']},
  {id:'d10',title:'Miyazaki — Surfer Property Near Beach',prefecture:'宮崎',city:'Hyuga',price_jpy:1200000,price_label:'120万円',size_m2:80,land_m2:100,built_year:1980,rooms:'3DK',condition:'普通',lat:32.42,lng:131.62,image_url:'https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Miyazaki',source:'Akiya2.com',description:'10-min walk to surf spots. Warm subtropical Miyazaki climate. Ideal for beach lifestyle.',tags:['宮崎','海','サーフィン','移住']},
  {id:'d11',title:'Yamanashi — Mt. Fuji View Villa',prefecture:'山梨',city:'Fujikawaguchiko',price_jpy:5500000,price_label:'550万円',size_m2:88,land_m2:160,built_year:1995,rooms:'3LDK',condition:'良好',lat:35.51,lng:138.76,image_url:'https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Yamanashi',source:'Akiya2.com',description:'Direct Mt. Fuji view. 2h from Tokyo. In vacation resort area. Well maintained.',tags:['山梨','富士山','別荘','景色']},
  {id:'d12',title:'Ehime — Shimanami Kaido Cycling Base',prefecture:'愛媛',city:'Imabari',price_jpy:700000,price_label:'70万円',size_m2:98,land_m2:140,built_year:1971,rooms:'4K',condition:'要リフォーム',lat:34.07,lng:132.99,image_url:'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Ehime',source:'Akiya2.com',description:'Perfect base for Shimanami Kaido cyclists. Sea and mountain views. Surrounded by Seto Inland Sea scenery.',tags:['愛媛','しまなみ','サイクリング','格安']},
  {id:'d13',title:'Akita — Samurai Town Kakunodate Area',prefecture:'秋田',city:'Semboku',price_jpy:2500000,price_label:'250万円',size_m2:130,land_m2:250,built_year:1958,rooms:'5K',condition:'要リフォーム',lat:39.59,lng:140.56,image_url:'https://images.unsplash.com/photo-1480796927426-f609979314bd?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Akita',source:'Akiya2.com',description:'Near historic Kakunodate samurai district. Historical architecture. Heavy snowfall in winter.',tags:['秋田','角館','歴史','古民家']},
  {id:'d14',title:'Iwate — Tono Folklore Village Farmhouse',prefecture:'岩手',city:'Tono',price_jpy:600000,price_label:'60万円',size_m2:145,land_m2:800,built_year:1948,rooms:'6K',condition:'要大規模修繕',lat:39.33,lng:141.53,image_url:'https://images.unsplash.com/photo-1440778303588-435521a205bc?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Iwate',source:'Akiya2.com',description:'In the legendary Tono folklore village. 800m² farmland. Historic old farmhouse. Major renovation needed.',tags:['岩手','遠野','農地','民話','格安']},
  {id:'d15',title:'Hiroshima — Onomichi Hillside Townhouse',prefecture:'広島',city:'Onomichi',price_jpy:1800000,price_label:'180万円',size_m2:78,land_m2:95,built_year:1975,rooms:'3DK',condition:'要修繕',lat:34.41,lng:133.19,image_url:'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=500',source_url:'https://www.akiya2.com/prefecture-listing/Hiroshima',source:'Akiya2.com',description:'In the artistic hillside lanes of Onomichi. Film location town vibes. Seto Inland Sea area.',tags:['広島','尾道','坂道','アート','瀬戸内']},
];
