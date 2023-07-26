#!/bin/bash
rm -f dist/rclink4g.tar
tar hcf dist/rclink4g.tar *.cgi *.html *.py rclink4g.* reset_network_link.sh
makeself --follow dist/ dist/setup_rclink4g.run "RCLink4G Setup Script" ./setup_rclink4g.sh
chmod -x dist/setup_rclink4g.run
