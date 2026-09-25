# Make.com Automation Scenarios

These specifications document the four Make.com scenarios for the Attendee &
Network Hub. All schedules are polling schedules and should be confirmed in
Make before go-live.

## Scenario A: Welcome Email Automation

- **Make scenario:** [Scenario A](https://us2.make.com/2731964/scenarios/6302872/edit)
- **Schedule:** Every 15 minutes
- **Trigger:** Airtable **Watch Records**
  - Base: `Attendee & Network Hub`
  - Table: `Attendees`
  - Trigger field: `Created Time`
  - Label field: `Email`
  - Limit: `10`
- **Filter:** `Type = "New Attendee"` and `Email` exists and
  `Outreach Status != "Welcome Sent"`.
- **Actions:**
  1. Brevo **Send an Email**, template ID `4`, to the trigger email.
     `NAME` is mapped from the attendee name/first name. Sender and Reply To
     are the static Georgia Faith and Recovery Collaboration address:
     `gafaithandrecovery@gmail.com`.
  2. Airtable **Update a Record**, setting `Outreach Status` to
     `"Welcome Sent"`.
- **Status fields:** `Outreach Status` on `Attendees`.
- **Error behavior:** No custom error handling. A failed module halts that
  run; use Make execution history to investigate failures.

## Scenario B: Post-Event Follow-Up

- **Make scenario:** [Scenario B](https://us2.make.com/2731964/scenarios/6305387/edit)
- **Schedule:** Every 10 minutes
- **Trigger:** Airtable **Watch Records**
  - Table: `Attendance`
  - Trigger field: `Created Time`
  - Label field: `Attendees`
  - Limit: `10`
- **Lookup:** Airtable **Search Records** on `Attendees` using:
  `RECORD_ID() = "{{1.Attendees[1]}}"`. This resolves the linked attendee's
  name, email, phone, outreach status, and import flag.
- **Pre-router filter:** Looked-up `Outreach Status != "Follow-up Sent"`.
- **Router paths:** Both paths require an email and `Import Flag` not true.
  - **Standard:** Looked-up `Outreach Status != "Needs Personal Contact"`.
    Brevo **Send an Email**, template ID `7`, to the looked-up email with
    `NAME` mapped from the looked-up full name (first-name-only by design).
    Then update the attendee's `Outreach Status` to `"Follow-up Sent"`.
  - **Needs Personal Contact:** Looked-up `Outreach Status =
    "Needs Personal Contact"`. Gmail sends staff an email at
    `gafaithandrecovery@gmail.com` containing the attendee name, email, phone,
    outreach status, and event. The event is mapped directly from the trigger's
    `Event` field.
- **Status fields:** `Outreach Status` and `Import Flag` on `Attendees`.
- **Error behavior:** No custom error handling. A failed module halts that
  run; use Make execution history to investigate failures.

## Scenario C: Partner Request Alert

- **Make scenario:** [Scenario C](https://us2.make.com/2731964/scenarios/6305413/edit)
- **Schedule:** Every 10 minutes
- **Trigger:** Airtable **Watch Records**
  - Table: `Partners`
  - Trigger field: `Created Time`
  - Label field: `Organization Name`
  - Limit: `10`
- **Filter:** `Approval Status = "Pending Review"` or `Approval Status` is
  empty, and `Alert Sent` is empty/false, and `Import Flag` is empty/false.
  The empty approval-status case is intentional and should remain covered by
  tests.
- **Actions:**
  1. Gmail sends an email to `gafaithandrecovery@gmail.com` with subject
     `New partner request needs review: [Organization Name]`. The body
     includes organization name, contact name, contact email, category, and
     location.
  2. Airtable **Update a Record**, setting `Alert Sent` to `true`.
- **Status fields:** `Approval Status`, `Alert Sent`, and `Import Flag` on
  `Partners`.
- **Error behavior:** No custom error handling. A failed module halts that
  run; use Make execution history to investigate failures.
- **Import note:** Set `Import Flag` to true for bulk-imported historical
  partner records so they do not trigger alerts.

## Scenario D: Partner Approval Confirmation

- **Make scenario:** [Scenario D](https://us2.make.com/2731964/scenarios/6305446/edit)
- **Schedule:** Every 15 minutes
- **Trigger:** Airtable **Watch Records**
  - Table: `Partners`
  - Trigger field: `Last Modified` (`Last Modified Time` field type)
  - Limit: `10`
- **Filter:** `Approval Status = "Approved"` and `Confirmation Sent` is
  empty/false.
- **Actions:**
  1. Brevo **Send an Email**, template ID `6`, to the trigger's contact email.
     `CONTACT_NAME` and `ORGANIZATION_NAME` are mapped from the partner record.
     Sender and Reply To use the static configured address.
  2. Airtable **Update a Record**, setting `Confirmation Sent` to `true`.
- **Status fields:** `Approval Status` and `Confirmation Sent` on `Partners`.
- **Error behavior:** No custom error handling. A failed module halts that
  run; use Make execution history to investigate failures.

## Operational invariants

1. Each scenario writes its send/alert status after the outbound module
   succeeds. These fields are idempotency keys that prevent duplicate sends on
   later polling cycles.
2. Import flags must be applied to historical bulk data before enabling the
   scenarios.
3. Scenario D must use a `Last Modified Time` trigger, not `Created Time`, so
   approval changes on existing partner records are detected.
4. Before go-live, verify the active polling intervals, Airtable base/table
   mappings, Brevo template IDs, and static sender/reply-to configuration in
   Make.
