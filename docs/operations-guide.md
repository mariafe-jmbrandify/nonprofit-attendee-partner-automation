# Operations Guide

A plain-language guide for staff who run the Attendee & Network Hub. Staff work
in Airtable while Make.com runs the automations in the background.

## Before enabling automation

1. Confirm Airtable, Make, Brevo, and Gmail connections.
2. Set `Import Flag` on historical attendee and partner imports so old records
   do not generate outreach or alerts.
3. Confirm the documented schedules: welcome and approval every 15 minutes;
   follow-up and partner alerts every 10 minutes.
4. Test one record for each scenario before enabling live processing.

## 1. Approve or reject a partner request

1. Open **Partners**. New requests arrive with `Approval Status` = *Pending
   Review* or blank, and staff receive an alert.
2. To approve, set `Approval Status` to **Approved**. A confirmation email goes
   out within about 15 minutes.
3. To reject, leave the status as-is or add a note in `Review Notes`. No
   automatic rejection email is sent.

Move a record to Approved once. `Confirmation Sent` prevents duplicate emails,
but switching the status back and forth makes the history harder to read.

![Annotated Partner Request Alert scenario](images/scenario-c-partner-alert.png)

![Annotated Partner Approval Confirmation scenario](images/scenario-d-partner-approval.png)

## 2. Flag an attendee for personal follow-up

Set `Outreach Status` to **Needs Personal Contact**. The next check-in sends
staff an alert with the attendee's name, email, phone, and event; no automated
email goes to the attendee.

![Annotated Post-Event Follow-Up scenario](images/scenario-b-followup.png)

## 3. Add a walk-in and send a welcome

1. Open **Attendees → Add record**. Fill in at least Name, Email, and **Type**.
2. Set `Type` to **New Attendee** if the person should receive the welcome
   email.
3. Log the visit in **Attendance** by linking the person and event.

The welcome scenario watches new attendee records, sends the welcome message,
and writes `Outreach Status = Welcome Sent`.

![Annotated Auto-Welcome scenario](images/scenario-a-welcome.png)

## 4. View attendee history

- **Attendee → linked Attendance:** every event attended, with dates and notes.
- **Event → `Attendee Count`:** filled in automatically.
- An Attendance row with an empty `Attendees` link will not appear in a
  person's history.

## 5. Bulk import from CSV or Excel

Use **Attendees → More (…) → Import data → CSV file** and verify the column
mapping. Imported records only receive welcome emails when `Type = New
Attendee`; historical rows should have `Import Flag = true` so they do not
trigger follow-ups.

## 6. Status reference

See [data-model.md — Status fields](data-model.md#status-fields-automation-contracts).
The status fields are idempotency guards. Check them before sending any manual
message.

## Troubleshooting

1. Open the relevant Make scenario and review **History** and **Incomplete
   Executions**.
2. Confirm the record meets every filter, has a valid email, and is not marked
   as an import.
3. Confirm the corresponding status is not already set:
   `Welcome Sent`, `Follow-up Sent`, `Alert Sent`, or `Confirmation Sent`.
4. Correct the Airtable record and allow the next polling interval to run.

Make uses default error behavior: a failed module halts that run, and these
scenarios have no custom error handler. If an outbound email succeeded but the
status update failed, use Make history to determine whether a retry could
duplicate the message before sending manually.

## Safe handoff checklist

- [ ] Test one welcome record.
- [ ] Test one standard and one personal-contact follow-up.
- [ ] Test a partner request with blank approval status.
- [ ] Test approval on an existing partner record.
- [ ] Verify each status was written back.
- [ ] Remove or mark test records according to the data policy.
- [ ] Record final schedules and connection owner.
