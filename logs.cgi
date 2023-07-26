#!/bin/bash
source bash.cgi


#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"


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
        <h2>Log Files</h2>
        <list>"

echo "<li>Boot Log <a href='log.cgi?file=$LOG_DIR/boot.log'>view</a></li>"

for LOG_FILE in $(ls -1 $LOG_DIR | grep -v boot); do
    LOG_EPOCH=${LOG_FILE%.*}
    LOG_DATE=$(date -d @$LOG_EPOCH +%Y-%m-%d_%H:%M:%S)
    echo "<li>$LOG_DATE <a href='log.cgi?file=$LOG_DIR/$LOG_FILE'>view</a></li>"
done

echo "
        </list>
    </body>
</html>"
