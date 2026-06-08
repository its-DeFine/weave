# FableFrame Studio

FableFrame Studio is a small Month 1 proof application for the WEAVE lifecycle.
It is a static web tool that turns an owner brief into a visual-novel pitch,
draws generated scene previews in canvas, exports JSON, estimates lightweight
KPIs, and supports one mocked feedback iteration.

## Local Run

```bash
cd apps/fableframe-studio
python3 -m http.server 4173
```

Open the local preview URL printed by your shell.

## QA

```bash
python3 scripts/month1_product_app_qa.py --app-dir apps/fableframe-studio
```

The QA script checks static assets, JavaScript syntax, story generation,
feedback iteration, monetization configuration, local HTTP serving, and writes a
proof artifact under the local Codex artifact directory.

## Vercel

The app is Vercel-ready as a static site:

```bash
cd apps/fableframe-studio
vercel deploy
```

Live deployment is an external/public effect. Run it only after owner approval.

## Monetization

The default checkout is disabled:

```json
{
  "checkoutUrl": "",
  "priceCents": 900
}
```

To connect a real payment path, update `public/config.json` with an HTTPS
checkout URL. The UI keeps checkout disabled until that URL is configured.
