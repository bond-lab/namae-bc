
Things that are slow, I should calculate, and then write as json.

Default for a table is:

table_name
```
{
    "headers": ["Product", "Price", "Quantity", "Total"],
    "rows": [
        ["Widget A", "1250.50", "100", "125050"],
        ["Widget B", "2400", "75", "180000"],
        ["Widget C", "500.25", "200", "100050"]
    ],
    "caption": "Sales Data - Q1 2024"
}
```

If the table is of the form

```
{
    "headers": ["Year", "Gender", "Value"],
    "rows": [
        ["Widget A", "1250.50", "100", "125050"],
        ["Widget B", "2400", "75", "180000"],
        ["Widget C", "500.25", "200", "100050"]
    ],
    "caption": "Sales Data - Q1 2024"
    "trends": {
    'F':{slope, intercept, r2, pvalue},	
    'M':{slope, intercept, r2, pvalue},
    }
    "difference": {"test", m-mean, f-mean, value, p-value}
}
```

