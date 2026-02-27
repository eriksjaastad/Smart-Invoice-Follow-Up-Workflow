# Make.com Building Notes

Lessons learned from building and importing SIW scenarios. Reference this before creating or debugging Make.com blueprints.

## Blueprint Import Gotchas

### Module IDs Get Reassigned on Import
Make.com reassigns module IDs when you import a blueprint. If your blueprint has module 2 referencing `{{2.spreadsheetId}}`, it might become module 6 after import. **All cross-module references break.**
- **Fix:** After importing, check every module that references another module's output. Update the IDs to match the new assignments (shown in the box under each module).

### Array Aggregator Source Module Always Unsets
Every time we imported a blueprint with `builtin:BasicAggregator`, the source module was blank — even though `feederModuleId` was set correctly in the JSON.
- **Fix:** After import, always open the aggregator and manually set the Source Module.

### Import Only Works on Empty Scenarios
You can't import a blueprint into a scenario that already has modules — the import button will be grayed out. Either create a new blank scenario or delete all existing modules first.

### Connection IDs Are Account-Specific
Connection IDs like `"__IMTCONN__": 7471828` are tied to your Make.com account. On import, Make.com will prompt you to select your own connections. Known connections:
- Google Sheets: `7471828` (admin@synthinsightlabs.com)
- Gmail: `7471878`
- Google Drive (restricted): `7506553`

### Webhook Hook IDs
Webhook `hook` IDs (e.g., `"hook": 1910258`) are account-specific. On import, you'll need to select or create the webhook. Set to `null` in blueprints for cleaner imports.

## Make.com Formula Pitfalls

### `toJSON()` Does NOT Exist
There is no `toJSON()` function in Make.com. Use `toString()` for simple values, but it flattens objects to `[{object},{object}]` which is useless for nested data.

### `toString()` Flattens Objects
`toString(array)` on an array of objects returns `[{object},{object}]` — not actual JSON. You cannot use it to serialize objects.

### Variable References Are Space-Sensitive
`{{6.A}}` works. `{{6. A}}` (with a space after the period) returns empty string. No error, just silently empty. **Always use the Make.com variable picker** instead of typing references manually to avoid this.

### `map()` Requires an Actual Array
`map(moduleId; "field")` does NOT work if the module outputs a single bundle. The `map()` function needs an array variable, not a module reference number. Error: `'X' is not a valid array`.

## Module-Specific Notes

### Search Rows (Google Sheets)
- With **Table contains headers: No** — the header row becomes a data row. Column values are returned as fields named `A`, `B`, `C`, etc.
- With **Table contains headers: Yes** — headers become field names, but only DATA rows are returned. If the sheet only has headers and no data, you get 0 bundles.
- There is no "Get a Row" module. Use Search Rows with headers=No and limit=1 to read a specific row.

### Array Aggregator vs JSON Aggregator
- **Array Aggregator** (`builtin:BasicAggregator`): Collects bundles into an array, but `toString()` on the result gives `[{object}]`. Not useful for webhook responses returning JSON.
- **Aggregate to JSON** (JSON app): Collects bundles into a proper JSON string. Use this when you need to return JSON in a webhook response. The output field is `.JSON` (for the raw string) or `.json` (wrapped in an object). **Use "JSON string"** in the Webhook Respond body selector to get the raw array.

### Webhook Respond Body
- When using Aggregate to JSON output, select **"JSON string"** (not "JSON bundle") to avoid wrapping in `{"json": "..."}`.
- Content-Type header should be `application/json`.

## Scenario Testing Workflow

1. Click **"Run once"** in Make.com (scenario starts listening)
2. **Immediately** send a curl request from the terminal before the 2-minute timeout
3. Check execution results in Make.com — click each module to see INPUT/OUTPUT
4. The "Response can't be processed when scenario is not executed immediately" warning is harmless — it just means you used "Run once" instead of a live webhook trigger

## Current Scenario Module IDs (as of 2026-02-21)

### SIW - List Sheets (Onboarding Webhook)
| Module | ID | Type |
|--------|----|------|
| Receive Request | 4 | Custom Webhook |
| Search Google Drive | 6 | google-drive:searchForFilesFolders |
| Collect All Sheets | 7 | JSON: Aggregate to JSON |
| Return Sheet List | 8 | Webhook Respond |

### SIW - Validate Sheet
| Module | ID | Type |
|--------|----|------|
| Receive Sheet ID | 1 | Custom Webhook |
| Google Sheets | 6 | google-sheets:searchRows |
| Return Column Names | 3 | Webhook Respond |

### SIW - Create Template (not yet tested)
| Module | ID | Type |
|--------|----|------|
| Receive User ID | ? | Custom Webhook |
| Create Spreadsheet | ? | google-sheets:createSpreadsheet |
| Add Header Row | ? | google-sheets:addRow |
| Return Sheet Info | ? | Webhook Respond |

### SIW - Daily Processing (not yet tested)
- Complex scenario — module IDs TBD after testing

## Canonical Column Schema (LOCKED)

**Source of truth:** `Documents/reference/GOOGLE_SHEET_TEMPLATE.md`

All Make.com scenarios depend on this exact column order. Do NOT change without updating all scenarios.

| Col | Index | Header | Type |
|-----|-------|--------|------|
| A | 0 | Invoice_Number | Text |
| B | 1 | Client_Name | Text |
| C | 2 | Client_Email | Email |
| D | 3 | Amount | Number |
| E | 4 | Due_Date | Date |
| F | 5 | Sent_Date | Date |
| G | 6 | Paid | Boolean (TRUE/FALSE) |
| H | 7 | Last_Stage_Sent | Number (auto) |
| I | 8 | Last_Sent_At | Date (auto) |

## Webhook URLs and Auth

All four webhooks use `x-make-apikey` header for authentication. URLs are stored in `.env` and must match the webhook trigger module in each scenario. **URLs change when you delete and re-import a scenario** — always update `.env` after re-importing.
