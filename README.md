# Gartner Skill Suite

A modular Gartner analysis skill suite for PDF extraction, Chinese translation, Hype Cycle and Magic Quadrant analysis, annual comparison, cross-report insight, and structured presentation.

## Included skills

- `gartner-analysis`: authoritative router and shared protocols
- `gartner-report-extraction`: auditable PDF extraction
- `gartner-pdf-zh-translation`: Chinese PDF translation with page-level QA
- `gartner-hype-cycle-analysis`: single-year and annual Hype Cycle analysis
- `gartner-magic-quadrant-analysis`: single-market and annual Magic Quadrant analysis
- `gartner-hc-mq-insight`: cross-report insight with optional domain profiles
- `gartner-structured-presentation`: structured report and presentation formatting
- `gartner-annual-comparison`: compatibility entry for annual Hype Cycle comparison

## Scope and safety

This repository contains reusable skill instructions, references, scripts, and tests. It does not include Gartner source PDFs, customer materials, generated reports, credentials, API keys, caches, bytecode, or local machine metadata.

Vendor-specific test data has been replaced with a generic placeholder so the suite is not tied to any specific company or customer context.

## Validation

From the `gartner-analysis` directory:

```bash
python3 -m pytest -q tests
python3 scripts/validate_terminology.py references/analysis-terminology.json
```

Use the skills only with source materials you are authorized to process and redistribute.
