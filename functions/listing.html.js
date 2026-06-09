// Cloudflare Pages Function — injects Open Graph tags for /listing?id=…
// so Discord / Slack / WhatsApp previews show the property image and key details in English.
// Regular browsers pass straight through to the static listing.html.

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
    const metaRes = await fetch(new URL('/listing-meta.json', url).toString());
    if (!metaRes.ok) return next();
    const meta = await metaRes.json();
    const l = meta[id];
    if (!l) return next();

    const title = l.title_en || 'Akiya Property';
    const price = fmtPrice(l.price_jpy);
    const parts = [
      l.prefecture || null,
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
