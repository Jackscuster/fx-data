"""Full rebuild. Run by GitHub Actions on a schedule."""
import os,sys,subprocess,shutil
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C=os.path.join(R,'code')
def run(m):
    print('\n=== %s ==='%m,flush=True)
    subprocess.run([sys.executable,os.path.join(C,m)],check=True)
run('build.py')
for m in ('sc2.py','sc2.py','sc2.py','sc2.py','sc2.py'):   # resumable, idempotent
    run(m)
run('sc3.py'); run('sc3.py')
run('rank2.py'); run('rank3.py'); run('prep.py')
run('strat.py'); run('framework.py'); run('bundle.py')
shutil.copy(os.path.join(R,'results','app_data.json'),os.path.join(R,'app_data.json'))
print('\napp_data.json refreshed at repo root')
