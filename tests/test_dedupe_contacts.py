import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dedupe_contacts as dc  # noqa: E402

SAMPLES = ROOT / "data" / "samples"


def load():
    return dc.read_csv(SAMPLES / "signins_raw.csv")


def by_name(contacts, name):
    return [c for c in contacts if c.full_name == name]


def test_merges_on_email_and_name_org():
    contacts = dc.dedupe(load())
    [alex] = by_name(contacts, "Alex Rivera")
    assert alex.email == "alex.rivera@example.com"
    assert "arivera@example.org" in alex.alt_emails  # matched by name+org, kept as alternate
    assert alex.to_row()["Meeting Count"] == "4"


def test_org_change_recorded_as_past_org():
    [alex] = by_name(dc.dedupe(load()), "Alex Rivera")
    assert alex.organization == "New Dawn Outreach"
    assert alex.past_orgs == ["Hope Street Church"]


def test_fallback_name_plus_org_when_no_email():
    [jordan] = by_name(dc.dedupe(load()), "Jordan Lee")
    row = jordan.to_row()
    assert row["Meeting Count"] == "2"
    assert row["Phone"] == "(555) 010-0202"
    assert "no email on file" in row["Review Notes"]


def test_first_name_only_never_auto_merged():
    sams = by_name(dc.dedupe(load()), "Sam")
    assert len(sams) == 2
    assert all("first name only" in s.to_row()["Review Notes"] for s in sams)


def test_same_day_duplicate_not_double_counted():
    [taylor] = by_name(dc.dedupe(load()), "Taylor Brooks")
    assert taylor.to_row()["Meeting Count"] == "1"


def test_malformed_email_flagged():
    [morgan] = by_name(dc.dedupe(load()), "Morgan Ellis")
    row = morgan.to_row()
    assert row["Needs Review"] == "Yes"
    assert "malformed email" in row["Review Notes"]


def test_clean_contact_needs_no_review():
    [casey] = by_name(dc.dedupe(load()), "Casey Nguyen")
    assert casey.to_row()["Needs Review"] == "No"


def test_match_against_existing_airtable():
    contacts = dc.dedupe(load())
    existing = [dc._lower_keys(r) for r in dc.read_csv(SAMPLES / "airtable_attendees_export.csv")]
    labels = {c.full_name: dc.match_existing(c, existing) for c in contacts}
    assert labels["Alex Rivera"] == "match:email"      # via alternate email
    assert labels["Jordan Lee"] == "match:name+org"
    assert labels["Casey Nguyen"] == "new"


def test_cli_writes_expected_output(tmp_path):
    out = tmp_path / "clean.csv"
    assert dc.main([str(SAMPLES / "signins_raw.csv"), "-o", str(out),
                    "--existing", str(SAMPLES / "airtable_attendees_export.csv")]) == 0
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 7
    assert list(rows[0].keys()) == dc.OUTPUT_FIELDS
