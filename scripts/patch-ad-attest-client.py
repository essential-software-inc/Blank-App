#!/usr/bin/env python3
"""Adds Play Integrity attestation to the app's ad fetch, in place, for each HTML file given.

Usage: python3 scripts/patch-ad-attest-client.py [--skip-missing] <html file>...
Runs from package.json's "capacitor:sync:before" hook on www/index.html (the copy each Codemagic workflow just put there), so the
source HTML files in the repo stay untouched. --skip-missing: a file with no _nbFetchNextAd at all (the Admin stub) is left alone.

Replaces _nbFetchNextAd() with a version that sends the attested ad key, and adds the helpers it needs
right before it. Safe to re-run (skips files already patched); fails loudly on a file whose
_nbFetchNextAd doesn't look as expected.
"""
import sys

NEW = r"""// Play Integrity attestation (Android app only). The native PlayIntegrity plugin (added at build time by
// scripts/add-play-integrity.py) returns a Google-signed token; the worker's POST /ads/attest verifies it and hands back an "ad key"
// good for a day, which GET /ads/next presents. Everything here is background work: it never delays opening a note, and outside the
// compiled app (no plugin) it does nothing and the ad fetch behaves as before.
const NB_AD_KEY_STORE = 'nb_ad_key';
let _nbAdKeyInflight = null;
function _nbPlayIntegrityPlugin() {
  const cap = window.Capacitor && window.Capacitor.Plugins;
  return (cap && cap.PlayIntegrity) || null;
}
function _nbCachedAdKey() {
  try {
    const k = JSON.parse(localStorage.getItem(NB_AD_KEY_STORE) || 'null');
    return k && k.key && k.exp > Date.now() + 60000 ? k.key : null;
  } catch (e) { return null; }
}
function _nbEnsureAdKey(force) {
  const plugin = _nbPlayIntegrityPlugin();
  if (!plugin) return Promise.resolve(null);
  if (!force) { const have = _nbCachedAdKey(); if (have) return Promise.resolve(have); }
  if (_nbAdKeyInflight) return _nbAdKeyInflight;
  _nbAdKeyInflight = (async () => {
    try {
      const bytes = crypto.getRandomValues(new Uint8Array(32));
      const nonce = btoa(String.fromCharCode.apply(null, bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      const r = await plugin.requestToken({ nonce });
      const res = await fetch(NB_PUBLISH_API.replace(/\/$/, '') + '/ads/attest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewerId: _nbDeviceId(), appId: r.appId, nonce, integrityToken: r.token })
      });
      if (!res.ok) return null;
      const data = await res.json();
      if (!data || !data.adKey) return null;
      localStorage.setItem(NB_AD_KEY_STORE, JSON.stringify({ key: data.adKey, exp: Date.now() + (data.expiresIn || 3600) * 1000 }));
      return data.adKey;
    } catch (e) {
      _nbLog('ad attest', e);
      return null;
    } finally {
      _nbAdKeyInflight = null;
    }
  })();
  return _nbAdKeyInflight;
}

async function _nbFetchNextAd(kind) {
  // Short client-side timeout: a slow/unreachable network here should
  // never delay opening a fresh note, just silently fall back to the
  // pristine template exactly as if nothing were active.
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), 3000) : null;
  try {
    // Write asks without a kind (what every older app version sends), Share asks for its own pool.
    // The attested ad key rides along when there is one; with none yet, attestation starts in the background for next time.
    const ak = _nbCachedAdKey();
    if (!ak) _nbEnsureAdKey(false);
    const qs = [];
    if (kind === 'share') qs.push('kind=share');
    if (ak) qs.push('ak=' + encodeURIComponent(ak));
    const res = await fetch(NB_PUBLISH_API.replace(/\/$/, '') + '/ads/next' + (qs.length ? '?' + qs.join('&') : ''), controller ? { signal: controller.signal } : {});
    if (!res.ok) return null;
    const data = await res.json();
    // The worker wants a (fresh) attested key: get one in the background; this screen falls back to the template.
    if (data && data.needAttest) { _nbEnsureAdKey(true); return null; }
    return (data && data.ad) || null;
  } catch (e) {
    return null;
  } finally {
    if (timer) clearTimeout(timer);
  }
}
"""

SKIP_MISSING = "--skip-missing" in sys.argv

def patch(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if "_nbEnsureAdKey" in src:
        print("already patched:", path)
        return
    start = src.find("async function _nbFetchNextAd(kind) {")
    if start < 0 and SKIP_MISSING:
        print("no _nbFetchNextAd in %s - nothing to patch" % path)
        return
    if start < 0:
        raise SystemExit("ERROR: %s has no _nbFetchNextAd - not an app HTML file?" % path)
    end = src.find("\n}\n", start)
    old = src[start:end + 3]
    if "/ads/next" not in old or "finally" not in old:
        raise SystemExit("ERROR: _nbFetchNextAd in %s doesn't have the expected shape; update this script." % path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src[:start] + NEW + src[end + 3:])
    print("patched:", path)

files = [a for a in sys.argv[1:] if not a.startswith("--")]
if not files:
    raise SystemExit(__doc__)
for p in files:
    patch(p)
