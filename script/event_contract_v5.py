"""Study-defined event contract, not a published SDA/OpSDA reproduction.

The endpoint chord and UTC greedy matching are definitions in
manuscript/V5_EXECUTION_PROTOCOL.md, not inferred literature algorithms.
Train-only transforms prevent test exposure (Kapoor & Narayanan, Leakage and
the reproducibility crisis, DOI 10.1016/j.patter.2023.100804, leakage taxonomy).
They change the validity of transfer comparisons, not the physical event truth.
"""
from itertools import combinations
from pathlib import Path
import hashlib
import json
import os
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('WPF_EVENT_OUT', str(ROOT / 'outputs/dynamic_events_v5')))
GROUP = ['site', 'turbine', 'split']
FEATURES = ['duration_hours', 'amplitude', 'power_range', 'total_variation',
            'max_abs_rate_per_hour', 'max_abs_chord_residual', 'curvature_l1',
            'pre_mean', 'post_mean']


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save_manifest(path, payload, inputs=(), outputs=()):
    payload = dict(payload)
    payload['inputs_sha256'] = {str(Path(p).relative_to(ROOT)): digest(p) for p in inputs}
    payload['outputs_sha256'] = {str(Path(p).relative_to(ROOT)): digest(p) for p in outputs}
    payload['protocol_sha256'] = digest(ROOT / 'manuscript/V5_EXECUTION_PROTOCOL.md')
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf8')


def history_epsilon(x, start):
    history = np.asarray(x[max(0, start-48):start+1], float)
    differences = np.diff(history)
    n = len(differences)
    if not n:
        return .025, 0, 'floor_no_history'
    mad = np.median(np.abs(differences - np.median(differences)))
    epsilon = max(.025, 1.4826*mad, .01*np.median(np.abs(history)))
    return float(epsilon), n, 'full_history' if n == 48 else 'partial_history'


def segment_corridor(x, epsilon=None):
    """Actual-endpoint chord tolerance; adaptive epsilon is frozen per segment."""
    x = np.asarray(x, float)
    if not np.isfinite(x).all() or (epsilon is not None and (not np.isfinite(epsilon) or epsilon <= 0)):
        raise ValueError('Require finite input and positive fixed epsilon')
    if len(x) < 2:
        return []
    start, low, high = 0, -np.inf, np.inf
    def tolerance(a):
        return history_epsilon(x, a) if epsilon is None else (float(epsilon), 0, 'fixed')
    eps, history_n, mode = tolerance(start)
    segments = []
    for end in range(1, len(x)):
        slope = (x[end]-x[start])/(end-start)
        if slope < low-1e-12 or slope > high+1e-12:
            segments.append((start, end-1, eps, history_n, mode))
            start, low, high = end-1, -np.inf, np.inf
            eps, history_n, mode = tolerance(start)
        low = max(low, (x[end]-x[start]-eps)/(end-start))
        high = min(high, (x[end]-x[start]+eps)/(end-start))
    segments.append((start, len(x)-1, eps, history_n, mode))
    return segments


def checked_take(matrix, indices):
    indices = np.asarray(indices)
    if not np.issubdtype(indices.dtype, np.integer) or np.any(indices < 0) or np.any(indices >= len(matrix)):
        raise IndexError('Missing or invalid encoded row; negative indices forbidden')
    return matrix[indices]


def fit_standardizer(x, train_rows):
    train = checked_take(np.asarray(x), np.asarray(train_rows, dtype=int))
    if not len(train) or not np.isfinite(train).all():
        raise ValueError('Nonempty finite training data required')
    mean, std = train.mean(axis=0), train.std(axis=0)
    return mean, np.where(std > 0, std, 1.)


def pair_intervals(table):
    """One-to-one UTC matching per turbine/split/config-pair; no score sampling."""
    if not table.event_id.is_unique:
        raise ValueError('Event IDs must be unique')
    d = table.copy()
    for field in ['time_start', 'time_end']:
        ts = pd.to_datetime(d[field], utc=True, errors='raise')
        if ts.isna().any():
            raise ValueError('Missing timestamp')
        d[field+'_ns'] = ts.astype('int64')
    if (d.time_end_ns <= d.time_start_ns).any():
        raise ValueError('Positive duration required')
    rows, coverage = [], []
    for group, g in d.groupby(GROUP, sort=True):
        parts = {c: t.sort_values(['time_start_ns', 'time_end_ns', 'event_id'])
                 for c, t in g.groupby('config', sort=True)}
        for ca, cb in combinations(sorted(parts), 2):
            a, b = parts[ca], parts[cb]
            left = list(a[['event_id', 'time_start_ns', 'time_end_ns']].itertuples(index=False, name=None))
            right = list(b[['event_id', 'time_start_ns', 'time_end_ns']].itertuples(index=False, name=None))
            bs = b.time_start_ns.to_numpy()
            max_duration = int((b.time_end_ns-b.time_start_ns).max())
            candidates = []
            for aid, a0, a1 in left:
                lo = np.searchsorted(bs, a0-max_duration, side='right')
                hi = np.searchsorted(bs, a1, side='left')
                for bid, b0, b1 in right[lo:hi]:
                    inter = min(a1, b1)-max(a0, b0)
                    union = max(a1, b1)-min(a0, b0)
                    score = inter/union
                    if score >= .5:
                        candidates.append((-score, abs(a0-b0), aid, bid, min(a0, b0)))
            used_a, used_b = set(), set()
            for negative_iou, _, aid, bid, timestamp in sorted(candidates):
                if aid in used_a or bid in used_b:
                    continue
                used_a.add(aid); used_b.add(bid)
                rows.append(dict(zip(GROUP, group)) | {'config_a': ca, 'config_b': cb,
                    'event_a': aid, 'event_b': bid, 'iou': -negative_iou,
                    'pair_time_utc': pd.Timestamp(timestamp, tz='UTC').isoformat()})
            coverage.append(dict(zip(GROUP, group)) | {'config_a': ca, 'config_b': cb,
                'left_n': len(a), 'right_n': len(b), 'pairs': len(used_a),
                'left_coverage': len(used_a)/len(a), 'right_coverage': len(used_b)/len(b)})
    columns = GROUP+['config_a', 'config_b', 'event_a', 'event_b', 'iou', 'pair_time_utc']
    return pd.DataFrame(rows, columns=columns), pd.DataFrame(coverage)
