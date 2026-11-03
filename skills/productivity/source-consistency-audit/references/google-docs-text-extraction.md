# Reading public Google Docs / link shorteners without auth

## Resolve a short link (link2.it, bit.ly, tinyurl, ...)

```python
new_tab("https://link2.it/XXXXX"); wait_for_load()
info = page_info()            # {'url': 'https://docs.google.com/document/d/<ID>/edit?tab=t.0', 'title': ...}
```

The resolved URL gives the document ID and the title gives the document's
name — both are worth quoting back to the user so they can confirm you
opened what they meant. `curl -s -o /dev/null -w '%{redirect_url}'`
returns nothing for shorteners that redirect via JavaScript or a meta
refresh (and can exit non-zero); do not conclude from it that the link is
dead.

Two short links that resolve to the same `/document/d/<ID>/` path are the
same file. Compare IDs before treating them as separate sources.

## Get the plain text of a publicly shared Google Doc

```python
goto_url(f"https://docs.google.com/document/d/{doc_id}/mobilebasic")
wait_for_load()
text = js("document.body ? document.body.innerText : ''")
```

`/mobilebasic` renders the document as plain HTML text — headings, lists,
tables and form-like underscore lines all come through as innerText, no
auth needed for a link-shared file. It is the dependable path; use it for
every doc in the audit so the extraction method is identical.

Alternatives and what to watch for:

- `/edit` loads the full editor chrome ("Fail Muuda Kuva Tööriistad Abi",
  "Lülita ekraanilugeja tugi sisse"); its innerText is mostly UI noise.
  Use `/edit` only to read the browser tab title / confirm which doc is
  open.
- `/export?format=txt` triggers a download rather than a page navigation
  in the browser session. The page therefore stays on the previously
  loaded document and `innerText` returns THAT document's text — a silent
  wrong-source bug that looks like a successful extraction. If you use an
  export/download URL anyway, prove the text belongs to the target: the
  first line of a Google Doc body is the document title, so check it
  against the expected title before comparing anything.
- `document.body.innerText` reflects the currently rendered page. After
  any navigation, call `wait_for_load()` first, and if the text looks like
  a different document than expected, re-navigate before trusting it.

## Sign-in walls

A fetched page whose content is only `Sign in` / `accounts.google.com`
links means the file is not link-shared. Say that in the report ("this
link needs access — I could not read it"), and ask the user to share it or
paste the text. Do not guess the contents, and do not treat "title
loaded, body empty" as an empty document.

## Save before comparing

Dump each source to a file in the workspace (`kodukord.txt`,
`nousolek.txt`, ...) as you extract it, then do the fact-matrix work in
code. Extraction is the part that is expensive to redo, and a later
comparison pass should never depend on conversation history for the text.
