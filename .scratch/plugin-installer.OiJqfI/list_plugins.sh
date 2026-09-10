#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail


source /jadawel/plugins/utils.sh

simple_log "Installed Jadawel Plugins:"
for plugin_folder in "$JADAWEL_PLUGIN_DIR"/*; do
    if [[ -d "$plugin_folder" ]]; then
        plugin_name="$(basename -- "$plugin_folder")"
        simple_log " - $plugin_name"
        if [[ -f "$plugin_folder/jadawel_plugin_info.json" ]]; then
            plugin_info="$(cat "$plugin_folder/jadawel_plugin_info.json")"
            description=$(echo "$plugin_info" | python3 -c "import sys, json; print(json.load(sys.stdin).get('description', ''))" || "")
            simple_log "      description: $description"
        fi
    fi
done