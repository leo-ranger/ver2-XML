#!/usr/bin/env bash
set -e

XML_FILE="$1"
SHOWS_JSON="EPG/Show_Data/shows.json"

if [ ! -f "$XML_FILE" ]; then
  echo "XML file not found: $XML_FILE"
  exit 1
fi

for show in $(jq -r 'keys[]' "$SHOWS_JSON"); do
  icon=$(jq -r --arg show "$show" '.[$show].icon' "$SHOWS_JSON")
  categories=$(jq -r --arg show "$show" '.[$show].categories[]' "$SHOWS_JSON")

  if grep -iq "<title[^>]*>$show</title>" "$XML_FILE"; then
    echo "Injecting metadata for: $show"
    insert_block="<icon src=\"$icon\"/>"
    for cat in $categories; do
      insert_block="$insert_block\n<category lang=\"en\">$cat</category>"
    done

    # Add block after every title match
    sed -i "/<title[^>]*>$show<\/title>/a $insert_block" "$XML_FILE"
  fi
done
