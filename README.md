# fx-data — self-refreshing feed for the FX Signal Gauntlet

GitHub Actions reruns the whole pipeline on a schedule and commits a fresh
`app_data.json`. The app points at the raw URL of that file and picks up changes
automatically. Nothing to upload by hand.

Feed URL:
    https://raw.githubusercontent.com/<you>/fx-data/main/app_data.json

Schedule: weekdays 06:00 UTC. Also runs on any push to `code/`, or on demand from
the Actions tab -> "rebuild fx data" -> Run workflow.

Runtime ~40 min. Free tier allows 6 h per job.
