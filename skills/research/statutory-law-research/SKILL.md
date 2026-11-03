---
name: statutory-law-research
description: "Use when a legal question needs current statute text."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Legal, Law, Research, Sources, Government]
    category: research
    related_skills: [grounded-citations, blocked-page-recovery]
---

# Statutory Law Research

Questions of the shape "must I / can I / what happens now that X happened" that turn
on what a statute actually says: fines and sanctions, deadlines, licensing conditions,
obligations, procedures. The deliverable is a cited answer whose load-bearing
sentences rest on the operative provision as currently in force, not on a paraphrase
of a blog post or an old redaktsioon.

## When to Use

- Any question about rights, duties, sanctions, deadlines or procedure under an act or regulation.
- The user describes something that happened to them (a notice, fine, refusal, deadline) and asks about consequences.
- Skip for a bare definition with no consequences attached; answer directly there.

## Procedure

1. **Pin the jurisdiction and the governing act.** Name the act (and its abbreviation) before fetching anything. Search results are for finding the act's name and section number only.
2. **Fetch the CURRENT consolidated text from the official register**, never a versioned/older copy and never a third-party mirror. If the register renders as a JS app or the extractor returns only a table of contents or a truncated page, switch to the register's JSON API instead of to a mirror. Country recipe with exact endpoints and commands: `references/estonia-riigi-teataja.md`. Acts the register's abbreviation index does not cover (municipal/KOV regulations, `lyhend: null`) are resolved through the register's version list - same file.
3. **Prove the act is operative, not merely the latest version.** Check the text header's validity end and whether its body says `Kehtetu`; a version list's `kehtivRedaktsioon` can identify the repeal-only final text. If repealed, identify and fetch its successor act before citing any operative rule. Then check the version list and recent amendment markers; a per-act "current version" field can echo an older id.
4. **Read the operative subsection verbatim**, including its conditions ("only if", "does not apply when"). Quote it by section and subsection number in the answer.
5. **Trace the consequence chain across acts.** The substantive act states the rule; the procedural act states how it is applied; the records/archiving act states when the consequence lapses. A term like "a valid punishment" or "punished within the last 12 months" is only resolvable in the records act.
6. **Get the responsible agency's operational guidance** for the practical steps the statute does not spell out: how to apply, fees, automatic pre-checks, where the user checks their own data.
7. **Answer**: conclusion first, then the legal basis with section/subsection numbers, then the facts that would flip the answer, then how the user verifies their own case, then a plain source list.

## Answer Shape

- Mirror the user's language (question in Estonian -> answer in Estonian).
- Lead with the direct yes/no verdict in the first line, then justify.
- Cite section + subsection numbers, and quote the decisive clause in the national-language wording when the wording is what settles it.
- Always include the flip case: the changed facts (a different document type, a different subsection, a different date) that produce the opposite answer.
- Close with the user's self-check path (the register or agency portal where their individual data lives) plus the concrete fee/step numbers when the task involves an application.
- Add a short source list of plain URLs at the end.
- In CLI mode: plain text, no markdown headers, asterisks or fences.

## Pitfalls

- **Resolve an act's current id from the register's abbreviation index before fetching text.** Ids copied from amendment-history links, old search results, or the act's first publication URL serve an earlier redaktsioon; registers keep every version at its own URL and do not redirect. Verified failure mode: quoting a penalty rate and a section layout that had been superseded years earlier, silently.
- **A cited section number is the law of its time; reforms move content between sections.** Never map a preamble's or a document's section number straight onto today's text: content cited as KOKS § 35 lg 2 in 2019 reads in today's act at § 22 lg 1 p 34. When number and content disagree, fetch the redaktsioon valid on the document's date instead of "correcting" the citation.
- **The register stops at norms; individual decisions live elsewhere.** KOV acts' decisions (otsused), protocols and preparatory eelnõud sit in the municipality's document register and web archive, not in the statute register - continue the chain there (patterns in the country reference).
- **A snippet is not the text.** A search-result description supports only what it literally states; open the register page before making any claim about wording or amounts.
- **Read the provision, not a summary of it.** Law-firm blogs, driving-school pages and "fine calculator" portals rank highly and are frequently a year or more stale on amounts, and they drop the conditions. Use them to identify the act and section, verify every number in the register.
- **Sanction type outranks sanction size.** Separate a real punishment (entered in the criminal-records register, capable of triggering further legal consequences) from an administrative fixed-charge or warning notice (not registered, cannot ground other consequences). Ask which document the user actually holds before answering - the entire answer turns on it.
- **Superscript numbering breaks naive greps.** Extracted plain text renders section 262-1 and 54-8 style superscripts as a space plus digit; search for the space-plus-digit form, not the typographic character.
- **Do not over-answer the implied question.** Give the verdict for the case the user described, then explicitly the case that flips it; do not reason from a scenario they never stated.
- **Penalty-rate and threshold provisions are the most-amended text in any act** - re-verify their currency even when the rest of the act is clearly current.
- **For support-measure (toetusmäärus) eligibility, read the agency's KKK and info-session slides right after the act** - they answer the recurring edge cases (e.g. a degree in place of a required kutse) and reveal what the e-form accepts; cite the act for the rule, the KKK for how it is applied. A user-attached PDF of the act is a copy: check its redaktsioon header against the register's version list.
- **Agency social posts are interpretation, not law.** Useful for how enforcement actually treats a case, but the statute is what goes in the legal basis.

## Verification

- Every section cited appears verbatim in the fetched current text.
- The newest amendment marker in the fetched text is not older than the entry-into-force date of anything cited.
- Cross-act terms are resolved (substantive + procedural + records act).
- The answer states the flip condition and the user's self-check path.

## References

- `references/estonia-riigi-teataja.md` - Estonian register (Riigi Teataja) JSON API recipe, version-history resolution for acts without abbreviations (KOV), KOV decision/protocol sources (Amphora document register, DIGAR web archive) and institution checks in the business register, sanction vocabulary (karistus / hoiatustrahv / mõjutustrahv) and the registers that hold them, plus the practical agency sources.
