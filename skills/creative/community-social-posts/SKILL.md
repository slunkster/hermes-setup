---
name: community-social-posts
description: "Use when writing a Facebook post text for the user's orgs."
version: 1.0.0
metadata:
  hermes:
    tags: [facebook, social-media, postitus, estonian, announcement]
    related_skills: [google-workspace, estonian-proofreading, humanizer]
---

# Community social posts (Facebook etc.)

## When to Use
User asks for a post text ("tekst facebooki postituse juurde", announcement, kuulutus) for
Setomaa youth work, school, MTÜ Algatusruum, Välk Meedia or similar — usually announcing
a schedule, event, or table they just made.

## Rules (user preferences)
1. **Short by default.** Hook line + 1 sentence + link/CTA + 1–2 hashtags. NO long
   enumerations of every item/location/time in the text — the details live in the linked
   table or image. The user rejects list-style posts; start short instead of offering a
   long version first.
2. **Put the details behind a link** (`👉 [LINK]`). If the link target is a Google
   Sheet/Doc created in the session, it is private: ask before sharing it
   "anyone with link can view" (`google-workspace` Rule 1), then substitute the real URL.
3. Write in Estonian, friendly and inviting, a few emojis (1–3), no corporate tone.
4. Don't invent facts not in the source (price, registration, contact). Add only one short
   line noting what the user could add if relevant (e.g. tasuta / registreerimine).
5. Deliver the post text ready to copy, then at most one question — no long commentary.

## Poster / image to go with the post
No Canva needed: write an HTML poster (user wants square 1080×1080 "Facebook post" proportions by default; 4:5 1080×1350 as alternative) to ~/Hermes/<topic>/, render with
browser_exec (`Emulation.setDeviceMetricsOverride` 1080×1350 dpr 2 + `Page.captureScreenshot`),
check that `main.scrollHeight` is no larger than clientHeight (overflow), and look at the screenshot. Keep the poster short too:
title + places + activity names (no times) + "Tule kaasa!". A Seto-pattern red band on off-white works well.
Example: ~/Hermes/huviringid/plakat.html.

## Template
```
**<Pealkiri>! <1–2 emojit>**

<Üks lause: mis ja kellele, kutse kaasa tulla.>

👉 <LINK>

#Setomaa #<teema>
```
