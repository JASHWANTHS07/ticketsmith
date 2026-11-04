# Add CSV export to the reading list

## Context
Readers want to back up their reading list outside the app.

## Acceptance criteria
- [ ] `export --csv` writes `reading-list.csv` with columns `title,author,added_on`.
- [ ] Exporting an empty list writes only the header row.
- [ ] Titles containing commas are quoted per RFC 4180.

## Out of scope
- Import from CSV.
