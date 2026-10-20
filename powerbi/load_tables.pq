// Power Query (M) to load the tracker's CSV exports.
//
// 1. In Power BI Desktop: Home > Transform data > New Source > Blank Query.
// 2. Create a text parameter named OutputFolder pointing at the exported folder, e.g.
//      C:\repos\ai-transformation-portfolio-tracker\output\powerbi\
//    (keep the trailing backslash).
// 3. For each table below, create a Blank Query, open Advanced Editor, paste the
//    matching block and name the query exactly as the comment says.

// ---------- query: dim_initiative
let
    Source = Csv.Document(File.Contents(OutputFolder & "dim_initiative.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"initiative_id", type text}, {"name", type text}, {"short_name", type text}, {"theme", type text},
        {"owner", type text}, {"period_end", type date}, {"reported_rag", type text}, {"assessed_rag", type text},
        {"rag_sort", Int64.Type}, {"rag_changed", type logical}, {"rag_rationale", type text},
        {"percent_complete", Int64.Type}, {"headline", type text}, {"risk_count", Int64.Type},
        {"max_risk_score", Int64.Type}, {"direct_dependents", Int64.Type}, {"transitive_dependents", Int64.Type},
        {"source_file", type text}})
in
    Typed

// ---------- query: fact_milestone
let
    Source = Csv.Document(File.Contents(OutputFolder & "fact_milestone.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Blanks = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, {"baseline_date", "forecast_date", "plot_date", "slip_days"}),
    Typed = Table.TransformColumnTypes(Blanks, {
        {"milestone_key", type text}, {"initiative_id", type text}, {"milestone", type text},
        {"baseline_date", type date}, {"forecast_date", type date}, {"plot_date", type date},
        {"slip_days", Int64.Type}, {"status", type text}, {"is_done", type logical}})
in
    Typed

// ---------- query: fact_risk
let
    Source = Csv.Document(File.Contents(OutputFolder & "fact_risk.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"risk_id", type text}, {"initiative_id", type text}, {"title", type text}, {"description", type text},
        {"category", type text}, {"likelihood", Int64.Type}, {"impact", Int64.Type}, {"score", Int64.Type},
        {"direct_dependents", Int64.Type}, {"portfolio_score", type number}, {"mitigation", type text},
        {"evidence", type text}, {"grounded", type logical}})
in
    Typed

// ---------- query: fact_dependency
let
    Source = Csv.Document(File.Contents(OutputFolder & "fact_dependency.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Blanks = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, {"needed_by", "to_initiative_id"}),
    Typed = Table.TransformColumnTypes(Blanks, {
        {"from_initiative_id", type text}, {"to_initiative_id", type text}, {"mention", type text},
        {"what", type text}, {"status", type text}, {"needed_by", type date}, {"is_live", type logical}})
in
    Typed

// ---------- query: portfolio_risk
let
    Source = Csv.Document(File.Contents(OutputFolder & "portfolio_risk.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"rank", Int64.Type}, {"title", type text}, {"root_initiative_id", type text},
        {"affected_initiatives", type text}, {"affected_count", Int64.Type}, {"base_score", Int64.Type},
        {"portfolio_score", type number}, {"impact_statement", type text}, {"recommended_action", type text},
        {"linked_risk_ids", type text}})
in
    Typed

// ---------- query: bridge_portfolio_risk
let
    Source = Csv.Document(File.Contents(OutputFolder & "bridge_portfolio_risk.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"rank", Int64.Type}, {"initiative_id", type text}})
in
    Typed

// ---------- query: run_metadata
let
    Source = Csv.Document(File.Contents(OutputFolder & "run_metadata.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"period_end", type date}, {"source_reports", Int64.Type}, {"source_pages", Int64.Type},
        {"source_words", Int64.Type}, {"initiatives", Int64.Type}, {"risks", Int64.Type}, {"warnings", Int64.Type}})
in
    Typed
