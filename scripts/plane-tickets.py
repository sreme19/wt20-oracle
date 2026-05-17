#!/usr/bin/env python3
"""Fetch and display pocket-dating-coach Plane tickets."""

import json
import sys
import urllib.request
import urllib.parse
from collections import defaultdict

API_KEY = "plane_api_6b9df478323d40aea66ff884183faf57"
WORKSPACE = "woam"
PROJECT_ID = "0b2cef85-7a7d-4936-baeb-8d9bb0e5c7cd"
BASE_URL = "https://api.plane.so/api/v1"
HEADERS = {"X-Api-Key": API_KEY, "User-Agent": "plane-tickets/1.0"}


def get(path):
    """Make a GET request to the Plane API."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_all(path):
    """Fetch all pages using Plane's cursor-based pagination."""
    results = []
    sep = "&" if "?" in path else "?"
    url_path = f"{path}{sep}per_page=100"
    while True:
        data = get(url_path)
        items = data.get("results", [])
        results.extend(items)
        if not data.get("next_page_results"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break
        base = url_path.split("?cursor=")[0]
        sep2 = "&" if "?" in base else "?"
        url_path = f"{base}{sep2}cursor={urllib.parse.quote(cursor)}&per_page=100"
    return results


def get_state_name(issue):
    """Extract state name from issue."""
    state = (issue.get("state_detail") or {}).get("name", "") or issue.get("state", "Unknown")
    return state


def get_priority_label(priority):
    """Convert priority to label."""
    labels = {"urgent": "🔴 URGENT", "high": "🟠 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW", "none": "⚪ NONE"}
    return labels.get(priority, priority or "⚪ NONE")


def get_assignees(issue):
    """Extract assignee names from issue."""
    assignees = issue.get("assignee_details") or []
    return ", ".join(a.get("display_name", a.get("email", "?")) for a in assignees) or "Unassigned"


def strip_html(html_text):
    """Simple HTML tag removal."""
    if not html_text:
        return ""
    import re
    return re.sub(r"<[^>]+>", "", html_text).strip()


def main():
    print("=" * 80)
    print("WT20-ORACLE — Plane Tickets")
    print("=" * 80)

    # Fetch all issues
    path = f"/workspaces/{WORKSPACE}/projects/{PROJECT_ID}/issues/"
    print(f"\nFetching tickets from {path}...")
    issues = get_all(path)

    if not issues:
        print("No tickets found!")
        return

    print(f"Found {len(issues)} tickets\n")

    # Group by state
    by_state = defaultdict(list)
    for issue in issues:
        state = get_state_name(issue)
        by_state[state].append(issue)

    # Display by state
    for state in sorted(by_state.keys()):
        issues_in_state = by_state[state]
        print(f"\n{'─' * 80}")
        print(f"{state.upper()} ({len(issues_in_state)})")
        print(f"{'─' * 80}")

        # Sort by priority, then by name
        sorted_issues = sorted(
            issues_in_state,
            key=lambda x: (
                {"urgent": 0, "high": 1, "medium": 2, "low": 3, "none": 4}.get(x.get("priority", "none"), 5),
                x.get("name", ""),
            ),
        )

        for issue in sorted_issues:
            seq = issue.get("sequence_id", "?")
            priority = get_priority_label(issue.get("priority", ""))
            name = issue.get("name", "")
            desc = strip_html(issue.get("description_html", ""))[:60]
            assignees = get_assignees(issue)

            print(f"\n  PDC-{seq}  {priority}")
            print(f"  Title: {name}")
            if desc:
                print(f"  Desc:  {desc}...")
            if assignees != "Unassigned":
                print(f"  Owner: {assignees}")

    # Summary stats
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    by_priority = defaultdict(int)
    for issue in issues:
        priority = get_priority_label(issue.get("priority", ""))
        by_priority[priority] += 1

    print(f"\nTotal: {len(issues)} tickets")
    print("\nBy Priority:")
    for priority in ["🔴 URGENT", "🟠 HIGH", "🟡 MEDIUM", "🟢 LOW", "⚪ NONE"]:
        count = by_priority.get(priority, 0)
        if count > 0:
            print(f"  {priority}: {count}")

    print(f"\nBy State:")
    for state in sorted(by_state.keys()):
        print(f"  {state}: {len(by_state[state])}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
