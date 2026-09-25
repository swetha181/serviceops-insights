// Create a blank Power Query called Tickets; paste this in Advanced Editor.
// Change only CsvPath to your generated tickets_clean.csv on Windows.
let
    CsvPath = "C:\ServiceOps\serviceops-insights\build\tickets_clean.csv",
    Source = Csv.Document(File.Contents(CsvPath), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    BlankToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, {"resolved_at", "resolution_hours"}),
    Typed = Table.TransformColumnTypes(BlankToNull, {
        {"ticket_id", type text}, {"department", type text}, {"category", type text},
        {"priority", type text}, {"status", type text}, {"sla_state", type text},
        {"created_at", type datetimezone}, {"resolved_at", type datetimezone},
        {"snapshot_at", type datetimezone}, {"created_on", type date},
        {"sla_hours", Int64.Type}, {"elapsed_hours", type number},
        {"resolution_hours", type number}, {"is_open", Int64.Type}
    }, "en-US"),
    // Power BI model timestamps are stored as UTC without a zone component.
    UTC = Table.TransformColumns(Typed, {
        {"created_at", each DateTimeZone.RemoveZone(DateTimeZone.ToUtc(_)), type datetime},
        {"resolved_at", each if _ = null then null else DateTimeZone.RemoveZone(DateTimeZone.ToUtc(_)), type nullable datetime},
        {"snapshot_at", each DateTimeZone.RemoveZone(DateTimeZone.ToUtc(_)), type datetime}
    })
in
    UTC
