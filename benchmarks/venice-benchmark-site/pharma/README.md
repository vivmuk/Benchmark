# Pharma Benchmark Fixture

Source-backed, executable benchmark fixtures for evaluating LLM performance on pharmaceutical domain tasks.

## Overview

This fixture provides two benchmark tracks:

1. **Drug-Drug Interaction (DDI) Identification** — Given synthetic patient medication lists, the model must identify clinically significant interactions, classify severity, and describe mechanisms.
2. **Regulatory Guideline Comprehension** — Given regulatory scenarios referencing ICH/FDA guidelines, the model must answer compliance questions with specific section citations.

## Key Properties

- **No paid API calls required** — All validation runs against local fixture data
- **Source-backed** — Fixture data derived from publicly available regulatory and reference sources
- **Deterministic validation** — Heuristic scoring with explicit rubric
- **Does not alter existing scored results** — Separate fixture files; additive-only changes to `run_benchmarks.py`

## Files

```
pharma/
├── README.md                          ← this file
├── pharma_benchmark_spec.json         ← master specification
└── fixtures/
    ├── drug_interaction_cases.json    ← 5 DDI test cases
    └── regulatory_qa_cases.json       ← 4 regulatory Q&A cases
```

## Source Provenance

All fixture data is derived from publicly available sources:

| Source | URL | Use |
|--------|-----|-----|
| FDA Drug Interactions Table | https://www.fda.gov/drugs/drug-interactions-labeling/drug-development-and-drug-interactions-table-substrates-inhibitors-and-inducers | DDI mechanisms, CYP substrate/inhibitor data |
| DrugBank | https://go.drugbank.com/ | Drug interaction pairs, mechanisms |
| ICH E6(R2) GCP | https://www.ich.org/page/efficacy-guidelines | Regulatory Q&A scenarios |
| 21 CFR Part 312 | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfcfr/CFRSearch.cfm?CFRPart=312 | IND regulatory requirements |
| ClinicalTrials.gov | https://clinicaltrials.gov/ | Endpoint pattern references |
| WHO ATC Classification | https://www.whocc.no/atc_ddd_index/ | Drug classification |

**Stability note:** All URLs above are canonical entry points maintained by their respective organizations. They have been stable for years and are not expected to change.

## Validation Requirements

### DDI Benchmark

Each model response is validated against:

1. **Interaction detection** — Must identify known pairs (true positives) and not fabricate non-existent ones
2. **Severity classification** — Must match expected severity (Major/Moderate/Minor)
3. **Mechanism accuracy** — Must include correct pharmacological terminology (CYP isoforms, transporters, pharmacodynamic effects)
4. **Clinical action** — Must provide actionable recommendation
5. **Hallucination avoidance** — Must not invent interactions absent from reference sources

### Regulatory Benchmark

Each model response is validated against:

1. **Requirement accuracy** — Must correctly state the regulatory requirement
2. **Citation specificity** — Must reference specific guideline sections (ICH E6 §5.18, 21 CFR §312.23, etc.)
3. **Completeness** — Must address all parts of the question including exceptions
4. **Fabrication avoidance** — Must not invent section numbers or requirements

## Running

### Dry-Run (No API Calls)

```bash
cd /Users/vivgatesai/.openclaw/workspace/benchmarks/venice-benchmark-site
python3 run_benchmarks.py --dry-run --benchmark pharma_drug_interaction
python3 run_benchmarks.py --dry-run --benchmark pharma_regulatory_comprehension
```

### Standalone Validation

The fixture spec includes a `validation` section with explicit rules. A standalone validator can be built against the JSON schema:

```python
import json

with open("pharma/pharma_benchmark_spec.json") as f:
    spec = json.load(f)

for bench in spec["benchmarks"]:
    print(f"Benchmark: {bench['id']}")
    print(f"  Scoring: {bench['scoring']['method']} (total: {bench['scoring']['total']})")
    for rubric in bench["scoring"]["rubric"]:
        print(f"    - {rubric['criterion']}: {rubric['weight']} pts")
```

## Caveats

1. **NOT CLINICAL ADVICE.** These benchmarks evaluate LLM text generation quality. They must not be used for actual clinical decision-making.

2. **Simplified severity.** Drug interaction severity is simplified to Major/Moderate/Minor. Real clinical DDI databases (Lexicomp, Micromedex) use more granular classifications.

3. **Textbook-level pairs only.** Fixture data uses well-established, commonly taught interaction pairs. Rare interactions, dose-dependent effects, and patient-specific factors are not covered.

4. **Regulatory versioning.** References cite publicly available guideline versions as of 2024-2025. Regulations change; specific section numbers should be verified against current editions.

5. **US/EU focus.** Fixture data is derived from US (FDA) and EU (ICH) public regulatory sources. Requirements differ in other jurisdictions.

6. **Heuristic scoring.** Automated scoring is approximate. Manual expert review is recommended for production evaluation.

7. **No patient data.** All medication lists are synthetic.

8. **Does not test clinical judgment.** High scores indicate factual recall and structured reasoning, not clinical competence.

## Integration with run_benchmarks.py

Two benchmark definitions are added to `run_benchmarks.py` as unregistered future entries:

- `pharma_drug_interaction` — DDI identification benchmark
- `pharma_regulatory_comprehension` — Regulatory comprehension benchmark

These are appended to the `BENCHMARKS` list and do not affect existing benchmark execution or scored results.

## License

Fixture data is released under the same terms as the parent benchmark project. Source data references are to publicly available government and international organization publications.
