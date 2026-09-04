---
name: fastbull-editor
description: Turn raw Thai talking-head or VLOG footage into a polished vertical social edit using the free local FASTBULL pipeline. Use for VLOG, value, awareness, or sales clips that need footage review, Thai transcription, silence cuts, captions, inserts, sound effects, CTA, export, and QC.
---

# FASTBULL Editor

Use the repository's deterministic pipeline instead of recreating edit commands. It is local-first and must not call paid media providers unless the user separately requests and authorizes them.

## Intake

Identify the source video and editing mode: `vlog`, `value`, `awareness`, or `sales`. Accept Thai aliases. Use `FASTBULL` for the page name and the mode default CTA when the user supplies no override. Do not make the user complete a long questionnaire; ask only when a missing brand/offer fact would materially change the result.

Read [references/modes.md](references/modes.md) when choosing pacing or structure. Read [references/brand-system.md](references/brand-system.md) when changing visual styling. Read [references/quality-gates.md](references/quality-gates.md) before delivery.

## Execute

1. Run the doctor once per machine/session:

   ```bash
   .venv/bin/python scripts/fastbull_editor.py doctor
   ```

   On Windows use `.venv\Scripts\python.exe`. If it is not ready, run the free setup script for that OS; report the exact failed check.

2. Review the source and understand the transcript before choosing the hook. Never use an unrelated previous clip as the creative reference unless the user explicitly requests that.

3. Create a concise, truthful headline from the strongest audience benefit or tension. Pass it explicitly with `--headline`; the CLI's first-sentence fallback is a draft, not a client-ready editorial decision.

4. Run the editor:

   ```bash
   .venv/bin/python scripts/fastbull_editor.py run --input INPUT.mp4 --mode value --headline "HEADLINE" --page-name "FASTBULL" --cta "กดติดตาม"
   ```

   Add one or more `--broll FOLDER` arguments only for client-owned or editor-approved media. The fallback motion cards are original and cost-free.

5. Inspect `edit_analysis.json`. Apply only exact, confirmed corrections through `--corrections-json`. Do not auto-delete low-confidence speech, possible false starts, factual claims, names, figures, or repeated words that may be intentional. Silence removal is automatic; ambiguous language remains review-only.

6. Check `quality_report.json`, open representative frames, and watch/listen to the entire final MP4. Technical success alone is not delivery approval.

## Output contract

Return the final MP4 plus its job folder. State the selected mode, whether the headline was editor-confirmed, whether local B-roll or generated cards were used, and any review flags still requiring the user. Never claim the clip is viral or factually correct merely because it passed technical QC.
