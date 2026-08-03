# fx-data — self-refreshing feed AND interface

Two files are served to the app:

    app_data.json   the numbers   (rebuilt automatically by GitHub Actions)
    app_ui.js       the interface (new tabs land here; no app redownload needed)

The shell HTML on your device loads BOTH from this repo. It never needs updating again.

Feed URL to paste into the app, once:

    https://raw.githubusercontent.com/<you>/fx-data/main/app_data.json

The app derives the app_ui.js URL from that automatically.

## Schedule
Weekdays 06:00 UTC, on any push to `code/`, or on demand:
Actions tab -> "rebuild fx data" -> Run workflow. Runtime ~40 min.

## Adding analysis
New tab = edit `app_ui.js`. New numbers = add a script under `code/` and a line in
`code/pipeline.py`, then extend `code/bundle.py` so it lands in app_data.json.
