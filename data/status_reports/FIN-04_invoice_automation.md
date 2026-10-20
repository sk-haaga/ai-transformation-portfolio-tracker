# FIN-04 — Intelligent Invoice Processing

Status update for Transformation Steering Group · period ending 16.10.2026
Owner: Finance Operations Manager · Status: **GREEN**

## Headline
Production rollout in Finland and Estonia entities complete. Straight-through processing (no human touch) reached 64% of supplier invoices in September vs. 22% before the project. Sweden entity is next.

## Key metrics
- Invoices processed by the solution in Sept: 18,430
- Straight-through processing rate: 64% (target 70% by end of year)
- Extraction field accuracy (sampled): 97.2%
- Average cycle time invoice receipt → approval: 6.1 days (was 11.4)
- Early-payment discounts captured: €38k in Sept (≈ €31k above prior run-rate)

## Done this period
- Go-live for Estonia entity on 5 Oct — smooth, no P1 incidents.
- Added the LLM-based exception classifier: invoices that fail matching are now routed to the right AP clerk with a suggested reason ("PO missing", "price variance", "duplicate suspected"). Clerks say it saves ~5 minutes per exception.
- Supplier master data cleanup completed for Finnish entity.

## Coming next
- Sweden entity go-live planned 16 Nov 2026.
- Integrate with the new Finance domain on the data platform (already migrated, so no blocker) to replace nightly flat-file exports for reporting.
- Business case refresh for steering group in December.

## Milestones
| Milestone | Planned | Forecast | RAG |
|---|---|---|---|
| Finland live | Jun 2026 | Done | G |
| Estonia live | 05 Oct 2026 | Done | G |
| Sweden live | 16 Nov 2026 | 16 Nov 2026 | G |
| Norway live | 25 Jan 2027 | 25 Jan 2027 | A |
| STP rate ≥ 70% | 31 Dec 2026 | 31 Jan 2027 | A |

Completion: approx. 70%.

## Risks
- **Norway e-invoicing format (medium):** Norway entity uses a different e-invoicing access point and the vendor's connector is only in beta. Could push Norway go-live by 4–6 weeks. Vendor has committed to GA in December. Mitigation: fallback to PDF ingestion for Norway first.
- **Vendor contract renewal (low/medium):** the document AI vendor's contract renews in March 2027 with an announced 12% price increase. Procurement negotiating; alternative vendor benchmark ready.
- **Key person dependency (medium):** one solution architect holds most integration knowledge. Documentation sprint scheduled for November.

## Dependencies
- Service accounts for the vendor connector currently use shared credentials; Security has asked us to move to managed identities once the Identity & Access programme (IT-07) delivers the new workload identity pattern. Not blocking go-lives, but it's an open audit point.

No decisions needed from steering group this period.
