from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wind_events.matching import overlap_graph,match_intervals

@pytest.mark.parametrize('left,right',[
    ([('a',0,0)],[('b',0,0)]),([('a',4,2)],[('b',0,3)]),
    ([('a',0,2),('a',2,4)],[('b',0,4)])])
def test_invalid_intervals_raise_before_iou(left,right):
    with pytest.raises(ValueError):match_intervals(left,right)
    with pytest.raises(ValueError):overlap_graph(left,right)

def test_touching_and_empty_are_not_edges():
    assert overlap_graph([('a',0,2)],[('b',2,4)])==([],[])
    assert overlap_graph([],[])==([],[])

def test_v_episode_keeps_both_legs():
    a=[('v',0,4)];b=[('fall',0,2),('rise',2,4)]
    edges,cc=overlap_graph(a,b)
    assert len(edges)==2 and len(cc)==1 and len(cc[0]['right_ids'])==2
    assert [r['iou'] for r in edges]==[.5,.5]
    assert len(match_intervals(a,b))==1

def test_many_to_many_and_containment_are_distinct():
    a=[('a1',0,3),('a2',1,4)];b=[('b1',0,2),('b2',2,4)]
    edges,cc=overlap_graph(a,b,cutoff=.2)
    assert len(cc)==1 and len(edges)==4
    assert overlap_graph([('v',0,4)],[('leg',1,2)],cutoff=.5)[0]==[]
    edges,cc=overlap_graph([('v',0,4)],[('leg',1,2)],cutoff=.5,measure='containment')
    assert edges[0]['iou']==.25 and edges[0]['score']==1
