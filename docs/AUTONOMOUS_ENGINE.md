# Autonomous engine spec (stages 0-32): what exists

| Stage | Status | Where |
|---|---|---|
| 0-3 input, ideas, research, audience | Partly. Content comes from a curated queue / Quran walk / your stories; ideas are not auto-scored. Claims verified via docfacts (VERIFIED/DISPUTED/UNCERTAIN) | content.py, docfacts.py, topics.py |
| 4 hooks | Multiple hook candidates + scoring | hooks.py |
| 5-8 story, script, dialogue | Structured beats; AI draft (any key) is validated line by line. No invented dialogue is ever labelled a quotation | scriptgen.py |
| 9-15 director, scenes, shots, characters, environments, props, camera | Yes, per video; unique camera/palette/scenery vs previous | direction.py, masterplan.py, studio.py |
| 16 visual explanation | Planned per shot (map/timeline/before-after/scale); only scenery/camera/text rendered | explain.py |
| 17-21 animation, VFX, SFX, music, editing | Parallax + optional 3D key shots, effects, real CC SFX, edit timeline. No music during recitation; no music track generated | anim.py, vfx.py, openverse.py |
| 22-23 retention / virality review | Heuristic engagement score only, not a viewer simulation | engagement.py |
| 24-25 QC reviewers | Automated checks (dimensions, codec, audio audible, sync, black frames, glyphs, subtitles, motion) + production checklist. No separate "reviewer" models; human review required | qc.py, vqc.py, explain.py |
| 26 package | 14 JSON files + report per video | studio.py |
| 27 titles/thumbnails | Thumbnail studio; metadata generated | thumbstudio.py, pipeline.py |
| 29 final render review, fix, re-render | Checks yes; auto fix-and-rerender loop is limited | qc.py |
| 30-31 publish safety + upload | Eligibility gate, quota guard, resumable upload, thumbnail, state record. Review gate stays on | publish_youtube.py |
| 32 analytics + learning | `python -m ivs stats`: views/likes/comments only. No CTR, watch time or retention (needs Analytics API scope). Learning notes are advisory, never auto-applied | analytics.py |

Rule kept on purpose: stories, hadith and AI drafts always need human approval, so "automatic publish with no human" is not enabled for them.
