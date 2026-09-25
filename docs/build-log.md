# Build Log — Bugs Found & Fixed

Every scenario was debugged against live data, not just configured. This log records the problems that came up and how each was fixed. Most apply to any Airtable + Make + Brevo build.

## Data migration

| Problem | Root cause | Fix |
|---|---|---|
| Linked-record fields (Attendee, Event) wouldn't populate from CSV | Airtable's CSV import can't write linked-record fields directly | Import them as **plain text**, then change the field type to *Link to another record*. Airtable then matches or creates the linked rows |
| `Source` held event names | Mixed up *where someone attended* with *how they found us* | Mapped to acquisition channels (`Online Signup` for form-based files, `Event/Meeting Sign-in` for sheets) |
| Import silently dropped a column | `Interest` in the CSV vs. `Interests` in Airtable | Matched header names exactly to the schema |
| "Interested in Facebook Group" rejected values | Field is a **checkbox**, not a text/select field | Converted values to a boolean |
| Couldn't set a historical "registered on" date | `Created Time` is a read-only system field | Stored real submission dates in a separate date field |
| Wrong defaults would have mislabeled people | `Type` was being defaulted | Left `Type` blank unless the source data stated it |
| Bad rows mixed into the import | 12 rows with no email, 1 malformed email, 6 name spellings that differed between sources | Moved to a separate **migration reference** file for review instead of importing them |
| Same event under two names | Typo in the source file | Normalized the event name before splitting into the Events table |

## Scenario A — Auto-Welcome

| Problem | Root cause | Fix |
|---|---|---|
| Every test run reprocessed the whole existing roster as "new" | Watch Records had **no trigger field set** | Set the trigger field to `Created Time` |
| Duplicate-check matched every new record | *Search Records* found the triggering record itself | Replaced with a filter on the intake form's `Type` field |
| Personalization rendered blank | Params key `Name` didn't match the template's `{{ params.NAME }}` (case-sensitive) | Standardized all params keys to UPPERCASE |
| Record ID, To and Reply-To mapped wrong | Pointed at the wrong upstream module | Re-mapped each to the correct module output |
| An auto-added "Path 2" step was wiping existing `Outreach Status` values | Destructive leftover step | Found in a full audit and removed |

## Scenario B — Post-Event Follow-Up

| Problem | Root cause | Fix |
|---|---|---|
| Lookup failed | Field-name mismatch (`Attendee` vs. `Attendees`) | Used the exact linked field name |
| *Get a Record* errored | Linked field arrives as an **array** of IDs | Switched to *Search Records* with `RECORD_ID() = "{{1.Attendees[1]}}"` |
| Staff alert fired on **every** follow-up | Router route 2 had no working condition | Added an explicit `Outreach Status = Needs Personal Contact` condition |
| Blank Event and Outreach Status in the staff alert | Mapped from the wrong module | Mapped Event straight from the Attendance trigger |
| **Detour:** the trigger was temporarily moved from Attendance to Attendees to make testing both router paths easier | `Event` only exists on Attendance, so three lookup-based workarounds followed and none was fully reliable | **Reverted to the Attendance trigger.** Event became a direct mapping again. Lesson: trigger on the table that owns the data you need |
| 237 migrated historical attendees would have received follow-ups at go-live | No way to tell imported records from live ones | Added an `Import Flag` checkbox to Attendees (matching the one on Partners) and gated both routes on it |
| Follow-up greeted people by first name only | Mapping choice, not a bug | Confirmed with the client as the intended style |

## Scenario C — Partner Request Alert

| Problem | Root cause | Fix |
|---|---|---|
| Filter was always true or always false | The filter compared `Approval Status` to itself | Compared the field against a literal value |
| Real form submissions arrived with a **blank** status | The partner form sets no default for `Approval Status` | Widened the filter to accept blank **or** "Pending Review" |
| The widened filter would also match bulk-imported legacy partners | Legacy rows have a blank status too | Added an `Import Flag` checkbox as a third filter condition |
| Subject-line fix didn't stick | The first edit wasn't saved in Make | Re-applied, then **verified by inspecting the raw saved field value** instead of trusting that it looked right. Confirmed end to end with a blank-status test record |

## Brevo templates

| Problem | Root cause | Fix |
|---|---|---|
| Merge tags didn't resolve | Templates used `{{ NAME }}`, which isn't valid in Brevo. Brevo supports `{{ contact.X }}` (stored contact attributes) or `{{ params.X }}` (values passed per send) | Standardized on `{{ params.X }}`, so the single `Name` field didn't need splitting into First/Last |
| "SMS Opt-In" template had no way to send | No SMS provider connected | Converted it to an email template |

## Platform

| Problem | Fix |
|---|---|
| The Make free plan's active-scenario limit blocked running all four together | Upgraded the plan |
