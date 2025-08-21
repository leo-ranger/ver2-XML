#!/usr/bin/env bash
set -e

XML_FILE="$1"
SHOWS_JSON="EPG/Show_Data/shows.json"

# Check XML file exists
if [ ! -f "$XML_FILE" ]; then
  echo "Error: XML file not found: $XML_FILE"
  exit 1
fi

# Check JSON file exists
if [ ! -f "$SHOWS_JSON" ]; then
  echo "Error: Shows JSON file not found: $SHOWS_JSON"
  exit 1
fi

# Validate JSON
if ! jq empty "$SHOWS_JSON" >/dev/null 2>&1; then
  echo "Error: Shows JSON is invalid: $SHOWS_JSON"
  exit 1
fi

# Loop over show names safely
jq -r 'keys[]' "$SHOWS_JSON" | while IFS= read -r show; do
  # Get icon URL
  icon=$(jq -r --arg show "$show" '.[$show].icon' "$SHOWS_JSON")
  # Get categories
  categories=$(jq -r --arg show "$show" '.[$show].categories[]' "$SHOWS_JSON")

  # Check if the show exists in the XML
  if grep -iq "<title[^>]*>$show</title>" "$XML_FILE"; then
    echo "Injecting metadata for: $show"

    # Build insert block
    insert_block="<icon src=\"$icon\"/>"
    for cat in $categories; do
      insert_block="$insert_block\n<category lang=\"en\">$cat</category>"
    done

    # Insert after title
    sed -i "/<title[^>]*>$show<\/title>/a $insert_block" "$XML_FILE"
  fi
done
