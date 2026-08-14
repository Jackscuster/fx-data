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

## Two datasets, on purpose

    data/px28.csv        LAYER 1. Fed H.10 noon rates, close-only, 1999-.
    data/ohlc/           LAYER 2. Yahoo daily OHLC, 28 pairs, raw download.
    data/ohlc_clean/     LAYER 2. The same after documented repairs. READ THIS ONE.

Layer 1 is frozen and close-only. Layer 2 cannot run on it: the risk plan sizes
every trade off ATR, stops and targets fill intrabar against the high and the
low, and a third of the NNFX indicator library reads the range directly. Layer 2
therefore has its own OHLC panel, and winners have to be found on real bars
because they have to port back to Pine on TradingView.

**Nothing in Layer 2 writes to px28.csv or to anything Layer 1 reads.** The two
disagree by construction — different sources, different snapshot times — and the
size of the disagreement is measured rather than assumed: median |Yahoo − H.10|
is 0.18% of price, per pair, in `results/l2_ohlc_coverage.csv`.

History is shorter: most pairs start 2003-12-01, not 1999 (USDJPY 1998, EURGBP
1999, AUDUSD 2006). Pre-2003 bars are not padded or reconstructed.

**There is no FX volume.** Spot FX has no consolidated tape and Yahoo's volume
column is identically zero, so it is dropped. Every indicator in the NNFX
"volume" slot must be a volatility or range measure.

    python code/l2data.py     # fetch (resumable, one file per pair) + coverage
    python code/l2clean.py    # the four repairs -> data/ohlc_clean/

The repairs are diagnosed in `code/l2clean.py`'s docstring and counted in
`results/l2_clean_report.csv`. The largest by far: Yahoo stamps the last bar of
the FX week on Sunday during US daylight saving, so 19,662 bars carry a date two
days late. Left alone, that misaligns three end-of-week bars in five against
Layer 1's Mon–Fri labels.

## Adding analysis
New tab = edit `app_ui.js`. New numbers = add a script under `code/` and a line in
`code/pipeline.py`, then extend `code/bundle.py` so it lands in app_data.json.
