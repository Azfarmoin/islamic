# Master Director package

Implements the output format of your MASTER DIRECTOR ENGINE spec (sections 1-28) **on top of** the existing director, without rebuilding it.

Every rendered video now gets `director_package.md` / `.json` next to it (also an artifact in the daily workflow), or run `python -m ivs package story:iqra` / `quran:114:1-4`.

Contents: Director Card, Authenticity Card (classes A established / B interpretation / C reconstruction / D metaphor, certainty, what must NOT be depicted), Hook, Anticipation plan, Story flow, Scene table, Frame-by-frame (hook, peak, ending), Transition map and Camera map (each with the reason), Prop map, Model map, Sound map, Text map, Continuity bible, an AI generation prompt per scene (with negative constraints) and the 21-point QC checklist.

## What is automatic and what is not
- Fields are copied from decisions the engine really made (treatment, storyboard, verified text). Nothing is invented. Reasons for camera moves and transitions come from fixed lookup tables, not from an LLM.
- QC items it can check are marked PASS/FAIL (hook, camera variety, no repeated director, actors whitelist, Quran exactness, forbidden hype words). Items only a person can judge (Arabic typography on a phone, invented religious claims, fake quotations, "generic AI feel", dua wording) are always **MANUAL**; the engine never ticks them for you.
- "Opening and ending visually connect" is PARTIAL unless the first and last environments match: the engine does not yet plan a deliberate visual callback (a closed door that opens at the end).

## Not covered by this spec yet
The package is documentation of the plan. The renderer does not yet realise: rack-focus, match cuts, mosque interiors, rain/forest scenes, or per-scene dramatised-dialogue labels. Quran-walk clips (recitation only) get a reduced package. See `docs/LIMITATIONS.md`.

## Frame records and the second continuity pass
Every planned shot gets one structured record with all 24 fields of the frame-record spec (FRAME ID ... NEXT-FRAME TRANSITION, plus a BASIS tag: A = from the verified text, B = engine inference, C = artistic choice). Faces/expressions are always "none: faceless by rule". After all records exist, an automatic second pass over the whole story flags: environment change on a hard cut, the same camera move twice in a row, lighting change inside one environment. It is an automatic check only; a human still watches the video.
Honest limits: one record per planned scene (the engine's shot), not one per rendered video frame; the per-frame "director question loop" is the deterministic selection the engine already makes, not a live re-design; no new 3D assets were added by this change.
