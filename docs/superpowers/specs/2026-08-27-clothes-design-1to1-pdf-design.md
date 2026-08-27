# Clothes Design 1:1 Sample Pattern Design

## Outcome

`clothes-design-skill` generates deterministic, one-size-at-a-time, true-scale pattern PDFs that can be tiled on A4 paper and assembled for a muslin sample. The generated geometry is the single source for the technical SVG, assembly overview, and tiled PDF, so the views cannot contradict each other.

## Scope and boundary

- Fix the crossover blouse so both asymmetric fronts are closed, positive-area, non-self-intersecting pattern pieces whose body width is preserved below the armhole.
- Generate a dependency-free vector PDF at `1 cm = 72 / 2.54 pt`.
- Tile onto A4 portrait pages with 10 mm overlap, page coordinates, alignment marks, a 50 × 50 mm calibration square, and explicit 100% print instructions.
- Include net seam line, true cutting line, grainline, fold/cut quantity, size, piece identity, and matching notches.
- Produce one size per PDF. A PDF is approved for muslin/sample development only.
- Exclude grading, production markers, shrinkage compensation, DXF/PLT, and authorization to bulk-cut fashion fabric.

## Architecture

Pattern drafting remains centimetre-based. A geometry module flattens quadratic paths, validates topology, applies explicit edge-aware seam allowances, and exposes the same canonical outlines to all renderers. A standard-library PDF writer emits vector paths directly and tiles a virtual full-size sheet into A4 viewports; no browser or third-party package is required.

## Acceptance gates

1. The crossover front pieces have positive area, no self-intersection, and retain at least the drafted quarter-bust width at the hem.
2. Cutting outlines are real offsets, not centre-scaled visual approximations; fold edges receive zero allowance.
3. Matching seam checks cover shoulders, side seams, sleeve cap/armholes, and collar/neckline within declared tolerances.
4. The PDF MediaBox is A4, its calibration square is exactly 50 mm in PDF units, adjacent tiles overlap by 10 mm, and every page is labelled.
5. Generated examples pass freshness validation and state the sample-only boundary.

