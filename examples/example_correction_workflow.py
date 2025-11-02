#!/usr/bin/env python
"""
Example workflow demonstrating the correction acceptance/rejection feature.

This script shows how to:
1. Create a correction run
2. List all suggestions
3. Accept/reject corrections individually
4. Accept/reject in bulk
5. Export document with only accepted corrections

Requirements:
- Server running on http://localhost:8000
- Valid authentication token
"""
import requests
import time
from typing import Dict, List


API_BASE = "http://localhost:8000"


def login(email: str, password: str) -> str:
    """Login and get access token."""
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_headers(token: str) -> Dict[str, str]:
    """Get headers with authentication."""
    return {"Authorization": f"Bearer {token}"}


def list_suggestions(token: str, run_id: str, status: str = None) -> List[Dict]:
    """List all suggestions for a run, optionally filtered by status."""
    url = f"{API_BASE}/suggestions/runs/{run_id}/suggestions"
    params = {"status": status} if status else {}
    response = requests.get(url, headers=get_headers(token), params=params)
    response.raise_for_status()
    return response.json()["suggestions"]


def accept_suggestion(token: str, suggestion_id: str) -> Dict:
    """Accept a single suggestion."""
    response = requests.patch(
        f"{API_BASE}/suggestions/suggestions/{suggestion_id}",
        headers=get_headers(token),
        json={"status": "accepted"}
    )
    response.raise_for_status()
    return response.json()


def reject_suggestion(token: str, suggestion_id: str) -> Dict:
    """Reject a single suggestion."""
    response = requests.patch(
        f"{API_BASE}/suggestions/suggestions/{suggestion_id}",
        headers=get_headers(token),
        json={"status": "rejected"}
    )
    response.raise_for_status()
    return response.json()


def bulk_accept(token: str, run_id: str, suggestion_ids: List[str]) -> Dict:
    """Accept multiple suggestions at once."""
    response = requests.post(
        f"{API_BASE}/suggestions/runs/{run_id}/suggestions/bulk-update",
        headers=get_headers(token),
        json={"suggestion_ids": suggestion_ids, "status": "accepted"}
    )
    response.raise_for_status()
    return response.json()


def bulk_reject(token: str, run_id: str, suggestion_ids: List[str]) -> Dict:
    """Reject multiple suggestions at once."""
    response = requests.post(
        f"{API_BASE}/suggestions/runs/{run_id}/suggestions/bulk-update",
        headers=get_headers(token),
        json={"suggestion_ids": suggestion_ids, "status": "rejected"}
    )
    response.raise_for_status()
    return response.json()


def accept_all(token: str, run_id: str) -> Dict:
    """Accept all pending suggestions."""
    response = requests.post(
        f"{API_BASE}/suggestions/runs/{run_id}/suggestions/accept-all",
        headers=get_headers(token)
    )
    response.raise_for_status()
    return response.json()


def reject_all(token: str, run_id: str) -> Dict:
    """Reject all pending suggestions."""
    response = requests.post(
        f"{API_BASE}/suggestions/runs/{run_id}/suggestions/reject-all",
        headers=get_headers(token)
    )
    response.raise_for_status()
    return response.json()


def export_with_accepted(token: str, run_id: str, output_path: str):
    """Export document with only accepted corrections applied."""
    response = requests.post(
        f"{API_BASE}/suggestions/runs/{run_id}/export-with-accepted",
        headers=get_headers(token),
        stream=True
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Document exported to: {output_path}")


def main():
    """Example workflow."""
    # Configuration
    EMAIL = "demo@example.com"
    PASSWORD = "demo123"
    RUN_ID = "your-run-id-here"  # Replace with actual run ID

    print("=" * 60)
    print("Correction Acceptance/Rejection Workflow Example")
    print("=" * 60)

    # Step 1: Login
    print("\n1. Logging in...")
    token = login(EMAIL, PASSWORD)
    print(f"   Token obtained: {token[:20]}...")

    # Step 2: List all suggestions
    print("\n2. Listing all suggestions...")
    suggestions = list_suggestions(token, RUN_ID)
    print(f"   Total suggestions: {len(suggestions)}")

    if not suggestions:
        print("   No suggestions found. Run a correction first!")
        return

    # Step 3: Show suggestions by type
    print("\n3. Suggestions by type:")
    by_type = {}
    for sugg in suggestions:
        stype = sugg["suggestion_type"]
        by_type.setdefault(stype, []).append(sugg)

    for stype, suggs in by_type.items():
        print(f"   - {stype}: {len(suggs)}")

    # Step 4: Accept all orthography corrections
    print("\n4. Auto-accepting orthography corrections...")
    ortho_ids = [s["id"] for s in by_type.get("ortografia", [])]
    if ortho_ids:
        result = bulk_accept(token, RUN_ID, ortho_ids)
        print(f"   Accepted {result['updated']} orthography corrections")

    # Step 5: Review style suggestions individually
    print("\n5. Reviewing style suggestions...")
    style_suggestions = by_type.get("estilo", [])
    for i, sugg in enumerate(style_suggestions[:3], 1):  # First 3 only
        print(f"\n   Suggestion {i}:")
        print(f"   Before: {sugg['before']}")
        print(f"   After:  {sugg['after']}")
        print(f"   Reason: {sugg['reason']}")
        print(f"   Context: {sugg['context'][:50]}...")

        # Example: Accept first, reject second, skip third
        if i == 1:
            accept_suggestion(token, sugg["id"])
            print("   -> ACCEPTED")
        elif i == 2:
            reject_suggestion(token, sugg["id"])
            print("   -> REJECTED")
        else:
            print("   -> SKIPPED (remains pending)")

    # Step 6: Accept all remaining pending
    print("\n6. Accepting all remaining pending suggestions...")
    result = accept_all(token, RUN_ID)
    print(f"   Accepted {result['accepted']} pending suggestions")

    # Step 7: Show final stats
    print("\n7. Final statistics:")
    for status in ["accepted", "rejected", "pending"]:
        suggestions = list_suggestions(token, RUN_ID, status=status)
        print(f"   {status}: {len(suggestions)}")

    # Step 8: Export final document
    print("\n8. Exporting document with accepted corrections...")
    output_path = f"output_accepted_{int(time.time())}.docx"
    export_with_accepted(token, RUN_ID, output_path)

    print("\n" + "=" * 60)
    print("Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
    except KeyError as e:
        print(f"\nConfiguration error: {e}")
        print("Make sure to set RUN_ID to a valid run ID")
