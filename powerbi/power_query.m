// Power Query M script for loading Superstore Star Schema CSVs
let
    SourceDir = "D:\github\go to offer\data-analyst\superstore-analytics\powerbi\",
    LoadFact = Csv.Document(File.Contents(SourceDir & "fact_sales.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedFact = Table.PromoteHeaders(LoadFact, [PromoteAllScalars=true]),
    TypedFact = Table.TransformColumnTypes(PromotedFact, {
        {"row_id", Int64.Type},
        {"order_id", type text},
        {"order_date", type date},
        {"customer_id", type text},
        {"product_id", type text},
        {"location_id", type text},
        {"ship_mode", type text},
        {"ship_days", Int64.Type},
        {"sales", type number},
        {"quantity", Int64.Type},
        {"discount", type number},
        {"profit", type number},
        {"cogs", type number},
        {"undiscounted_sales", type number},
        {"discount_amount", type number},
        {"profit_margin", type number},
        {"is_loss", type logical},
        {"is_toxic_discount", type logical},
        {"discount_tier", type text},
        {"is_returned", type logical}
    })
in
    TypedFact
