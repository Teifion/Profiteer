There are two ways to run the profiteer engine.

cli.py
======
This is designed for command line tasks such as data validation checks
and batch processing.

To list the options and commands available type:
    python cli.py -h

web.py
======
This script is the entry point to the Admin GUI. It's designed to be run
via a webserver. I'm using the Apache server that comes with OSX.

For those in a similar boat here's the changes I had to make to the conf file

    open /etc/apache2/httpd.conf

In the <IfModule alias_module> block add:

    ScriptAliasMatch ^/profiteer/web.py*$ "/Library/WebServer/CGI-Executables/profiteer/web.py$1"

