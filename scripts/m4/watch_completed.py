"""Postprocess completed queued studies; never inspect an actively written RTH."""
import argparse,re,time
from pathlib import Path
from post_completed_studies import process,RUN

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cases',nargs='+');a=p.parse_args();remaining=list(a.cases)
    while remaining:
        for name in list(remaining):
            path=RUN/name/'study.out'
            if not path.exists():continue
            with path.open('rb') as stream:
                stream.seek(max(0,path.stat().st_size-12000));tail=stream.read().decode(errors='replace')
            if 'RUN COMPLETED' not in tail:continue
            if not re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0',tail):raise RuntimeError('Native errors: '+name)
            process(name);remaining.remove(name)
        if remaining:time.sleep(10)
