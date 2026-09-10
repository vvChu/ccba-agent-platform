# ccba-qc-core

CCBA AI Quality Control Core Engine — Deep Seams for drawing structure discovery, quad-view multi-discipline alignment, semantic schedule clash detection, QCVN 06:2022 PCCC map-reduce auditing, and technical report synthesis.

## Features
- **Discovery**: Analyzes PDF sets, extracts title block regions, and compiles `ProjectBackbone`.
- **Quad-View Alignment**: Renders and aligns 4 disciplines (Arch, KC, MEP, PCCC) per level into synchronized quad-views.
- **Semantic Audit**: Detects schedule, room tag, and specification inconsistencies across disciplines.
- **PCCC Map-Reduce**: Specialized regulatory compliance audit for QCVN 06:2022/BXD and TCVN 3890:2023.
- **Reporter**: Generates Markdown heat maps, coordination matrices, and executive summaries.

## CLI Usage
```bash
# Discovery
ccba-qc discover --input path/to/drawings.pdf --output backbone.json

# Batch Coordination Audit
ccba-qc batch --project-dir ./drawings/ --matrix-csv ./matrix.csv --out-dir ./reports/
```
