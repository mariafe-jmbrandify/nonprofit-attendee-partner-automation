# Data Migration

Historical data came from two kinds of source, and each needed its own pipeline.

## 1. Spreadsheet sources (registrations + typed sign-ins)

Six files, one per event, from online registration forms and typed-up sign-in sheets.

```
6 source files ──► combine ──► normalize ──► dedup by email ──► split
     279 rows                                                    │
                                    ┌────────────────────────────┼───────────────────────┐
                                    ▼                            ▼                       ▼
                          Attendees_import.csv          Events_import.csv      Attendance_import.csv
                             237 people                    6 events               249 visits
                                    │
                                    └──► migration_reference.csv (19 rows set aside for review)
```

**Import order matters:** Events → Attendees → Attendance. Attendance's linked fields are imported as plain text and then converted to *Link to another record* (see [build-log.md](build-log.md)). A **10-record test batch** covering a range of cases was imported and checked before the full load.

## 2. Scanned handwritten sign-in sheets

34 scanned pages covering 2023–2026.

1. **Transcription:** an AI vision model reads each page and returns one row per sign-in line. It includes a confidence note wherever the handwriting is unclear.
2. **Cleanup + dedup:** [`scripts/dedupe_contacts.py`](../scripts/dedupe_contacts.py) merges the lines into unique contacts.
3. **Human review:** rows marked `Needs Review = Yes` are checked against the original scan.
4. **Match against the live base:** each contact is matched to an existing Attendee or marked as new (the shared base serves several programs).
5. **Import:** new rows get `Status = Active` and `Import Flag = true`. Consent and interest fields are left blank.

Result: **375 sign-in lines → 143 unique contacts**, with 53 flagged for review.

## Matching & merge rules

| Step | Rule |
|---|---|
| Primary key | `Email`, lowercased and trimmed |
| Fallback key | normalized `Full Name` + normalized `Organization` (only when there's no email) |
| Name-only rows | kept as separate contacts and flagged. They are **never** auto-merged on first name alone |
| Merge | Emails that differ go to `Alternate Emails`. A changed organization goes to `Past Organizations`. The longest version of the name wins |
| Meeting count | number of **distinct** meeting dates across all merged rows (summed across duplicates, with no double-counting) |
| First / Last meeting | min / max of the merged dates |
| Flags | no email · first name only · uncertain transcription · malformed email |

### Matching against the existing Airtable table

Given an export of the live Attendees table (`--existing`), each clean contact is labeled:

- `match:email`: an existing row has the same email
- `match:name+org`: no email match, but the name and organization match
- `new`: no match, so a new record is created

Matched contacts **update** the existing record. They never create a duplicate.
