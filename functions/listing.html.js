// Cloudflare Pages Function — injects Open Graph tags for /listing?id=…
// so Discord / Slack / WhatsApp previews show the property image and key details in English.
// Regular browsers pass straight through to the static listing.html.
//
// Uses ids.json (id→chunk index) + listings-{c}.json to look up the listing
// instead of the monolithic listing-meta.json (which grows without bound).

const BOT_RE = /bot|discord|slack|twitter|facebook|linkedin|whatsapp|telegram|crawler|spider|preview|embed|facebookexternalhit/i;
const EUR_RATE = 0.0062;

function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function fmtPrice(jpy) {
  if (jpy == null) return null;
  if (jpy === 0)   return 'Free (無償譲渡)';
  const eur = Math.round(jpy * EUR_RATE);
  if (jpy >= 1_000_000) return `¥${(jpy / 1_000_000).toFixed(1)}M ≈ €${eur.toLocaleString()}`;
  return `¥${jpy.toLocaleString()} ≈ €${eur.toLocaleString()}`;
}

export async function onRequestGet(context) {
  const { request, next } = context;
  const ua = request.headers.get('User-Agent') || '';
  if (!BOT_RE.test(ua)) return next();

  const url = new URL(request.url);
  const id  = url.searchParams.get('id');
  if (!id) return next();

  try {
    const base = url.origin;

    // Step 1: find which full chunk contains this listing via ids.json
    const idsRes = await fetch(`${base}/ids.json`);
    if (!idsRes.ok) return next();
    const ids = await idsRes.json();

    const chunkIdx = (ids.chunks || []).findIndex(arr => arr.includes(id));
    if (chunkIdx < 0) return next();

    // Step 2: fetch only that one chunk and find the listing
    const chunkRes = await fetch(`${base}/listings-${chunkIdx}.json`);
    if (!chunkRes.ok) return next();
    const chunk = await chunkRes.json();

    const l = (chunk.listings || []).find(x => x.id === id);
    if (!l) return next();

    const PREF_EN = {'北海道':'Hokkaido','青森':'Aomori','岩手':'Iwate','宮城':'Miyagi','秋田':'Akita','山形':'Yamagata','福島':'Fukushima','茨城':'Ibaraki','栃木':'Tochigi','群馬':'Gunma','埼玉':'Saitama','千葉':'Chiba','東京':'Tokyo','神奈川':'Kanagawa','新潟':'Niigata','富山':'Toyama','石川':'Ishikawa','福井':'Fukui','山梨':'Yamanashi','長野':'Nagano','岐阜':'Gifu','静岡':'Shizuoka','愛知':'Aichi','三重':'Mie','滋賀':'Shiga','京都':'Kyoto','大阪':'Osaka','兵庫':'Hyogo','奈良':'Nara','和歌山':'Wakayama','鳥取':'Tottori','島根':'Shimane','岡山':'Okayama','広島':'Hiroshima','山口':'Yamaguchi','徳島':'Tokushima','香川':'Kagawa','愛媛':'Ehime','高知':'Kochi','福岡':'Fukuoka','佐賀':'Saga','長崎':'Nagasaki','熊本':'Kumamoto','大分':'Oita','宮崎':'Miyazaki','鹿児島':'Kagoshima','沖縄':'Okinawa'};

    const title = l.title_en || l.title || 'Akiya Property';
    const price = fmtPrice(l.price_jpy);
    const parts = [
      PREF_EN[l.prefecture] || l.prefecture || null,
      l.size_m2    ? `${l.size_m2} m²`      : null,
      l.rooms      || null,
      l.built_year ? `Built ${l.built_year}` : null,
      price        || null,
    ].filter(Boolean);

    const desc      = parts.join(' · ');
    const img       = l.image_url || '';
    const pageTitle = `${title}${price ? ' — ' + price : ''} | Akiya Search`;

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${esc(pageTitle)}</title>
<meta property="og:type"         content="website">
<meta property="og:site_name"    content="Akiya Search 空き家">
<meta property="og:title"        content="${esc(title)}${price ? ' — ' + esc(price) : ''}">
<meta property="og:description"  content="${esc(desc)}">
<meta property="og:url"          content="${esc(url.href)}">
${img ? `<meta property="og:image"        content="${esc(img)}">
<meta property="og:image:width"   content="800">
<meta property="og:image:height"  content="533">` : ''}
<meta name="twitter:card"         content="summary_large_image">
<meta name="twitter:title"        content="${esc(title)}${price ? ' — ' + esc(price) : ''}">
<meta name="twitter:description"  content="${esc(desc)}">
${img ? `<meta name="twitter:image"        content="${esc(img)}">` : ''}
</head>
<body></body>
</html>`;

    return new Response(html, {
      headers: { 'Content-Type': 'text/html;charset=utf-8' },
    });
  } catch {
    return next();
  }
}
