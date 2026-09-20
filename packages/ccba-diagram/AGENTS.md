# ccba-diagram Package Guidance

Deterministic layout engines, topology analysis, and visual ergonomics for Excalidraw diagrams.

- **Public Deep Seams**: `from ccba_diagram import apply_smart_layout, apply_sugiyama_layout, apply_wheel_layout, apply_matrix_layout, apply_tree_layout, apply_radial_layout, apply_concentric_layout, apply_value_chain_layout, apply_cycle_layout, DiagramTheme, generate_markdown_spec_table`.
- **CLI Commands**: `ccba-diagram layout <input.json> -o <output.json> [--engine auto|sugiyama|wheel|matrix|tree|radial|concentric|value_chain|cycle]` and `ccba-diagram spec-table <input.json>`.
- **Contracts**: All layout operations modify elements in-place and return boolean status. Layouts must strictly adhere to 16:9 canvas dimensions ($W \le 1150\text{px}$) and compute safe arrow endpoints via shape boundary clipping.
- **Scoped Tests**: `pytest packages/ccba-diagram/tests`
