#!/bin/bash
# Example curl commands for using the correction acceptance/rejection API

# Base URL
API_BASE="http://localhost:8000"

# === Step 1: Login ===
echo "1. Logging in..."
TOKEN=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}' \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

# === Step 2: List all suggestions ===
echo -e "\n2. Listing all suggestions..."
RUN_ID="your-run-id-here"  # Replace with actual run ID

curl -s -X GET "$API_BASE/suggestions/runs/$RUN_ID/suggestions" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.total, .suggestions[0:3]'

# === Step 3: List only pending suggestions ===
echo -e "\n3. Listing pending suggestions..."
curl -s -X GET "$API_BASE/suggestions/runs/$RUN_ID/suggestions?status=pending" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.total'

# === Step 4: Accept a single suggestion ===
echo -e "\n4. Accepting single suggestion..."
SUGGESTION_ID="suggestion-id-here"  # Replace with actual suggestion ID

curl -s -X PATCH "$API_BASE/suggestions/suggestions/$SUGGESTION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"accepted"}' \
  | jq '.'

# === Step 5: Reject a single suggestion ===
echo -e "\n5. Rejecting single suggestion..."
curl -s -X PATCH "$API_BASE/suggestions/suggestions/$SUGGESTION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"rejected"}' \
  | jq '.'

# === Step 6: Bulk accept multiple suggestions ===
echo -e "\n6. Bulk accepting suggestions..."
curl -s -X POST "$API_BASE/suggestions/runs/$RUN_ID/suggestions/bulk-update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_ids": ["id1", "id2", "id3"],
    "status": "accepted"
  }' \
  | jq '.'

# === Step 7: Accept all pending suggestions ===
echo -e "\n7. Accepting all pending..."
curl -s -X POST "$API_BASE/suggestions/runs/$RUN_ID/suggestions/accept-all" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# === Step 8: Reject all pending suggestions ===
echo -e "\n8. Rejecting all pending..."
curl -s -X POST "$API_BASE/suggestions/runs/$RUN_ID/suggestions/reject-all" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# === Step 9: Export document with accepted corrections ===
echo -e "\n9. Exporting document with accepted corrections..."
curl -X POST "$API_BASE/suggestions/runs/$RUN_ID/export-with-accepted" \
  -H "Authorization: Bearer $TOKEN" \
  -o "output_accepted.docx"

echo "Document saved to: output_accepted.docx"

# === Step 10: Show final statistics ===
echo -e "\n10. Final statistics:"
for STATUS in pending accepted rejected; do
  COUNT=$(curl -s -X GET "$API_BASE/suggestions/runs/$RUN_ID/suggestions?status=$STATUS" \
    -H "Authorization: Bearer $TOKEN" \
    | jq '.total')
  echo "  $STATUS: $COUNT"
done
