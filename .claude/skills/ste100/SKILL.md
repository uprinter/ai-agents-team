---
name: ste100
description: Write and review English technical documentation in ASD-STE100 Simplified Technical English — sentence-length limits, one instruction per sentence, imperative procedures, active voice, approved verb forms, noun clusters of three words at most, six-sentence paragraphs, and safety notes that start with a command. Use for README files, runbooks, ADRs, spec.md, plan.md, and docs/ pages in a target project. Does not apply to UI strings (use ux-copy), to personal posts or outreach published under a person's own name, to legal text, or to non-English text.
---

# ASD-STE100 — Simplified Technical English for docs

ASD-STE100 is the controlled-language standard of ASD (Aerospace, Security and Defence Industries Association of Europe). The current edition is **Issue 9, January 2025**: 53 writing rules plus a dictionary of about 900 approved words. The standard is free on request from ASD, and ASD owns the copyright. This skill restates the writing rules in summary. It does not copy the dictionary, and it never claims a word is "approved" or "not approved" from memory.

## Scope

**Apply STE to** English prose in a target project's documentation: `README*`, runbooks, ADRs, `spec.md`, `plan.md`, `tasks.md` prose, and `docs/` pages.

**Do not apply STE to:**
- UI strings — `ux-copy` owns them.
- Personal posts or outreach published under a person's own name.
- Legal, consent, and licence text.
- Code, code blocks, commands, command output, log lines, quoted error messages, identifiers, file paths, and quotations from other sources.
- Non-English text.

## Two kinds of text

Classify each block before you write it. The rules differ.

| | Procedure (an instruction) | Description (an explanation) |
|---|---|---|
| Sentence length | **20 words maximum** | **25 words maximum** |
| Verb form | Imperative: "Restart the pod." | Simple present, past, or future |
| Unit | One instruction per sentence | One topic per paragraph, **6 sentences maximum** |

Code spans and identifiers count as one word each.

## Writing rules

1. **Use one word for one meaning.** Use the same term for the same thing in the full document. Do not use a synonym for variety. If the project has a glossary, use its terms.
2. **Use a word only in its usual part of speech.** Do not make a noun into a verb ("to action", "to task").
3. **Technical names and technical verbs are permitted.** Names of products, services, commands, APIs, files, and settings are technical names. Verbs that name a specific technical process (deploy, merge, rebase, provision) are technical verbs. For all other words, use the shortest common word: "use", not "utilize"; "start", not "commence"; "help", not "facilitate".
4. **Use these verb forms only:** infinitive, imperative, simple present, simple past, simple future, and the past participle as an adjective ("the deployed version"). Do not use "-ing" forms, except in a technical name ("load balancing"). Do not use "should", "could", or "would" in a procedure. Write "must" or give the command.
5. **Use the active voice.** In a procedure, always. In a description, use the passive only when the agent is not known or not important.
6. **Keep noun clusters to three words maximum.** Change "cluster node pool upgrade policy" to "the upgrade policy for the node pool".
7. **Write one instruction per sentence.** If two actions must occur at the same time, put them in one sentence.
8. **Put a condition before the instruction.** "If the job fails, restart it." Not: "Restart the job if it fails."
9. **Number the steps of a procedure.** Use one numbered step for each action. Show the result of a step after the step, not inside it.
10. **Put the most important information first** in a sentence and in a paragraph.
11. **Use articles and "that"** where they make the sentence clear. Do not remove them to save words.
12. **Do not use a vague pronoun.** If "it" or "this" can refer to two things, repeat the noun.

## Warnings and cautions

- A **warning** tells the reader about a risk to people or data. A **caution** tells the reader about a risk to equipment or service.
- Start with a short, clear command. Then give the reason in one sentence. Example: "Do not run `terraform destroy` on the shared state. This command deletes the production cluster."
- Put the note before the step that it applies to.

## Self-check before you open the MR

- Run `.claude/skills/ste100/scripts/ste100-check.sh <file>...` from this repository (`-p` for a procedure file) on every prose file you touched, and fix every line it reports before you push. Three authors missed the length rule by hand and paid two to four review rounds per MR (→ RP-49).
- Count the words in each sentence the script cannot split. Procedure: 20 maximum. Description: 25 maximum.
- Find each "-ing" word, each passive verb, and each "should". Rewrite each one, or confirm that it is a permitted exception.
- Count the sentences in each paragraph. Six is the maximum.
- Read each numbered step. Each step has one action.
- Find each noun cluster with more than three words. Rewrite it.

## In review

The reviewer runs the same script on the touched files first and cites its output. The reviewer records a **docs** finding in the `REVIEW-ATTESTATION` for each touched prose file. A finding names the file, the rule number from this skill, and the sentence. A sentence over its length limit, more than one instruction in one sentence, or a procedure that is not in the imperative is a blocking finding. A long word with a common short equivalent is a nit.

## Example

Before (39 words, conditional at the end, passive, "-ing", "should"):

> "The migration should be run by the operator after verifying that the backup has been successfully completed, and the application pods should be scaled down before starting it, otherwise data written during the migration might be lost."

After (procedure, 3 steps, each under 20 words):

> 1. Make sure that the backup is complete.
> 2. Scale the application pods to zero.
> 3. Run the migration.
>
> **Warning:** Do not run the migration while the pods run. The migration can lose new data.
