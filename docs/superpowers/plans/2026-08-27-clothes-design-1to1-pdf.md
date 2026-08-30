# Clothes Design 1:1 PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate geometrically valid crossover-blouse pieces and a dependency-free, tiled A4 1:1 PDF suitable for making one muslin sample.

**Architecture:** Keep canonical pattern coordinates in centimetres, add a focused geometry layer for topology and seam-allowance outlines, then feed both SVG and native vector PDF renderers from those results. PDF pages clip and translate one full-size virtual sheet, guaranteeing physical scale and consistent 10 mm overlaps.

**Tech Stack:** Python 3 standard library, existing SVG renderer, `unittest`/existing script test harness, minimal PDF 1.4 writer.

## Global Constraints

- One PDF contains exactly one selected size.
- Default paper is A4 portrait, 210 × 297 mm, with 10 mm tile overlap.
- Calibration square is exactly 50 × 50 mm.
- No runtime dependency on Chrome, ReportLab, CairoSVG, or network access.
- Output is for muslin/sample development only, not bulk production cutting.
- Preserve unrelated and pre-existing workspace changes.

---

### Task 1: Canonical geometry and crossover-front repair

**Files:**
- Create: `clothes-design-skill/scripts/pattern_geometry.py`
- Modify: `clothes-design-skill/scripts/pattern_drafting.py`
- Test: `clothes-design-skill/tests/test_pattern_geometry.py`

**Interfaces:**
- Produces: `flatten_path(path, tolerance_cm=0.05) -> list[Point]`, `signed_area(points) -> float`, `self_intersections(points) -> list`, and corrected `draft_crossover_blouse(...)` pieces.

- [ ] Write failing tests with hand-derived assertions: both fronts close, have positive area/no crossings, and hem span is at least the quarter-bust working width.
- [ ] Run `python3 clothes-design-skill/tests/test_pattern_geometry.py` and confirm failures identify the narrow lower-front defect.
- [ ] Implement path flattening/topology checks and correct both front paths so `w_big` and `w_small` are used as real piece widths.
- [ ] Run the focused test and existing drafting tests until green.
- [ ] Commit only Task 1 files.

### Task 2: True cutting outlines and match marks

**Files:**
- Modify: `clothes-design-skill/scripts/pattern_geometry.py`
- Modify: `clothes-design-skill/scripts/pattern_drafting.py`
- Test: `clothes-design-skill/tests/test_pattern_geometry.py`

**Interfaces:**
- Produces: `build_cut_outline(piece, tolerance_cm=0.05) -> list[Point]`, `Notch`, edge seam metadata, and `validate_sample_pattern(pieces) -> list[str]`.

- [ ] Add failing tests proving a 1 cm straight-edge allowance measures 1 cm, fold edges remain unoffset, and generated outlines remain positive/non-self-intersecting.
- [ ] Add failing seam-match tests for shoulders, side seams, sleeve cap versus armholes, and collar versus neckline using literal tolerances.
- [ ] Implement line/flattened-curve offsets with outward normals and miter-limited joins; add stable named notches and seam-role metadata.
- [ ] Run focused and full pattern tests; refactor only after green.
- [ ] Commit only Task 2 files.

### Task 3: Dependency-free tiled A4 PDF

**Files:**
- Create: `clothes-design-skill/scripts/pattern_pdf.py`
- Create: `clothes-design-skill/tests/test_pattern_pdf.py`
- Modify: `clothes-design-skill/scripts/draw_pattern.py`

**Interfaces:**
- Produces: `write_tiled_pdf(pieces, output, size, paper='A4', overlap_mm=10) -> PdfManifest`; CLI option `--pdf PATH` with exactly one `--size`.

- [ ] Write failing parser-level tests for A4 MediaBox, page count/labels, 10 mm overlap, and a 50 mm calibration vector measured in points.
- [ ] Run the PDF test and confirm it fails because the writer/API is absent.
- [ ] Implement a minimal PDF 1.4 object/xref writer, full-sheet placement, page clipping/translation, vector outlines, grainlines, notches, tile IDs, alignment marks, and print instructions.
- [ ] Integrate the CLI and reject multi-size PDF requests with an actionable error.
- [ ] Run PDF tests and all existing drawing tests until green; commit only Task 3 files.

### Task 4: Unified examples, skill contract, and release gate

**Files:**
- Modify: `clothes-design-skill/examples/regenerate.sh`
- Replace: `clothes-design-skill/examples/02-crossover-blouse-pattern.svg`
- Replace: `clothes-design-skill/examples/02-crossover-blouse-assembly-guide.svg`
- Create: `clothes-design-skill/examples/02-crossover-blouse-pattern-a4.pdf`
- Modify: `clothes-design-skill/examples/02-crossover-blouse-spec.md`
- Modify: `clothes-design-skill/examples/README.md`
- Modify: `clothes-design-skill/SKILL.md`
- Modify: `clothes-design-skill/references/industrial-delivery-contract.md`
- Modify: `clothes-design-skill/scripts/validate_skill.py`
- Modify: `clothes-design-skill/tests/test_examples_current.py`

**Interfaces:**
- Consumes: corrected canonical pieces and `write_tiled_pdf`.
- Produces: reproducible SVG/PDF examples and a validation gate that rejects stale or scale-invalid sample deliverables.

- [ ] Add failing freshness/contract tests that regenerate the PDF, inspect its scale manifest, and reject missing sample-only warnings.
- [ ] Update regeneration so technical SVG, assembly overview, spec, and PDF all derive from the same M-size draft.
- [ ] Update the skill workflow: 1:N SVG remains explanatory; only the validated 1:1 PDF is eligible for muslin cutting.
- [ ] Regenerate examples and remove any manually invented assembly geometry.
- [ ] Run `python3 clothes-design-skill/scripts/validate_skill.py`, `git diff --check`, and inspect the generated PDF/page overview.
- [ ] Commit only the feature files, leaving unrelated staged/dirty files untouched.

