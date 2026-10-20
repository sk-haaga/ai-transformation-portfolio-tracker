# Weekly Status Report — GenAI Customer Service Copilot

**Initiative ID:** CRM-01
**Sponsor:** Director of Customer Operations
**Programme lead:** Customer Ops Transformation Lead
**Reporting period:** w/e 16 Oct 2026
**Overall status:** AMBER (was GREEN)

## Summary

Pilot with 40 agents in the Tampere contact centre continued this fortnight. Agents are using the copilot for roughly 55% of eligible tickets, up from 38%. Average handle time in the pilot group is down 11% vs. the control group, which is below the 15% target in the business case but trending the right way. Customer satisfaction is flat (no degradation).

Status has moved to Amber because the wider rollout (wave 2, ~350 agents) is now unlikely to start on 2 Nov as planned. Two things are holding it up:

1. The knowledge base the copilot retrieves from still points at the legacy SharePoint export. The new product knowledge index is supposed to come off the lakehouse (Data Platform team), and their migration of the product catalogue domain has slipped. Until that lands we would be scaling a copilot that answers from stale content.
2. Responsible AI sign-off. The AI Governance board has not yet published the final approval checklist for customer-facing GenAI use cases. We submitted our DPIA and model card in September but cannot get formal go-live approval until the checklist exists.

We also still need SSO / conditional access for the copilot web app before it can be opened to the outsourced partner agents in Tallinn — dependent on the Identity programme.

## Progress this period

- Prompt library v3 deployed; hallucination rate in weekly sample audit dropped from 4.1% to 2.3% of responses.
- Feedback button added to agent UI; 1,240 ratings captured, 81% thumbs up.
- Finalised wave 2 training plan with the AI Skills Academy team (sessions booked for weeks 45–46 but these will need to move if go-live slips).
- Cost per 1,000 tickets running at €18, inside the €25 budget assumption.

## Milestones

| Milestone | Baseline | Forecast | Status |
|---|---|---|---|
| Pilot complete (40 agents) | 15 Oct 2026 | 30 Oct 2026 | Extended 2 weeks |
| Responsible AI approval | 20 Oct 2026 | TBC | At risk |
| Wave 2 go-live (350 agents) | 2 Nov 2026 | 7 Dec 2026 | At risk |
| Partner agents (Tallinn) live | 11 Jan 2027 | 1 Feb 2027 | At risk |

Overall completion estimate: 45%.

## Risks & issues

- **Stale knowledge content (HIGH).** If wave 2 goes live on the legacy SharePoint export, wrong answers on pricing and warranty terms are likely. Impact: customer complaints, potential regulatory exposure on consumer terms. Likelihood high if Data Platform slips further. Mitigation: hold wave 2 until the product index is live; interim manual refresh of top 200 articles (owner: Knowledge Manager).
- **Governance approval delay (HIGH).** No checklist = no approval = no go-live. Escalated to sponsor. Mitigation: offered our use case as the test case for the draft checklist.
- **Agent adoption plateau (MEDIUM).** Some senior agents ignore suggestions. Mitigation: champions network, coaching via Skills Academy.
- **Vendor token pricing change (LOW).** Model provider has announced pricing changes for 2027; our assumption may be ~10% light. Monitoring.

## Decisions / asks for leadership

- Confirm that wave 2 should wait for the new knowledge index rather than go live on legacy content.
- Push AI Governance board for a date on the customer-facing GenAI checklist.
