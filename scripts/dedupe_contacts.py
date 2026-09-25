#!/usr/bin/env python3
"""Merge transcribed sign-in lines into unique contacts.

Input: a CSV with one row per sign-in line. Columns (case-insensitive):
    name, email, phone, organization, meeting_date, transcription_note

Output: one row per unique contact, ready for review and Airtable import.

Matching rules (see docs/data-migration.md):
    1. Email (lowercased, trimmed) is the primary key.
    2. With no email, fall back to normalized full name + organization.
    3. Rows with only a first name are never auto-merged. They are flagged.

Optionally, --existing <attendees_export.csv> labels each contact as
match:email, match:name+org, or new against the live Airtable table.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)

OUTPUT_FIELDS = [
    "Full Name", "First Name", "Last Name", "Email", "Alternate Emails",
    "Phone", "Organization", "Past Organizations", "Meeting Count",
    "First Meeting", "Last Meeting", "Meeting Dates Attended",
    "Needs Review", "Review Notes", "Airtable Match",
]


def norm_text(value: str | None) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    value = (value or "").lower()
    value = re.sub(r"[^\w\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def norm_email(value: str | None) -> str:
    return (value or "").strip().lower()


def norm_phone(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return (value or "").strip()


def split_name(full: str) -> tuple[str, str]:
    parts = full.split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


@dataclass
class Contact:
    full_name: str = ""
    email: str = ""
    alt_emails: list[str] = field(default_factory=list)
    phone: str = ""
    organization: str = ""
    past_orgs: list[str] = field(default_factory=list)
    dates: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    # ---- merging -------------------------------------------------------
    def absorb(self, row: dict[str, str]) -> None:
        name = row.get("name", "").strip()
        if len(name) > len(self.full_name):
            self.full_name = name

        email = norm_email(row.get("email"))
        if email:
            if not self.email:
                self.email = email
            elif email != self.email and email not in self.alt_emails:
                self.alt_emails.append(email)

        phone = norm_phone(row.get("phone"))
        if phone and not self.phone:
            self.phone = phone

        org = row.get("organization", "").strip()
        if org:
            if not self.organization:
                self.organization = org
            elif norm_text(org) != norm_text(self.organization):
                if self.organization not in self.past_orgs:
                    self.past_orgs.append(self.organization)
                self.organization = org  # rows are processed oldest first

        date = row.get("meeting_date", "").strip()
        if date:
            self.dates.add(date)

        note = row.get("transcription_note", "").strip()
        if note and note not in self.notes:
            self.notes.append(note)

    # ---- review flags --------------------------------------------------
    def review_flags(self) -> list[str]:
        flags: list[str] = []
        first, last = split_name(self.full_name)
        if not self.email:
            flags.append("no email on file")
        elif not EMAIL_RE.match(self.email):
            flags.append("malformed email")
        if first and not last:
            flags.append("first name only - needs last name")
        flags.extend(self.notes)
        return flags

    def to_row(self, match: str = "") -> dict[str, str]:
        first, last = split_name(self.full_name)
        dates = sorted(self.dates)
        flags = self.review_flags()
        return {
            "Full Name": self.full_name,
            "First Name": first,
            "Last Name": last,
            "Email": self.email,
            "Alternate Emails": "; ".join(self.alt_emails),
            "Phone": self.phone,
            "Organization": self.organization,
            "Past Organizations": "; ".join(self.past_orgs),
            "Meeting Count": str(len(dates)),
            "First Meeting": dates[0] if dates else "",
            "Last Meeting": dates[-1] if dates else "",
            "Meeting Dates Attended": "; ".join(dates),
            "Needs Review": "Yes" if flags else "No",
            "Review Notes": "; ".join(flags),
            "Airtable Match": match,
        }


def _lower_keys(row: dict[str, str]) -> dict[str, str]:
    return {k.strip().lower().replace(" ", "_"): (v or "") for k, v in row.items() if k}


def dedupe(rows: list[dict[str, str]]) -> list[Contact]:
    """Merge sign-in rows into contacts. Rows are sorted by date first."""
    rows = sorted((_lower_keys(r) for r in rows), key=lambda r: r.get("meeting_date", ""))
    by_email: dict[str, Contact] = {}
    by_name_org: dict[tuple[str, str], Contact] = {}
    contacts: list[Contact] = []

    for row in rows:
        email = norm_email(row.get("email"))
        name_key = norm_text(row.get("name"))
        org_key = norm_text(row.get("organization"))
        full_name = len(name_key.split()) >= 2
        key = (name_key, org_key)

        contact = by_email.get(email) if email else None
        if contact is None and full_name:
            contact = by_name_org.get(key)

        if contact is None:
            contact = Contact()
            contacts.append(contact)

        contact.absorb(row)
        if email:
            by_email.setdefault(email, contact)
        if full_name:
            by_name_org.setdefault(key, contact)

    return contacts


def match_existing(contact: Contact, existing: list[dict[str, str]]) -> str:
    """Label a contact against an Airtable Attendees export."""
    emails = {contact.email, *contact.alt_emails} - {""}
    for rec in existing:
        if norm_email(rec.get("email")) in emails:
            return "match:email"
    name_key = norm_text(contact.full_name)
    org_key = norm_text(contact.organization)
    if len(name_key.split()) >= 2:
        for rec in existing:
            if norm_text(rec.get("name")) == name_key and norm_text(rec.get("organization")) == org_key:
                return "match:name+org"
    return "new"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="raw transcribed sign-ins CSV")
    ap.add_argument("-o", "--output", type=Path, default=Path("contacts_clean.csv"))
    ap.add_argument("--existing", type=Path, help="export of the live Airtable Attendees table")
    args = ap.parse_args(argv)

    raw = read_csv(args.input)
    contacts = dedupe(raw)
    existing = [_lower_keys(r) for r in read_csv(args.existing)] if args.existing else None

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for c in contacts:
            writer.writerow(c.to_row(match_existing(c, existing) if existing is not None else ""))

    review = sum(1 for c in contacts if c.review_flags())
    print(f"{len(raw)} sign-in lines -> {len(contacts)} unique contacts ({review} need review)", file=sys.stderr)
    print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
