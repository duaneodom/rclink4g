#!/bin/bash
source bash.cgi


#===== setup variables =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
SNAPSHOT_DIR="snapshots"


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
        <h2>Snapshots</h2>
        <list>"

for SNAPSHOT in $(ls -1 $SNAPSHOT_DIR); do
    echo "<li>$SNAPSHOT <a href='$SNAPSHOT_DIR/$SNAPSHOT'>view</a></li>"
done

echo "
        </list>
    </body>
</html>"
