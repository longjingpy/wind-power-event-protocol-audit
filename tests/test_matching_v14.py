import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
from event_matching_v14 import greedy, optimal

def test_conflicting_edges_maximum_iou():
    edges=[(0,0,.9,'a','x',0),(0,1,.8,'a','y',1),(1,0,.8,'b','x',1)]
    assert sum(e[2] for e in greedy(edges))==.9
    assert sum(e[2] for e in optimal(edges))==1.6

def test_empty_and_rectangular():
    assert optimal([])==[]
    edges=[(0,0,.9,'a','x',0),(1,0,.3,'b','x',1),(2,0,.4,'c','x',2)]
    assert optimal(edges)==[edges[0]]

def test_stable_ties():
    edges=[(0,0,.5,'a','x',0),(0,1,.5,'a','y',0),(1,0,.5,'b','x',0),(1,1,.5,'b','y',0)]
    assert greedy(edges)==greedy(list(reversed(edges)))
    assert optimal(edges)==optimal(list(reversed(edges)))
