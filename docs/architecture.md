# Architecture

## Components

| Layer | Tool | Role |
|---|---|---|
| Data | **Airtable** | System of record for attendees, attendance, events, partners and meetings. Staff work here day to day. |
| Orchestration | **Make.com** | Four polling scenarios that watch Airtable, branch on status and call email providers |
| Email (templated) | **Brevo** | Transactional templates for welcome, follow-up and partner confirmation emails |
| Email (internal) | **Gmail** | Plain alerts to the shared staff inbox |
| Data prep | **Python** | One-time and repeatable cleanup of transcribed sign-in sheets ([data-migration.md](data-migration.md)) |

## Scenario summary

| Scenario | Trigger table / field | Poll | Filter | Sends | Writes back |
|---|---|---|---|---|---|
| [A · Auto-Welcome](scenarios/A-auto-welcome.md) | Attendees / Created Time | 15 min | Type = New Attendee ∧ Email ∧ Outreach ≠ Welcome Sent | Brevo template | Outreach Status = Welcome Sent |
| [B · Post-Event Follow-Up](scenarios/B-post-event-follow-up.md) | Attendance / Created Time | 10 min | Outreach ≠ Follow-up Sent ∧ Email ∧ ¬Import Flag | Brevo template **or** Gmail staff alert | Outreach Status = Follow-up Sent |
| [C · Partner Request Alert](scenarios/C-partner-request-alert.md) | Partners / Created Time | 10 min | (Pending Review ∨ blank) ∧ ¬Alert Sent ∧ ¬Import Flag | Gmail staff alert | Alert Sent = true |
| [D · Partner Approval Confirmation](scenarios/D-partner-approval-confirmation.md) | Partners / Last Modified | 15 min | Approved ∧ ¬Confirmation Sent | Brevo template | Confirmation Sent = true |

## Design principles

### 1. Idempotent by status write-back
Polling triggers can pick up the same record twice. Staff also edit records at unpredictable times. Every scenario ends by writing a marker, and every filter checks that marker before sending, so a scenario can run over and over with no side effects.

### 2. Guard historical data with `Import Flag`
Bulk-loading hundreds of past sign-ins would otherwise look like hundreds of new check-ins. Imported rows get `Import Flag = true`, and Scenarios B and C skip them.

### 3. Humans stay in the loop where it matters
- Partner approval is a manual status change. The automation only handles notifying people.
- Attendees can be flagged `Needs Personal Contact`, which routes them to a staff member instead of an automated email.

### 4. Match before create on a shared base
The Attendees table serves several programs. Imports and future intake match by **email**, then by **normalized name + organization**, before creating a record. Matched records are merged, and their meeting counts are summed.

### 5. Created Time vs. Last Modified triggers
- Scenarios A, B and C react to *new* records, so they watch **Created Time**.
- Scenario D reacts to a *status change* on an existing record, so it watches a **Last Modified Time** field. A Created Time trigger would miss approvals entirely.

## Tradeoffs and known limitations

| Choice | Tradeoff | Mitigation / future |
|---|---|---|
| Polling (10–15 min) instead of webhooks | Up to one interval of delay. Uses Make operations even when nothing has changed | Fine for this volume. Airtable webhooks via Make would make it instant |
| No custom error handlers | A failed module stops that run. Failures only show up in execution history | Add Make error routes that alert the staff inbox |
| No rejection email for partners | Declined partners don't hear back automatically | Add a `Declined` branch to Scenario D |
| No automatic Attendance record on intake form submission | Walk-ins who fill out the intake form aren't logged to an event automatically | Considered but not built: the form has no Event field, so there's nothing to link to. Adding an Event dropdown to the form would make it possible |
| SMS not connected | The `Consent to SMS?` field is collected but unused | Add an SMS provider behind the consent check |
| Template merge tags are case-sensitive | A mismatched `{{ params.NAME }}` renders blank without an error | Param contracts documented in [`brevo/templates/`](../brevo/templates/README.md) |
