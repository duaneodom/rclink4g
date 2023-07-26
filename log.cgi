#!/bin/bash
source bash.cgi


#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
LOG_FILE=${FORMS[file]}
LOG_EPOCH=$(basename ${LOG_FILE%.*})
LOG_DATE=$(date -d @$LOG_EPOCH +%Y-%m-%d || echo "Boot Log")


echo -e "Content-type: text/html\n\n"
echo "<!DOCTYPE html>
<html>
    <head>
        <style>
            li:nth-child(odd)
            {
                background: #eee;
            }

            li:nth-child(even)
            {
                background: #fff;
            }
        </style>
    </head>
    <body>
        <h2>$LOG_DATE</h2>
        <list>"

while read LINE; do
    echo "<li>$LINE</li>"
done < "$LOG_FILE"

echo "
        </list>
    </body>
</html>"
