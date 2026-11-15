# Newspaper articles (ajaleht Setomaa etc.)

## Procedure
1. **Ask before writing** (one clarify form, the user expects it): date + venue, game/sport and
   format, organiser, sponsors/supporters, prizes, broadcast/viewer numbers, quotes, final score,
   length + byline. If the user says "siit leiad infot" but nothing is attached, ask for it.
2. Default shape: medium news story ~2500–3500 chars — headline, bold juhtlõik, body,
   one subheading, byline (user's name, italic) at the end.
3. **Never invent quotes.** If none are given, write without them and offer to add one.
   Don't invent specifics the user didn't give (e.g. "teams trained for weeks") — describe
   the discipline in general terms instead.
4. Write the article to `~/Hermes/<topic>/<name>.html` (simple HTML: h1, p, b, h2, i),
   then run `scripts/copy_html_to_clipboard.py <file>` and `open` the file. Tell the user
   to press ⌘V in Google Docs (fallback: ⌘A/⌘C in the opened browser tab). Pasting chat
   markdown into Docs loses formatting — the rich-text clipboard is the deliverable.
5. Follow-up edits: patch the exact sentence in the HTML (assert the old string exists),
   re-copy to clipboard, and show only the changed passage in chat.

## Style rules (user preferences)
- **No bullet/numbered lists in the article** — rankings and results go in flowing prose
  ("Kolmandaks tuli X, neljandaks Y, viiendaks Z ja kuuendaks W.").
- **Avoid English expressions**: play-off → väljalangemismängud, MVP → turniiri parima
  mängija medal, tiim → meeskond. Keep only proper names (event, game, team, company names).
- Prize money: state it **per team** (total for the team), not per player.
- Don't credit the broadcast production crew unless asked; commentators may be named.
- Avoid flat, matter-of-fact openers like "Turniir peeti ühe päevaga." — fold the fact into
  a livelier sentence ("Pingeline võistluspäev algas alagrupimängudega…").
- Endings should be punchy: a strong claim + a forward-looking hook (e.g. will the champion
  win again?), not a generic summary sentence.
- E-sport stories: the user wants it framed as real sport — tactics, roles, teamwork,
  pressure, broadcast with commentators, spectators — not "kids playing video games".
- Use sponsor names exactly as the user writes them; don't "correct" them to the brand's
  self-styled form.
- Scores with a colon (2:0); ranges with mõttekriips. Run `estonian-proofreading` checks.
