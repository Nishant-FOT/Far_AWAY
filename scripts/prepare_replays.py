#!/usr/bin/env python3
"""Prepare and save demo replays for sample detection events.

This script will read `data/sample_detection_events.json`, run the
`PipelineOrchestrator` for each sample, and save a final-stage replay
into the sqlite-backed replay store so the frontend can load them
instantly via `/api/v1/command/replay/{incident_id}`.
"""
import os
import sys
import json
import asyncio

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from shared.orchestrator import PipelineOrchestrator
from backend.app.services.replay_store import save_stages


async def prepare():
    samples_path = os.path.join(repo_root, 'data', 'sample_detection_events.json')
    if not os.path.exists(samples_path):
        print('Samples file not found:', samples_path)
        return
    with open(samples_path, 'r', encoding='utf-8') as fh:
        samples = json.load(fh)

    for s in samples:
        incident_id = s.get('incident_id')
        print(f'Processing sample {incident_id} ...')
        try:
            orch = PipelineOrchestrator()
            state = await orch.process_incident(s)
            # store a single final snapshot
            save_stages(incident_id, [{"stage": "final", "output": state}])
            print(f'Wrote replay for {incident_id}')
        except Exception as e:
            print(f'Failed to prepare {incident_id}:', e)


if __name__ == '__main__':
    asyncio.run(prepare())
