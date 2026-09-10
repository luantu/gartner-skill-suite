# Gartner Skill Suite

English | [简体中文](README.zh-CN.md)

A modular skill suite for auditable Gartner research workflows: PDF extraction, Chinese translation, Hype Cycle and Magic Quadrant analysis, annual comparison, cross-report insight, and structured presentation.

## Quick start

1. Copy the skill directories into the skills directory used by your agent runtime.
2. Start with `gartner-analysis`, the suite's authoritative router.
3. State the task and select the appropriate mode. For example:

   > Use `$gartner-analysis` to extract the fields and page anchors from this Gartner PDF. Use `mode=extract` and return Markdown.

   > Use `$gartner-analysis` to compare the 2025 and 2026 editions of this Gartner Hype Cycle. Use `mode=annual-hc` and cite page evidence.

4. Provide only source materials that you are authorized to process. Keep generated reports and source PDFs outside this repository.

## Modes and skills

| Goal | Entry point | Mode |
| --- | --- | --- |
| Extract metadata, fields, tables, and page evidence | `gartner-report-extraction` | `extract` |
| Translate a Gartner PDF into Simplified Chinese | `gartner-pdf-zh-translation` | `translate-pdf` |
| Analyze one Hype Cycle | `gartner-hype-cycle-analysis` | `single-hc` |
| Compare two Hype Cycle editions | `gartner-hype-cycle-analysis` | `annual-hc` |
| Analyze one Magic Quadrant | `gartner-magic-quadrant-analysis` | `single-mq` |
| Compare Magic Quadrant editions | `gartner-magic-quadrant-analysis` | `annual-mq` |
| Combine completed HC and MQ analyses | `gartner-hc-mq-insight` | `cross-insight` |
| Arrange a validated result for presentation | `gartner-structured-presentation` | `presentation` |

`gartner-annual-comparison` is retained as a compatibility entry point and routes to `gartner-hype-cycle-analysis` with `mode=annual-hc`.

## Recommended workflow

1. **Extract**: build an auditable input table from the source PDF and record page anchors.
2. **Analyze**: run the HC or MQ specialist for the selected mode. Keep Gartner statements, external evidence, and analysis clearly separated.
3. **Compare or combine**: use annual comparison only for comparable editions; use cross-report insight only after both HC and MQ analyses are complete.
4. **Present**: use the presentation skill to arrange verified content without changing its evidence or conclusions.
5. **Validate**: run the relevant validator before sharing results.

## Repository layout

- `gartner-analysis/`: router, shared protocols, validators, and tests
- `gartner-report-extraction/`: PDF extraction contract
- `gartner-pdf-zh-translation/`: translation scripts and page-level QA
- `gartner-hype-cycle-analysis/`: Hype Cycle analysis
- `gartner-magic-quadrant-analysis/`: Magic Quadrant analysis
- `gartner-hc-mq-insight/`: cross-report insight
- `gartner-structured-presentation/`: structured presentation contract
- `gartner-annual-comparison/`: compatibility entry point

## Validation

From `gartner-analysis/`:

```bash
python3 -m pytest -q tests
python3 scripts/validate_terminology.py --skills-root ..
```

The PDF translation scripts provide additional QA commands in `gartner-pdf-zh-translation/scripts/`.

## Scope and safety

This repository contains reusable skill instructions, references, scripts, and tests. It does not include Gartner source PDFs, customer materials, generated reports, credentials, API keys, caches, bytecode, or local machine metadata.

Use the skills only with source materials you are authorized to process and redistribute. Vendor-specific test data is represented by generic placeholders.

## License and third-party rights

Review Gartner's terms and the license of any source material before redistribution. This repository provides workflow instructions and tooling; it does not grant rights to redistribute Gartner reports or other third-party content.
