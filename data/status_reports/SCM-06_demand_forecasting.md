# Demand Forecasting with ML — SCM-06

**Status report, period ending 16 October 2026**
Product owner: Supply Chain Planning Director · Delivery lead: Analytics CoE

### RAG: AMBER

Proof of value finished in August with good results: on the pilot category (power tools, ~1,900 SKUs), the gradient-boosted model reduced forecast error (weighted MAPE) from 38% to 27% against the current statistical tool. Estimated inventory reduction potential of €2.1–2.6M across the full range once scaled.

Industrialisation phase started in September. The scaling plan assumed we would train on 3 years of sales and inventory history from the new data platform, plus a clean product hierarchy.

### What happened this period

- MLOps pipeline built (training, registry, batch scoring) in the analytics workspace. Tested end-to-end on pilot data.
- Planner UI prototype reviewed with 6 planners. Main feedback: they want to see *why* the forecast changed (drivers), not just the number. Explainability view added to backlog.
- **Blocked on data:** the supply chain history tables on the lakehouse were due 16 Oct, now 6 Nov. The product hierarchy / SKU mapping comes from the product catalogue domain, which the Data Platform team now forecasts for early December. We cannot scale beyond the pilot category with the current hand-curated mapping file.

### Impact

If the catalogue domain lands in December, we lose about 6 weeks, and the planned go-live for the spring/summer season planning cycle (planners start building S/S 2027 plans in mid-January) is at risk. Missing that cycle means waiting until the autumn/winter cycle in mid-2027, deferring most of the inventory benefit by ~6 months. That's roughly €1M of working-capital benefit pushed out.

### Milestones

- Proof of value — done (Aug 2026)
- MLOps pipeline — done (Oct 2026)
- Full-range training data available — planned 16 Oct → forecast 4 Dec 2026 (dependent on DAT-02)
- Model validated on full range — planned 13 Nov → forecast 18 Dec 2026
- Planner go-live for S/S 2027 cycle — planned 11 Jan 2027 → forecast at risk
- Legacy forecasting tool retired — planned Jun 2027

Approx. 40% complete.

### Risks

1. **Data dependency on DAT-02** — HIGH impact, HIGH likelihood. Catalogue slip directly delays scaling. Mitigation: extend hand-curated mapping to 3 more categories (covers ~45% of revenue) as an interim; ask DAT-02 to prioritise SKU mapping table ahead of the rest of the catalogue domain.
2. **Planner trust / adoption** — MEDIUM. Planners override forecasts heavily today. Without explainability, they may ignore the model. Mitigation: explainability view, co-design sessions, champions from AI Skills Academy network.
3. **Data science capacity** — LOW/MEDIUM. One of two data scientists on parental leave from December.

### Asks
- Steering group to support prioritising the SKU mapping table within DAT-02's catalogue work.
