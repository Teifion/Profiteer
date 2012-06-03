Install PG utils (mine are at /Library/PostgreSQL/9.0/bin)

Install .pgpass

OSX
===
Place the profiteer folder into /Library/WebServer/CGI-Executables/
Ensure web.py has executable permissions

TODO - Find script to make web.py executable

Optionally: add a shortcut to cli.py in ~bash_profile, mine looks like this:

    alias prof='python3 /Library/WebServer/CGI-Executables/profiteer/cli.py'


Linux
=====

Windows
=======


Postgres Users
--------------
The profiteer engine uses 3 separate databases. Live, Mock and Test. The live
database (normally referred to without any prefix) is where all the action will
take place. The Mock database is designed to be used to test out possibly
dangerous code and the Test database is used solely for unit testing.

When you configure the config.json file you will need to input login details
for the profiteer user on the postgres server.

Forum API
---------
You need to upload the Forum API folder to your server and setup the configuration
file within it to connect it to the database. Without this the profiteer engine
cannot connect to the Forum Database and thus cannot sync with it.

Installing the database
-----------------------
Run

    cli.py install

The first time you run it you will be prompted to add some information to the
config.json file, running it again will test the data and then setup the tables
for the database. Once this is done you have an empty database.

Installing the forum API
------------------------

Create data
-----------
You will now need to run "check" mode, normally most modes are run through the command
line interface however you can run this mode through the web GUI by clicking "checks"
under the System header on the right-side nav bar.

Running the "check" mode on profiteer will now inform you there is a lack
of resources, techs, station modules, ship components, ship hulls, factions and
authors. As you start to add them the messages will alter to inform you of how
many of each you have. These messages will stop appearing once you start your
first turn. It is up to you to decide how many of each you want to include in
your game, the colour coding is only a guideline.

Some settings
-------------
 * **use\_simple\_components**: When set to true it strips most of the attributes from the ship component pages and lists. If set to false you have access to the full set of properties I thought might be needed by myself. Profiteer has this set to true.
 * **use\_z**: The engine is designed to allow 3D combat. Profiteer the game only uses two dimensions.
 * **admin\_gui\_password**: If you access the system from outside the computer it is running on it will require you to login. This is not considered a secure login as it works by IP and will time out after 5 minutes of inactivity.

