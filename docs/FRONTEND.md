# FRONTEND — The Roundtable

### Design direction: "Precision Instrument" — Apple-grade minimalism, terminal-native micrographics

**Stack:** React 18 \+ Vite (kept from the llm-council fork) · vanilla CSS with custom properties (no Tailwind, no component library — this design is 90% typography and spacing, a library would fight it) · zero chart libraries — every graphic is typographic (ASCII/Unicode glyphs) or a ≤40-line inline SVG.

**The one-line brief:** it should look like Apple designed a Bloomberg terminal for watching AIs argue.

---

## 1\. Design rationale (why ASCII fits, and where it stops)

The product's promise is *visible machinery* — budgets, scores, costs, who's winning. ASCII/monospace micrographics are the native visual language of machinery, and they solve a real POC problem: `▓▓▓▓▓▓░░░░ 640` renders instantly, animates by string replacement, streams over SSE as plain text, and never needs a charting dependency.

The discipline that keeps it Apple and not "hacker theme":

- **ASCII is for data only.** Budgets, scores, sparklines, event log. Never for decoration, borders, or headings.  
- **Everything else is quiet.** Near-white canvas, one text color at three opacities, huge whitespace, one accent color per agent used sparingly.  
- **No terminal cosplay.** No green-on-black, no scanlines, no blinking cursor, no `>` prompts.

## 2\. Design tokens

:root {

  /\* Canvas & ink — warm paper white, near-black ink \*/

  \--bg:        \#FAFAF8;

  \--ink:       \#1D1D1F;          /\* Apple's near-black \*/

  \--ink-60:    rgba(29,29,31,.60);

  \--ink-30:    rgba(29,29,31,.30);

  \--hairline:  rgba(29,29,31,.10);

  \--card:      \#FFFFFF;

  /\* Agent accents — muted, editorial, one per persona \*/

  \--brand:     \#B4432F;   /\* Brand Manager  — oxblood   \*/

  \--media-mgr: \#2F6DB4;   /\* Media Manager  — cobalt    \*/

  \--script:    \#7A5CB4;   /\* Scriptwriter   — violet    \*/

  \--copy:      \#B4832F;   /\* Copywriter     — ochre     \*/

  \--planner:   \#2F8A62;   /\* Media Planner  — pine      \*/

  \--chairman:  \#1D1D1F;   /\* Chairman — no color, pure ink \*/

  /\* State \*/

  \--gain:      \#2F8A62;

  \--loss:      \#B4432F;

  /\* Type \*/

  \--sans: \-apple-system, "SF Pro Display", Inter, system-ui, sans-serif;

  \--mono: "SF Mono", "IBM Plex Mono", ui-monospace, monospace;

  /\* Scale (1.25 ratio) \*/

  \--t-hero: clamp(28px, 4vw, 44px);  /\* brief headline \*/

  \--t-name: 15px;                     /\* agent names \*/

  \--t-body: 15px; \--t-data: 13px; \--t-micro: 11px;

  \--radius: 14px;

  \--ease: cubic-bezier(.22,1,.36,1);

}

Type rules: sans for everything humans say (turns, verdict, headings, letter-spacing −0.01em on headings). Mono **exclusively** for machine truth (credits, scores, costs, the event log, all glyph graphics). This split *is* the visual system — a reader learns in 5 seconds that monospace \= the game state.

## 3\. The micrographic vocabulary (the signature)

All built from strings, tabular by nature, animated by re-render \+ CSS transition on a wrapping span.

BUDGET METER      ▓▓▓▓▓▓▓░░░  640          (10 cells \= B₀; loss flashes \--loss)

CHARGE TICKER     − 62 ▸ 578                (appears right of meter for 1.2s, fades)

REWARD TICKER     \+ 300 ▸ 878               (--gain)

SCORE ROW         N 8 · E 6 · P 7 · R 2     (mono, ink-60; winner row full ink \+ 🏆→ replaced by "WIN" tag, no emoji)

NOVELTY SPARK     ▁▃▆█▅                     (per-agent novelty across rounds, 5 glyphs max)

ROUND MARKER      ROUND 2 / 3 ─────────     (mono micro caps, hairline rule)

MUTED STATE       ░░░░░░░░░░ 0   SILENCED   (meter empties, whole card drops to 35% opacity)

EVENT LOG LINE    14:02:11  copywriter  fine  −100  redundancy 8/10

Rules: box-drawing characters (`─`) only as rules/dividers inside mono blocks; block elements (`▓░▁▃▆█`) only as data; never mix ASCII into sans-serif copy.

## 4\. Layout

Single screen, no routes. Desktop ≥1024px is a two-column stage; mobile stacks.

┌────────────────────────────────────────────────────────────────────┐

│  THE ROUNDTABLE                                    ROUND 2/3 ────  │   header: micro caps, hairline below

├──────────────────────────────┬─────────────────────────────────────┤

│                              │                                     │

│         THE TABLE            │        THE TRANSCRIPT               │

│                              │                                     │

│        ( circular SVG,       │   Priya · Brand Manager             │

│      5 nodes on a ring,      │   Performance spikes decay; the     │

│      speaker node breathes,  │   brand compounds. Rohan's CPM…     │

│     hairline chord drawn     │   ─ cost 62 ▸ ▓▓▓▓▓▓░░░░ 578        │

│     speaker→last rebutted )  │                                     │

│                              │   Rohan · Media Planner             │

│  ┌ agent chips under table ┐ │   At ₹180 CPM that “brand film”…    │

│  │ ● Priya  ▓▓▓▓▓▓░ 578    │ │                                     │

│  │ ● Rohan  ▓▓▓▓▓▓▓ 812    │ │   ── ROUND 1 SETTLED ───────────    │

│  │ ● Sana   ▓▓▓░░░░ 310    │ │   WIN  rohan   \+300   N8 E9 P7      │

│  │ ● Dev    ░░░░░░░ 0  SIL │ │   2ND  priya   \+100   N7 E6 P8      │

│  │ ● Mira   ▓▓▓▓░░░ 455    │ │   FINE dev     −100   redundancy    │

│  └─────────────────────────┘ │                                     │

├──────────────────────────────┴─────────────────────────────────────┤

│  \[ Brief input · one field, one button: “Convene” \]                │   pre-debate this is the hero, centered

└─────────────────────────────────────────────────────────────────────┘

**Pre-debate state (the hero):** empty canvas, centered — product name in micro caps, one large sans headline ("Five specialists. One brief. Watch them earn their say."), a single input, a single black pill button **Convene**. Under it, the five agents as quiet chips with full `▓▓▓▓▓▓▓▓▓▓ 1000` meters. That's the whole screen. Apple restraint \= the empty state is the marketing page.

**Verdict state:** table dims to 40%, a white card slides up center: "THE VERDICT" micro-caps eyebrow, chairman synthesis in sans, then a mono block crediting winning arguments by agent color-dot. One button: **Export transcript**.

## 5\. The Table (center SVG) — precise spec

- One `<svg viewBox="0 0 400 400">`: a single hairline circle (r=150, stroke `--hairline`), 5 agent nodes at `angle = -90° + i·72°`.  
- Node \= 44px circle, white fill, 1.5px stroke in agent accent; inside, the agent's **initial** in sans 600\. Name in `--t-micro` caps below the node. No avatars, no illustrations, no emoji.  
- **Speaking:** node scales to 1.12 and gains a soft accent glow (`filter: drop-shadow(0 0 12px accent-30%)`), pulsing at 2s. Everything else stays still.  
- **Rebuttal chord:** when a turn names another agent, draw one hairline line node→node in the speaker's accent at 25% opacity, fade out over 3s. This is the only "flashy" element — it earns its place because it visualizes *engagement*, the thing the loss function rewards.  
- **Muted:** node stroke → `--ink-30`, initial → `--ink-30`, tiny mono tag `SILENCED` under the name.  
- Center of the ring: current round in mono micro caps (`ROUND 2/3`), nothing else.

## 6\. Motion (complete list — nothing else animates)

| Event | Animation |
| :---- | :---- |
| Turn text arrives | Fade-up 12px, 300ms `--ease` (per turn; per-token streaming just appends text, no effect) |
| Budget charge/reward | Meter cells change instantly; the numeric value counts via CSS transition 400ms; ticker fades in/out |
| Round settles | Scoreboard block fade-up; winner's meter does one 1.2s `--gain` underline sweep |
| Agent goes silent | Card opacity → .35 over 600ms; node desaturates |
| Verdict | Backdrop dim \+ card slide-up 24px, 500ms |

`@media (prefers-reduced-motion)` kills all of it. No parallax, no confetti, no spring physics.

## 7\. Components & build instructions

src/

  state/useDebate.js      EventSource → useReducer; single source of truth

  lib/glyphs.js           meter(balance,max)→"▓▓▓░░", spark(values)→"▁▃▆█"

  components/

    Hero.jsx              pre-debate state \+ brief input

    Table.jsx             the SVG ring (§5)

    AgentChip.jsx         dot \+ name \+ \<Meter/\> \+ ticker

    Meter.jsx             renders glyph string in mono; props: balance, max, delta

    Transcript.jsx        turn cards \+ inline round-settlement blocks

    RoundSettlement.jsx   mono score table (WIN/2ND/FINE rows)

    Verdict.jsx           final card

    EventLog.jsx          collapsible mono log (dev/trust view, hidden behind ⌘K or a "log" text button)

**Implementation order (fits the 20–28 min slot in the architecture doc):**

1. `glyphs.js` \+ `Meter` — 15 lines, unlocks everything visual.  
2. `useDebate` reducer against the SSE event schema (already defined in ARCHITECTURE §3).  
3. `Hero` → `Transcript` (the product works end-to-end here, ugly but functional).  
4. `AgentChip` row, then `Table` SVG.  
5. Tokens/polish pass: spacing (8px grid, sections at 48/64px gaps), hairlines, motion.

**Hard rules for whoever builds it (Claude Code prompt-ready):**

- No component libraries, no chart libraries, no icon packs, no emoji in UI chrome.  
- Mono font only inside elements carrying game state; sans everywhere else.  
- Max 2 font sizes visible in any one component.  
- Every color must be a token from §2 — no ad-hoc hex.  
- Nothing animates except the six rows in §6.  
- Ship keyboard focus states and reduced-motion; meters get `aria-label="Priya budget 578 of 1000"`.

## 8\. Quality bar / self-critique checklist

- Squint test: screen reads as 3 zones (table / transcript / input), not 12 boxes.  
- Remove-one-accessory pass: if the rebuttal chord AND node glow AND ticker all fire at once, cut the glow.  
- A screenshot with numbers redacted should still look designed; a screenshot of only the mono blocks should still tell the whole game state.

