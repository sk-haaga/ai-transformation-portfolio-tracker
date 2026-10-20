## SAL-08 · AI Sales Proposal Generator — update

*Sales Excellence team · 16 Oct 2026 · status: AMBER*

**TL;DR** — The generator works well internally (first drafts in 20 minutes instead of ~2 days), but we can't let AI-drafted content go to customers until governance approves customer-facing GenAI. The retrieval component we planned to reuse from the Customer Service Copilot is also tied to the copilot's knowledge index, so we inherit its data delay. Business case value is still there but timing is slipping.

**Progress**
- 25 account managers in the B2B pilot. 63 proposals drafted with the tool since August.
- Average time to first draft: ~20 min (baseline ~2 days of AM + bid support time).
- Win rate on pilot proposals is not yet measurable — too few closed deals.
- Built the template library (12 proposal templates, 140 approved content blocks) with Legal and Marketing.
- CRM integration: proposals can now be generated straight from an opportunity record.

**Problems / risks**

*Customer-facing approval.* Legal's position is that proposals drafted by AI must go through the customer-facing GenAI checklist that the AI Governance group (GOV-03) is still writing. Right now every proposal is fully human-rewritten before sending, which removes most of the time saving. Likelihood that this delays us: very high. Impact: medium-high (we can't claim the €1.4M productivity benefit until it's resolved).

*Shared retrieval / knowledge index.* To avoid building our own, we agreed to reuse CRM-01's retrieval service and product knowledge index. That index depends on the data platform product catalogue (DAT-02), which is now December. Our product-spec sections will use the old content until then. Accuracy risk on technical specs in proposals — impact high if a wrong spec ends up in a signed contract. Mitigation: product specs section locked to human-written content blocks until the new index is live.

*Pricing data leakage.* Concern from Finance that the model could mix up pricing from one customer's proposal into another. Mitigation: retrieval scoped per account; red-team test scheduled for November.

*Adoption.* Sales training for the wider rollout (~180 people) is planned with the AI Skills Academy for January but we can't confirm a date yet.

**Milestones**
- Pilot launched — done (Aug)
- Template library complete — done (Oct)
- Red-team / data leakage test — 15 Nov 2026
- Customer-facing approval (GOV-03) — needed by 30 Nov; GOV-03 earliest 11 Nov for checklist, then our review
- Wider rollout to 180 sellers — planned 1 Feb 2027, at risk

About 35% complete overall.

**Ask:** Agreement from steering group that SAL-08 goes through the customer-facing checklist dry run together with CRM-01 rather than separately, to save time.
