# dominotify

OS X notifications of Domino Data Lab runs.

Setup:

    brew install terminal-notifier
    pip install requests
    export DOMINO_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX

To run:

    ./dominotify.py [search_paths] &

Todo:

- Growl notify support

Notes:

Sadly, the current combination of OS X & terminal-notifier does not support URLs.  Hopefully in the future, clicking the notification will open the results page.
