# Troubleshooting Cheat Sheet

## "An email didn't send"
Check these in order:
1. **Email on file?** If not, nothing sends. That's by design.
2. **Brevo template Active?** Inactive templates can't be sent.
3. **Brevo contact status:** unsubscribed, bounced or blocked addresses are always skipped by Brevo.
4. **Already marked?** If `Outreach Status`, `Alert Sent` or `Confirmation Sent` is already set, skipping the record is correct.
5. **Attendees:** is `Type` exactly *New Attendee*? The welcome email only goes to that value.
6. **Import Flag** set? Imported records are skipped on purpose.

## "The automation didn't run"
1. Is the scenario toggled **Active** in Make?
2. Did the record **exactly** match the filter (exact Type, Approval Status and Outreach Status values)?
3. Look for red modules in the execution history.
4. These scenarios poll, so a delay of up to **10–15 minutes** is normal.

## "Duplicate emails"
- Is a native Airtable automation doing the same job as the Make scenario?
- Was a status field cleared or reset by hand? A cleared record looks new again.

## "Blank name or field in an email"
- **Merge tag mismatch:** `{{ params.NAME }}` has to match the Make params key exactly, including capitalization.
- **Wrong upstream module:** the field is mapped from the trigger when it should come from the lookup, or the other way around. Fix this in Make. It can't be fixed from Airtable.

## "A new partner request didn't send an alert"
Check `Approval Status` and `Import Flag` on the record. The filter accepts *Pending Review* or blank, as long as it isn't flagged as an import.

## "Someone's attendance history looks wrong"
Check the **Attendance** tab directly. Attendance rows, not the Attendee record, are where each visit is stored.

## "SMS not sending"
There's no SMS provider connected. Once one is added, check `Consent to SMS?` and the phone number format.

## Where to look
| Tool | Where |
|---|---|
| Make | Scenario → **History**: every run, with the data that passed through each module |
| Brevo | **Transactional** logs: delivery and bounce status |
| Airtable | Record **activity history** (clock icon): field changes over time |

If a fix isn't obvious, **stop and ask** before editing a working scenario.
