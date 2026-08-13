# Queued: SHAPE_MEASUREMENTS.md — four measurements

Build against the corrected NINE-state version (three shapes x three activity
levels). Each measures something about the CURRENT state; whether it also leads a
state change is a second question and not the point.

1. **Failed swings** — is a level being defended.
   Partly built: `code/failswing.py` has the within-window definition and the
   X x Y surface, but it was scored as a LEAD indicator against state changes and
   dropped on that basis (16.4l). Rescore it as a present-tense property of the
   current state, which is what was actually asked for.
2. **Retracement depth** — is a trend tiring. Not built.
3. **Swing spacing** — is momentum fading. Not built. `shapewin.lookback()`
   already measures swing spacing per window and is the natural starting point.
4. **Cross-pair** — is this move idiosyncratic or panel-wide. Not built.

Do not lose these.
