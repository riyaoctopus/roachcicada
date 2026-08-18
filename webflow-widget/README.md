# Floating chat widget — install on roachcicada.co (Webflow)

`floating-chat-widget.html` is a single, self-contained snippet (CSS + HTML + JS, no external
dependencies) that mounts a floating "chat with sales" button in the bottom-right corner of every
page, and opens the live [Roach Cicada sales chat](https://dev.axonbos.com/roachcicada-chat/) in a
panel (desktop) or full-screen sheet (mobile, ≤640px viewport width) when clicked.

## Install (2 minutes)

1. In Webflow, go to **Project Settings → Custom Code**.
2. Open `floating-chat-widget.html`, select all, copy.
3. Paste the entire contents into the **Footer Code** box (this runs site-wide, before `</body>`,
   on every page — that's what makes the button appear everywhere without touching individual pages).
4. **Publish** the site.

That's it — no Embed element, no per-page setup. To show it on only specific pages instead, paste the
same snippet into that page's own "Before `</body>` tag" custom code field instead of the site-wide
footer.

## What it does

- A 60px circular button, bottom-right, in the brand's dark green (`#163a2a`) with a chat icon.
- A one-time dismissible tooltip ("Questions about Roach Cicada? Chat with our sales consultant.")
  appears ~2.5s after page load on desktop, to draw attention without being pushy. Shown once per
  browser session (`sessionStorage`), and only on screens wider than 640px (a tooltip has no useful
  anchor point on a full-screen mobile layout, so it's suppressed there).
- Clicking the button opens a panel: ~392×650px floating card on desktop, **true full-screen** on
  mobile (≤640px) — no floating card, no rounded corners, covers the entire viewport edge-to-edge,
  and locks background scroll while open.
- The panel loads `https://dev.axonbos.com/roachcicada-chat/` in an iframe, **lazily** — the iframe
  `src` is only set on first open, so it costs nothing on initial page load.
- Clicking the button again (now showing an ✕) or the header's close button closes the panel.
  Escape key also closes it.
- Every element is scoped under unique `rc-fw-*` ids/classes with `box-sizing: border-box` forced,
  so it won't visually clash with Webflow's own site styles.

## Verified before shipping

- Cross-origin iframe load works with no `X-Frame-Options` / CSP `frame-ancestors` blocking (checked
  the live deployment's response headers directly — none set).
- CORS preflight from an arbitrary origin returns `Access-Control-Allow-Origin: *`, so the embedded
  chat's own API calls work from `roachcicada.co`.
- Open/close toggle, focus handling (no aria-hidden-while-focused warnings), and the full-screen
  mobile layout were all tested in a local harness mimicking a third-party host page before this was
  written up as done.

## Updating the backend URL later

If the chat backend ever moves (new domain, different path), there is exactly one line to change —
`var CHAT_URL = "https://dev.axonbos.com/roachcicada-chat/";` near the bottom of the script — then
re-paste the updated snippet into Webflow and republish.

## Removing it

Delete the pasted block from Webflow's Custom Code settings and republish. Nothing else to clean up —
it doesn't set cookies, doesn't touch the rest of the page's DOM beyond its own `#rc-fw-root`
container, and the only persisted browser state is a single `sessionStorage` flag for the tooltip.
