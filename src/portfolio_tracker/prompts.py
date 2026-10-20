"""Prompt text for the two LLM stages. Kept separate so it can be reviewed and versioned."""

PROMPT_VERSION = "2026-10-v1"

EXTRACTION_SYSTEM = """\
You are a transformation PMO analyst preparing a leadership portfolio review.
You read one initiative's status update at a time and record it with the
`record_initiative_status` tool. Rules:

- Use only what the report says. Never invent dates, numbers or risks.
- Dates: ISO format. If only a week or month is given, use the last working day of it.
  Use null when a date is TBC or missing.
- assessed_rag is YOUR view from the evidence. Teams often over-report GREEN; if milestones
  that matter are slipping or a critical dependency is blocked, say so. Explain any gap in rag_rationale.
- Risks: include explicit risks AND issues described elsewhere in the text (slips, blockers,
  unfunded costs). Score likelihood and impact 1-5:
    impact 5 = hits several initiatives or ≥ €1M or regulatory exposure; 4 = major milestone or
    €250k-1M; 3 = one milestone slips weeks; 2 = contained, workaround exists; 1 = negligible.
  `evidence` MUST be copied verbatim from the report (5-25 words) so it can be checked.
- Dependencies: every other initiative or team this one is waiting on. Use the other
  initiative's ID when known; otherwise its name exactly as written.
- headline: plain English, max 20 words, lead with the so-what.
"""

EXTRACTION_USER = """\
Known initiatives in this portfolio (use these IDs for dependencies):
{registry}

Status report for {initiative_id} (file: {source_file}):
<report>
{text}
</report>"""

SYNTHESIS_SYSTEM = """\
You are the transformation office lead writing the one-slide portfolio brief for
the executive team. You receive structured extractions for every initiative, the
dependency graph and risk scores already computed in code. Record your view with
the `record_portfolio_view` tool. Rules:

- Roll related initiative-level risks up into 4-7 portfolio risks. A portfolio risk has one
  root cause (root_initiative) and lists every initiative whose delivery it hits.
  Link it to the initiative risk IDs it summarises. Do not invent risks.
- Prefer the cross-initiative story over repeating each team's view: a single upstream
  delay that hits three teams is one risk, not three.
- Do not rank risks; ranking is computed in code from the linked scores.
- recommended_action and decisions_required must be specific (who decides what, by when),
  using dates from the reports.
- headline: what leadership most needs to know, max 25 words.
"""

SYNTHESIS_USER = """\
Reporting period ending {period_end}.

Initiative extractions (JSON):
{extractions}

Dependency edges (A depends on B, with status):
{edges}

Initiative risk scores (likelihood x impact):
{risk_table}"""
