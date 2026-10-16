"""Separate bounded historical readiness/exit0 and heartbeat/exit8 experiments."""
import asyncio
import json
import os
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, immutable_json


async def main():
    if platform.system()!='Darwin':raise RuntimeError('these incidents require native macOS')
    root=RAW/'historical-macos'/uuid.uuid4().hex;root.mkdir(parents=True)
    declarations=[dict(incident='R3-02',control='TestAdversarialStubbornUnixDescendantCleanup',
                       interpretation='Original readiness/exit0 branch remains causally unproven'),
                  dict(incident='R3-03',control='TestAdversarialStubbornHeartbeatPublication',
                       interpretation='Reduced torn-heartbeat publication fixture repair; not a diagnosis of every old exit8')]
    schedule=[dict(batch='ordinary',race=False,load=False),dict(batch='race',race=True,load=False),
              dict(batch='race-contention',race=True,load=True)]
    immutable_json(root/'declared-schedule.json',dict(incidents=declarations,batches=schedule,repetitions_each=50,
        bounds='Each owned contention worker lasts at most two seconds; Go test parent 900 seconds; no product deadline change'))
    records=[]
    for incident in declarations:
        for batch in schedule:
            argv=['go','test','-json','-count=50','-run','^'+incident['control']+'$','./internal/runner']
            if batch['race']:argv.insert(2,'-race')
            result=await execute(argv,'historical-macos',incident['incident']+'-'+batch['batch'],
                                 timeout=900,load=batch['load'],campaign=Campaign())
            events=[]
            for line in result['output'].splitlines():
                try:event=json.loads(line)
                except ValueError:continue
                if isinstance(event,dict) and event.get('Test')==incident['control'] and event.get('Action') in {'pass','skip','fail'}:
                    events.append(event)
            if len(events)!=50 or any(e['Action']!='pass' for e in events):
                raise RuntimeError('missing or nonpassing whole control repetitions')
            records.append(dict(incident=incident['incident'],batch=batch['batch'],attempt=result['id'],actual_passes=50))
            immutable_json(root/(incident['incident']+'-'+batch['batch']+'.json'),records[-1])
            print(incident['incident'],batch['batch'],'fifty actual passes',flush=True)
    immutable_json(root/'summary.json',dict(records=records,claim='Bounded current-control observations; original unlogged causal branches remain unresolved'))


if __name__=='__main__':asyncio.run(main())
