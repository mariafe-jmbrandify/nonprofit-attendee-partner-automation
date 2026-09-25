# Make.com Blueprints

Exported scenario blueprints go here, **sanitized**, as `*.sanitized.json`. `.gitignore` blocks every other `.json` file in this folder.

## Export

Open the scenario in Make, click **⋯ → Export Blueprint**, and save the file as for example `scenario-a-auto-welcome.json`.

## Sanitize before committing

Blueprints can contain account-specific values. Replace these before you rename the file to `*.sanitized.json`:

| Find | Replace with |
|---|---|
| Airtable base ID (`app…`) and table IDs (`tbl…`) | `appXXXXXXXXXXXXXX`, `tblXXXXXXXXXXXXXX` |
| `__IMTCONN__` connection IDs | `0` |
| Brevo template IDs | `0` |
| Sender, reply-to and staff alert addresses | `staff@example.org` |
| Organization name in subjects or bodies | `Your Organization` |

Check before you commit:

```bash
grep -nE 'app[A-Za-z0-9]{14}|tbl[A-Za-z0-9]{14}|@(gmail|yahoo|outlook)\.com|__IMTCONN__": [1-9]' make/blueprints/*.sanitized.json
```

The command should print nothing.

## Import

In Make, go to **Create a new scenario → ⋯ → Import Blueprint**. Then reconnect Airtable, Brevo and Gmail, and set the IDs from `.env.example`.
