# ccba-qc-core Package Guidance

Deep module for AI quality control, drawing discovery, Quad-View cross-discipline audit, and technical reporting.

- **Public Deep Seams**: `from ccba_qc_core import QCAuditPipeline, AuditReportSummary, QCBatchOrchestrator, DiscoveryEngine, QuadViewAuditEngine, ReporterEngine, PcccMapReduceEngine, SemanticAuditEngine, PcccJurisdictionRouter, PcccProjectSpec, PcccJurisdictionResult, PcccProjectType`
- **Contracts**: Callers must interact via QCAuditPipeline.run_audit(project_dir) or QCBatchOrchestrator.run_batch(...) or PcccJurisdictionRouter.evaluate(spec). Sub-engines adhere to CCBA QC Protocols.
- **Scoped Tests**: pytest packages/ccba-qc-core/tests
