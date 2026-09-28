---
name: ux-copy
description: Write and review user-facing text for brevity and plain language — every string should read in about 2 seconds, no jargon, no exposed implementation detail. Use when writing or reviewing UI copy — headings, body microcopy, button labels, form fields, error/empty/loading states, confirmation and outcome text. Does not apply to legal/consent text (T&Cs, privacy policy body, GDPR consent language), which may run longer for legal completeness.
---

# UX Copy — plain, short, no leaks

Most user-facing text fails not because it's wrong, but because it makes the
user work to read it: long sentences, hedged qualifiers, and implementation
detail that belongs in a commit message, not a UI.

## The 2-second rule

Any user-facing string outside legal/consent text must be readable in about
2 seconds — roughly one short sentence, ~12 words, one idea. If a string
needs a second sentence to land, that's a sign to cut, not to keep writing.
Legal/consent copy (T&Cs, privacy policy body, GDPR consent language) is
exempt — precision there matters more than speed — but still prefer short
paragraphs and plain words over dense legal-brochure prose.

## Rules

1. **Plain words only.** If a non-technical user wouldn't say it themselves,
   don't write it. "Log in" not "authenticate." "Save" not "persist."
2. **Never expose the mechanism.** Users don't need to know about queues,
   webhooks, retries, endpoints, databases, async processing, feature flags,
   or "our system." Describe the outcome they get, not how it's built or
   what's happening (or not yet built) behind it.
3. **Name the outcome, not the mechanic**, on every button/link/CTA. "Send
   my report" beats "Submit." "Get updates" beats "Subscribe."
4. **One idea per sentence.** If a string does two things, it's two strings
   — a heading plus one short line, or a label plus placeholder — not one
   long sentence joined by "and" or "which."
5. **Errors: what happened, what to do — two short clauses, no more.**
   Skip technical causes and blame. "Couldn't save your changes. Try again."
   not "A network timeout occurred while persisting your changes to the
   server; please retry your request."
6. **Cut hedges and filler.** "Please note that," "in order to," "we just
   wanted to let you know" — delete them; the sentence loses nothing.
7. **A "not built yet" caveat is not a paragraph.** This team's
   scope-integrity rule (`product-owner.md` §7,
   `senior-software-engineer.md` "Scope Integrity") sometimes requires
   disclosing that something isn't automatic yet, so users aren't misled —
   that's a product decision, not a copy-length one. Keep the disclosure,
   but say it once in a short clause; don't let honesty become an essay.
   Whether the disclosure itself is still required is for the product
   owner to decide, not for a copy pass to remove unilaterally.

## Self-check before shipping any string

- Read it aloud. Past ~2 seconds (legal text excepted), cut it.
- Underline any word a non-technical friend wouldn't use in conversation —
  replace it or delete it.
- Count sentences in the string. More than one → split or cut.
- Would a user actually read this, or skim past it? If they'd skim, it's
  too long regardless of how important the content feels to the team.

## Example

Before (rewritten in this codebase's history to sound reassuring — but a
non-technical user has to read four sentences to find "leave your email"):

> "Observing Planner is new and still changing. Leave your address and I'll
> write when something worth knowing changes — including if clear-sky
> alerts start working. One email to confirm, then a few updates a year,
> written by me. Nothing here is automatic — clear-sky alerts don't exist
> yet, and this list is how you'd hear if they start working. One click
> unsubscribes and deletes your address."

After (same substance, same required disclosure, each string readable in
~2 seconds):

> Heading: "Get occasional updates"
> Body: "A few emails a year, written by me — nothing automatic yet."
> Button: "Email me updates"
> Fine print (below, smaller): "One click to unsubscribe and delete your
> address."

The "nothing automatic yet" clause is kept (per rule 7) because it's a
scope-integrity disclosure, not filler — it's just said once, briefly,
instead of across three sentences.
