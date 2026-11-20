import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PUSH JACK'S PHONE WHEN A DELIVERABLE LANDS.

The watchdog pushes when a chain finishes WITHOUT its deliverable. This pushes
when one is PRESENT, which is the thing Jack asked to hear about on 20 Nov and
which nothing else reports. It refuses to push if the file is missing or empty,
because a false landing is worse than silence.

    python3 code/l2r2push.py --what "mode B passers books" \\
        --file results/r2gate2/MODEB_PASSERBOOKS.md \\
        --also results/r2gate2/MODEA_PASSERBOOKS.md
"""
import subprocess
import l2r2gate1 as G

TOPIC_FILE = os.path.expanduser('~/fx-data-logs/ntfy_topic')


def freegb():
    try:
        out = subprocess.run(['df', '-g', '/System/Volumes/Data'],
                             capture_output=True, text=True, timeout=10).stdout
        return out.strip().splitlines()[-1].split()[3]
    except Exception:
        return '?'


def main():
    what = G.opt('--what', str, 'a deliverable')
    files = [f for f in (G.opt('--file', str, None), G.opt('--also', str, None)) if f]
    assert files, 'pass at least --file'
    missing = [f for f in files if not (os.path.exists(f) and os.path.getsize(f) > 1)]
    if missing:
        print('  NOT PUSHING: %s is missing or empty -- a false landing is worse '
              'than silence' % ', '.join(missing), flush=True)
        return 1
    lines = []
    for f in files:
        with open(f) as fh:
            lines.append('%s: %d lines' % (os.path.basename(f), sum(1 for _ in fh)))
    if not os.path.exists(TOPIC_FILE):
        print('  NOT PUSHING: no ntfy topic file at %s' % TOPIC_FILE, flush=True)
        return 1
    topic = open(TOPIC_FILE).read().strip()
    body = '%s landed.\n%s\nFree space %s GB.' % (what, '\n'.join(lines), freegb())
    r = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '20',
         '-H', 'Title: fx-data: %s LANDED' % what,
         '-H', 'Priority: default', '-H', 'Tags: books',
         '-d', body, 'https://ntfy.sh/%s' % topic],
        capture_output=True, text=True)
    print('  push "%s" -> ntfy HTTP %s' % (what, r.stdout.strip()), flush=True)
    return 0 if r.stdout.strip() == '200' else 1


if __name__ == '__main__':
    raise SystemExit(main())
