# Design Tokens — Variant B (Gray and Plum)

Implement these as CSS custom properties in `static/css/tokens.css`. Templates and
components use the tokens only; no raw hex values elsewhere.

**Source of values:** colors marked *(guide)* are exact values from
`jm_wedding_brand_guidelines.html`. Colors marked *(PDF)* were sampled from the Variant B
PDF export and should be verified against the design source when available. Font sizes
are measured from the PDF at desktop width.

## 1. Color

### Brand
| Token | Value | Use |
|---|---|---|
| `--plum-950` | `#2D123B` *(guide)* | Headings, couple names, primary text emphasis |
| `--plum-800` | `#4B2164` *(guide)* | Primary buttons, selected radio, footer top rule |
| `--plum-700` | `#62327D` *(guide)* | Eyebrow labels, links, secondary button border/text, timeline dots, FAQ "+" icon |
| `--plum-500` | `#936BB0` *(guide)* | Ampersand accent in names, decorative accents |
| `--plum-rsvp` | `#3B1A4A` *(PDF)* | RSVP section background |
| `--lavender-300` | `#CBB8DC` *(guide)* | Decorative lines, short dividers in cards |
| `--lavender-200` | `#E2D7EC` *(guide)* | Text on dark plum (RSVP eyebrow, intro) |
| `--lavender-100` | `#F1EAF6` *(guide)* | Hero radial glow |

### Neutrals
| Token | Value | Use |
|---|---|---|
| `--paper` | `#FFFDFD` *(guide)* | Page background |
| `--white` | `#FFFFFF` | Cards, form card, inputs, nav |
| `--mist` | `#E8E5EC` *(PDF)* | "The Day" section background, selected radio fill, map placeholder |
| `--mist-deep` | `#DAD7E2` *(PDF)* | Footer background |
| `--silver-700` | `#68636E` *(guide)* | Secondary text on `--mist` backgrounds |
| `--silver-500` | `#928C98` *(guide)* | Hero divider rule |
| `--silver-300` | `#C9C4CD` *(guide)* | Input borders, timeline line, hero decorative circles |
| `--silver-200` | `#E3DFE5` *(guide)* | Card borders, section dividers, FAQ row borders |
| `--ink` | `#302936` *(guide)* | Body text, field labels, date line |
| `--muted` | `#716B76` *(guide)* | Secondary text on light backgrounds (addresses, helper text) |

### Contrast notes (WCAG AA, normal text needs 4.5:1)
- `--muted` on `--paper`: ≈ 5.2:1 — OK.
- `--muted` on `--mist`: ≈ 4.1:1 — **fails** for small text. Use `--silver-700` (≈ 4.7:1)
  for secondary text inside "The Day" section.
- `--plum-700` on `--white`/`--paper`: OK for eyebrow labels.
- On `--plum-rsvp`: use `--white` for headings and `--lavender-200` for small text.
- Never use `--silver-500`, `--silver-300` or `--lavender-300` for text.

### Attire swatches
Swatch colors are content entered in the Site Admin, not tokens. The PDF shows Lavender,
Lilac, Dusty Mauve, Light Gray, Sage Green and Ivory as examples.

## 2. Typography

| Token | Value |
|---|---|
| `--font-serif` | `"Cormorant Garamond", Georgia, "Times New Roman", serif` |
| `--font-sans` | `"Nunito Sans", "Segoe UI", Arial, sans-serif` |

- Cormorant Garamond: weights 400, 500, and 400 italic. Nunito Sans: 400, 600, 700.
  The body face in the PDF appears to be Nunito Sans; confirm against the design source.
- Self-host both (WOFF2) with `font-display: swap`. Both are SIL Open Font License.

### Type scale
| Role | Font | Size (mobile → desktop) | Weight | Line height | Other |
|---|---|---|---|---|---|
| Couple names (hero) | serif | 48px → 88px | 500 | 1.0 | letter-spacing -0.02em; color `--plum-950`; "&" in `--plum-500` italic |
| Section title (H2) | serif | 36px → 56px | 500 | 1.1 | color `--plum-950` |
| Invitation headline | serif | 28px → 40px | 400 | 1.25 | color `--plum-800` |
| Sub-heading (H3, e.g. "The order of the day", venue name) | serif | 24px → 28px | 500 | 1.2 | |
| Card time ("2:00 PM") | serif | 26px → 30px | 400 | 1.1 | color `--plum-800` |
| Timeline item title, FAQ question, radio label | serif | 20px → 22px | 400 | 1.3 | |
| Italic line ("invite you to celebrate…", footer message) | serif italic | 18px → 22px | 400 | 1.4 | color `--plum-800` |
| Body | sans | 15px → 16px | 400 | 1.6 | color `--ink` |
| Small / helper text | sans | 13px | 400 | 1.5 | color `--muted` |
| Field label | sans | 13px | 700 | 1.4 | letter-spacing 0.02em |
| Eyebrow label ("THE DAY", "CEREMONY") | sans | 11px → 12px | 700 | 1.4 | uppercase; letter-spacing 0.18em; color `--plum-700` |
| Date line ("TUESDAY, JANUARY 5, 2027 · 2:00 PM") | sans | 13px → 14px | 700 | 1.4 | uppercase; letter-spacing 0.16em; color `--ink` |
| Full names line | sans | 11px → 12px | 600 | 1.4 | uppercase; letter-spacing 0.12em |
| Nav link | sans | 12px | 600 | 1 | uppercase; letter-spacing 0.12em |
| Button | sans | 12px | 700 | 1 | uppercase; letter-spacing 0.12em |

## 3. Spacing
4px base scale.

| Token | Value |
|---|---|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 24px |
| `--space-6` | 32px |
| `--space-7` | 48px |
| `--space-8` | 64px |
| `--space-9` | 88px |

- Section padding: `--space-9` desktop, `--space-7` mobile.
- Card padding: `--space-6` desktop, `--space-5` mobile.
- Eyebrow → title gap: `--space-3`. Title → content gap: `--space-6`.
- Form field gap: `--space-5`.

## 4. Layout
| Token | Value |
|---|---|
| `--content-max` | 1120px |
| `--text-max` | 640px (invitation message, FAQ list, RSVP intro) |
| `--form-max` | 520px (RSVP form card) |
| `--gutter` | 24px desktop / 16px mobile |
| `--nav-height` | 64px |

- Desktop: Ceremony/Reception cards in two columns; Attire and Venue in two columns.
- Mobile (< 720px): everything single column; nav collapses to logo + "Kindly RSVP"
  button + menu toggle.

## 5. Radius, borders, shadow
| Token | Value | Use |
|---|---|---|
| `--radius-sm` | 8px | Inputs, radio cards |
| `--radius-md` | 16px | Ceremony/Reception cards, Venue card |
| `--radius-lg` | 24px | RSVP form card |
| `--radius-pill` | 999px | Buttons, stepper buttons |
| `--border` | `1px solid var(--silver-200)` | Cards, dividers |
| `--border-input` | `1px solid var(--silver-300)` | Inputs |
| `--shadow` | none | The design uses borders, not shadows |

## 6. Components

**Nav** — white background, bottom `--border`, sticky. Logo 44px left; links right;
"Kindly RSVP" primary button.

**Primary button** — background `--plum-800`, text `--white`, `--radius-pill`, height 40px,
padding 0 24px. Hover: `--plum-950`. Focus: 2px outline `--plum-500`, offset 2px.
Disabled: 50% opacity.

**Secondary button** ("See the details", "View on map") — transparent background,
1px border and text `--plum-700`, same height as primary. Hover: background `--lavender-100`.

**Hero** — centered; background `--paper` with a soft `--lavender-100` radial glow; two
large thin-outline circles (`--silver-300`, 1px) partly off-screen left and right; monogram
~300px desktop / 200px mobile; short divider rule 72px `--silver-500`.

**Event card** (Ceremony / Reception) — `--white`, `--border`, `--radius-md`, centered text:
eyebrow → time → date line → 40px `--lavender-300` divider → venue and address in `--muted`.

**Timeline** — vertical 1px `--silver-300` line; dot 14px `--plum-700` inside a 20px ring
(`--plum-700` 1px); time right-aligned left of the line as an eyebrow-style label; title
(serif) and subtitle (small) right of the line.

**Attire swatches** — 48px circles, 1px `--silver-200` border, name below in small text.
Desktop: 6 per row (do not wrap one swatch onto its own row); mobile: 3 per row.

**Venue card** — `--white`, `--border`, `--radius-md`; top area is a `--mist` map
placeholder (subtle grid lines, pin icon in `--plum-700`); body with eyebrow, venue name
(serif), address, secondary "View on map" button.

**RSVP section** — background `--plum-rsvp`; eyebrow and intro in `--lavender-200`; title
in `--white`; form card `--white`, `--radius-lg`, padding `--space-6`.

**Text input / textarea** — `--white`, `--border-input`, `--radius-sm`, height 40px
(textarea 72px min), placeholder `--muted`. Focus: border `--plum-700` + 3px ring
`--lavender-200`. Error: border `#A33A4A` and message below in `#A33A4A` (13px).

**Attending radio cards** — two equal cards, `--border-input`, `--radius-sm`, serif label.
Selected: background `--mist`, border `--plum-800`, radio filled `--plum-800`.

**Stepper** — two 36px circular buttons (1px `--plum-700` border, `--plum-700` "−"/"+"),
value between in serif 22px. Disable "−" at 1 and "+" at max.

**FAQ accordion** — rows separated by `--border`; question in serif; "+" icon `--plum-700`
rotates to "×" when open; answer in body text. Each row is a `<button>` with
`aria-expanded`.

**Footer** — background `--mist-deep`, 3px top border `--plum-800`; centered monogram
(~100px), names in serif with `--plum-500` "&", date line, italic message.

**Logo** — `our_monogram.png` must show no white/gray box. Provide a transparent PNG/SVG,
or process the PNG at build time to remove the white background.

## 7. Motion
- Smooth scrolling for anchor links; accordion open/close 200ms ease.
- Disable all transitions and smooth scrolling under `prefers-reduced-motion: reduce`.
