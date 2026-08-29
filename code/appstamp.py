import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Stamp app_ui.js with a build id and publish it in app_version.json.

WHY A CONTENT HASH RATHER THAN A COMMIT OR A TIMESTAMP. A commit hash is not
known until after the commit that contains the stamp, which is circular. A
timestamp changes on every run and would invalidate a 9 MB feed for no reason.
A hash of app_ui.js's own bytes -- with the stamp line itself normalised out --
changes exactly when the interface changes, and not otherwise.

The running interface compares its embedded UI_BUILD against app_version.json,
fetched with a cache-buster. If they differ the browser is serving stale code
and the interface says so, with a button that re-fetches bypassing cache. That
is the failure this exists for: a normal reload served a cached app_ui.js while
incognito served the current one, and nothing on screen said which was which.

Run after editing app_ui.js. pipeline.py runs it so CI keeps the two in step.
"""
import hashlib, json, re, time

UI = os.path.join(_R, 'app_ui.js')
VER = os.path.join(_R, 'app_version.json')
PAT = re.compile(r"^const UI_BUILD='[^']*';", re.M)


def stamp():
    src = open(UI).read()
    if not PAT.search(src):
        raise SystemExit('app_ui.js has no UI_BUILD line to stamp')
    norm = PAT.sub("const UI_BUILD='';", src)
    h = hashlib.sha1(norm.encode()).hexdigest()[:12]
    new = PAT.sub("const UI_BUILD='%s';" % h, src)
    changed = new != src
    if changed:
        open(UI, 'w').write(new)
    json.dump(dict(ui_build=h,
                   built=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   note='app_ui.js compares its embedded UI_BUILD against this. '
                        'Fetched with a cache-buster so it is never stale.'),
              open(VER, 'w'), indent=1)
    return h, changed


if __name__ == '__main__':
    h, ch = stamp()
    print('app_ui.js build %s%s; app_version.json updated'
          % (h, ' (stamp rewritten)' if ch else ' (already current)'))
