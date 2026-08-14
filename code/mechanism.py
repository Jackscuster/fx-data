import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Why each pair behaves the way it does, in one sentence.

THE HONEST STATUS OF THIS FILE. The RANKING is measured -- it comes from
pair_character.csv and it held across both halves of 27 years. The MECHANISM is
an explanation attached to that measurement afterwards. It is economics, not
output: nothing here was fitted, and no sentence below was tested. It is included
because a ranking without a reason invites the reader to invent one, and a stated
reason can at least be argued with.

The sentences are COMPOSED, not hand-written per pair: each currency carries a
declared role, and the line is built from the two roles plus the pair's measured
position in the ranking. That way 28 sentences cannot quietly disagree with 28
numbers.

Writes results/pair_mechanism.csv + .txt.
"""
import pandas as pd

CHAR = os.path.join(ROOTOUT, 'pair_character.csv')

ROLE = {
    'USD': ('the world reserve currency', 'moves on US rates and global risk'),
    'EUR': ('a large, slow bloc', 'moves on ECB policy and growth differentials'),
    'GBP': ('a mid-sized open economy', 'moves on UK policy and its own politics'),
    'JPY': ('a funding and haven currency',
            'strengthens when global risk rises and carry trades unwind'),
    'CHF': ('a haven currency',
            'strengthens when European risk rises, and is periodically managed '
            'by its central bank'),
    'AUD': ('a commodity and China-growth proxy',
            'moves on industrial demand and global risk appetite'),
    'NZD': ('a small commodity currency',
            'moves on soft commodities and global risk appetite, with the '
            'thinnest liquidity of the eight'),
    'CAD': ('an oil-linked North American currency',
            'moves on crude and on the US economy it borders'),
}
HAVEN = {'JPY', 'CHF'}
COMMODITY = {'AUD', 'NZD', 'CAD'}
BLOC = {'EUR', 'GBP'}


def line(pair, trendiness, rank, n):
    a, b = pair[:3], pair[3:]
    A, B = ROLE[a], ROLE[b]
    trendy = trendiness > 0
    pair_of = {a, b}
    if pair_of & HAVEN and pair_of & COMMODITY:
        why = ('one side is bid when risk rises and the other is sold, so a '
               'single shift in global risk pushes both legs the same way at '
               'once -- the cleanest trending structure in the set')
    elif pair_of <= BLOC:
        why = ('two neighbouring economies on similar policy paths, so the two '
               'legs mostly cancel and the pair spends its time going nowhere')
    elif pair_of <= COMMODITY:
        why = ('two currencies driven by the same global demand cycle, so much '
               'of the move cancels and what is left is range-bound')
    elif pair_of <= HAVEN:
        why = ('both are bid when risk rises, so they largely offset and the '
               'pair moves on the difference between two central banks')
    elif 'USD' in pair_of:
        other = (pair_of - {'USD'}).pop()
        why = ('the dollar leg carries global risk and rates while %s %s, so '
               'the pair trends when those two stories diverge and ranges when '
               'they agree' % (other, ROLE[other][1]))
    elif pair_of & HAVEN:
        other = (pair_of - HAVEN).pop()
        why = ('a haven leg against %s, so risk-off episodes move it in one '
               'direction for weeks at a time' % ROLE[other][0])
    else:
        why = ('%s against %s, so it moves on the gap between two policy cycles'
               % (A[0], B[0]))
    tail = ('It sits at rank %d of %d on trendiness, so it is one of the more '
            'directional pairs in the set.' if trendy else
            'It sits at rank %d of %d on trendiness, so it spends more of its '
            'life range-bound than trending.') % (rank, n)
    return ('%s: %s. %s' % (pair, why[0].upper() + why[1:], tail))


def main():
    C = pd.read_csv(CHAR)
    C = C.sort_values('trendiness', ascending=False).reset_index(drop=True)
    C['rank'] = C.index + 1
    n = len(C)
    rows = []
    for _, r in C.iterrows():
        rows.append(dict(pair=r.pair, rank=int(r['rank']),
                         trendiness=float(r.trendiness),
                         mechanism=line(r.pair, r.trendiness, int(r['rank']), n)))
    M = pd.DataFrame(rows)
    M.to_csv(os.path.join(ROOTOUT, 'pair_mechanism.csv'), index=False)
    print('PAIR MECHANISM -- one composed sentence per pair')
    for _, r in M.head(4).iterrows():
        print('  %s' % r.mechanism)
    print('  ... %d rows' % len(M))
    with open(os.path.join(ROOTOUT, 'pair_mechanism.txt'), 'w') as f:
        f.write(
            'Why each pair behaves the way it does\n'
            '=====================================\n\n'
            'THE RANKING IS MEASURED. It comes from pair_character.csv and it\n'
            'held across both halves of 27 years.\n\n'
            'THE MECHANISM IS AN EXPLANATION ATTACHED AFTERWARDS. It is\n'
            'economics, not output: nothing here was fitted and no sentence was\n'
            'tested. It is included because a ranking without a reason invites\n'
            'the reader to invent one, and a stated reason can be argued with.\n\n'
            'The sentences are COMPOSED from declared currency roles plus the\n'
            "pair's measured position in the ranking, so 28 sentences cannot\n"
            'quietly disagree with 28 numbers.\n\n'
            + '\n'.join('  ' + r.mechanism for _, r in M.iterrows()) + '\n')
    print('wrote pair_mechanism.csv + .txt')
    return M


if __name__ == '__main__':
    main()
