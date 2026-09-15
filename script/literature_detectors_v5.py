"""Source-traced SDA and conference-version OpSDA, with explicit study settings.

Florita et al., Identifying Wind and Solar Ramping Events, 2013,
DOI 10.1109/GreenTech.2013.30, printed pp.2-3: two hinges, parallel doors,
close AT the violating observation. This is not the endpoint-chord variant.
Cui et al., An Optimized Swinging Door Algorithm for Wind Power Ramp Event
Detection, 2015, DOI 10.1109/PESGM.2015.7286272, printed p.2 Eqs.(1)-(3):
dynamic programming, squared interval-length reward, user-defined ramp rule.
The same-direction merge restriction follows p.2 text. This implementation
declares window stride/endpoints and ties absent from that preprint. It is NOT
a reproduction of the extended 2016 journal version or its ERCOT results.
"""
import numpy as np


def original_sda(x, epsilon):
    x=np.asarray(x,float)
    if not np.isfinite(x).all() or not np.isfinite(epsilon) or epsilon<=0:
        raise ValueError('Finite signal and positive epsilon required')
    if len(x)<2:return []
    start=0; lower=-np.inf; upper=np.inf; segments=[]
    for end in range(1,len(x)):
        lower=max(lower,(x[end]-x[start]-epsilon)/(end-start))
        upper=min(upper,(x[end]-x[start]+epsilon)/(end-start))
        if lower>=upper-1e-12:
            segments.append((start,end))
            start=end; lower=-np.inf; upper=np.inf
    if start<len(x)-1:segments.append((start,len(x)-1))
    return segments


def optimize_window(x, knots, amplitude=.2):
    """Prefix form of Cui Eq.(1); zero-score intervals fill non-ramp portions."""
    x=np.asarray(x,float); knots=np.asarray(knots,int)
    if len(knots)<2:return [],0.
    if (np.diff(knots)<=0).any() or knots[0]<0 or knots[-1]>=len(x):
        raise ValueError('Ordered in-range SDA endpoints required')
    n=len(knots); best=np.zeros(n); previous=np.full(n,-1,int); chosen=np.zeros(n,bool)
    for j in range(1,n):
        best[j]=best[j-1]; previous[j]=j-1
        for i in range(j):
            changes=np.diff(x[knots[i:j+1]])
            monotone=(changes>=0).all() or (changes<=0).all()
            qualifies=monotone and abs(x[knots[j]]-x[knots[i]])>=amplitude
            if qualifies:
                reward=float((knots[j]-knots[i])**2)
                candidate=best[i]+reward
                if candidate>best[j]+1e-12:
                    best[j]=candidate; previous[j]=i; chosen[j]=True
    intervals=[]; j=n-1
    while j>0:
        i=previous[j]
        if chosen[j]:intervals.append((int(knots[i]),int(knots[j])))
        j=i
    return intervals[::-1],float(best[-1])


def opsda_2015(x, epsilon, horizon_steps, amplitude=.2):
    """Windows start at every SDA knot; stop at last knot <= requested horizon.

    Union of per-window DP optima, exact duplicate endpoints removed. This
    explicit overlap policy preserves candidates; it does not claim uniqueness
    of meteorological events. A segment exceeding the horizon is not clipped.
    """
    if horizon_steps<1:raise ValueError('Positive horizon required')
    segments=original_sda(x,epsilon)
    if not segments:return []
    knots=np.array([segments[0][0]]+[b for a,b in segments])
    intervals=set()
    for i,a in enumerate(knots[:-1]):
        stop=np.searchsorted(knots,a+horizon_steps,side='right')
        ramps,_=optimize_window(x,knots[i:stop],amplitude)
        intervals.update(ramps)
    return sorted(intervals)
