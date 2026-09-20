"""Export input-only, randomly ordered copies of the existing blind packet."""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/protocol_benchmark_v25/ai_reference'
RUBRIC="""Independent AI review of a wind-power display. Rate the CENTRAL TWO HOURS
(-60,-30,0,30,60 minutes); the four-hour context (-120 to120) helps interpretation.
The nine values are normalized power at 30-minute intervals. Use only these
curves, not other labels, detector definitions, site identities or web sources.
Judge whether a recognizable dynamic change occurs centrally. Rise=upward,
fall=downward, valley=v_shape, peak=inverted_v, repeated substantial reversals=
oscillatory, near-steady=quiet, persistent near-zero=low_state. A V/peak can be
dynamic despite small net change. Transition into/out of low power is a change,
not merely low_state. Ordinary small jitter need not be a dynamic event.
Use uncertain when the sampled data cannot support a judgment; missing invalid
values may be bad_data. No universal numerical threshold is imposed by the
original human rubric. Return one dominant morphology and confidence H/M/L per
window. Do not fabricate boundary precision or weather/fault causes.
This is an AI-generated assessment, never a human questionnaire response.
Do not implement a threshold classifier to generate answers; independently
inspect and judge each supplied numeric curve. Other reviewers' answers are
not available. Preserve every window, including difficult/ambiguous cases.
"""

def main():
    packet=json.loads((ROOT/'annotation_multirater_v19/packet.json').read_text())
    windows=packet['windows'];assert len(windows)==320
    OUT.mkdir(parents=True,exist_ok=True)
    for round_ in range(1,8):
        folder=OUT/f'A{round_:02d}';folder.mkdir(exist_ok=True)
        rows=[RUBRIC,'','Output: CSV columns window_id,morphology,confidence.',
              'Allowed morphology: upward,downward,v_shape,inverted_v,oscillatory,quiet,low_state,uncertain,bad_data.',
              'Input times (min): -120,-90,-60,-30,0,30,60,90,120.','']
        for j in np.random.default_rng(2500+round_).permutation(320):
            w=windows[j];assert len(w['power'])==9
            values=','.join('NA' if v is None or not np.isfinite(v) else f'{v:.5f}' for v in w['power'])
            rows.append(w['window_id']+': '+values)
        (folder/'input.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    (OUT/'protocol.json').write_text(json.dumps({'status':'INPUTS_READY_NO_AI_LABELS_YET','planned_ai_sessions':7,'human_observers':3,'windows':320,
        'scope':'existing selected-window cohort; centrally rated 2h within 4h context',
        'source_type':'AI; not anonymous human survey respondents','stopping':'all 7 completed sessions per user reduction before alpha; not agreement-threshold stopping',
        'effective_model':'record from actual runtime where available; do not infer identity'},indent=2))
    print('Prepared 7 input-only randomized presentation packets, 320 windows each.')

if __name__=='__main__':main()
