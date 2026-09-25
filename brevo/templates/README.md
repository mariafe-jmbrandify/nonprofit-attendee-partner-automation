# Brevo Templates: Param Contracts

All templates use **`{{ params.KEY }}`** personalization. Make passes the values with each send.

> Keys are **case-sensitive**. If the Make params key doesn't exactly match the template tag (`Name` vs. `NAME`), the tag renders **blank** and no error is raised.

| Template | Env var | Used by | Params |
|---|---|---|---|
| Welcome Email | `BREVO_TEMPLATE_WELCOME` | Scenario A | `NAME` |
| Follow-Up Email | `BREVO_TEMPLATE_FOLLOW_UP` | Scenario B | `NAME` (optional `EVENT` for the subject-line variant that names the event) |
| Partner Approval Confirmation | `BREVO_TEMPLATE_PARTNER_APPROVAL` | Scenario D | `CONTACT_NAME`, `ORGANIZATION_NAME` |
| Follow-Up Confirmation (formerly SMS Opt-In) | none | not wired | none. Converted to email because no SMS provider is connected |

## Why `params` and not `contact` attributes

Brevo offers two personalization systems:

- `{{ contact.FIRSTNAME }}` reads attributes stored on the Brevo contact.
- `{{ params.NAME }}` reads values passed in the API call.

Airtable stores a single `Name` field, and Airtable remains the system of record. Using `params` avoids copying contacts into Brevo or splitting names into First/Last.

## Go-live check

Templates must be set to **Active** in Brevo. An inactive template can't be selected in Make and can't be sent.
