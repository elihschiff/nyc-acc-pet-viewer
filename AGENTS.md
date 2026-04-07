# Agents Guidelines

## History Data Backwards Compatibility

`nycacc_history.json` is an append-only dataset that accumulates over time on the `gh-pages` branch. Any changes to the scraper or data schema **must be backwards compatible** with existing records.

Rules:
- **Never rename or remove existing fields** in the JSON. Old records won't have the new schema applied retroactively.
- **New fields must be optional.** The frontend JS must handle records where any `_`-prefixed metadata field is missing (`null`, `undefined`, or absent). Use defensive checks like `if (p._goneDate)` rather than assuming the field exists.
- **Never change the semantics of existing fields.** If `_gone` means "not in the latest API response," don't repurpose it to mean something else.
- **Test with mixed data.** When adding new tracking fields, consider that historical records won't have them. For example, a pet marked `_gone: true` before `_goneDate` was introduced will have `_gone` but no `_goneDate` — the UI must handle this gracefully.
- **The pet ID (string) is the stable key.** Don't change how IDs are stored or compared.
