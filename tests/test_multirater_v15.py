import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
from merge_multirater_v15 import cohen, nominal_alpha, agreement, merge_payloads

def test_perfect_variable_labels():
    assert cohen(['yes','no'],['yes','no'])['kappa']==1
    assert nominal_alpha([['yes','yes'],['no','no']])['alpha']==1

def test_disagreement_and_degenerate_cases():
    assert cohen(['yes','no'],['no','yes'])['kappa']==-1
    assert nominal_alpha([['yes','no'],['no','yes']])['alpha']==-.5
    assert cohen(['yes'],['yes'])['kappa'] is None
    assert nominal_alpha([['yes','yes']])['alpha'] is None
    assert agreement([])['status']=='AWAITING_INDEPENDENT_RATINGS'

def test_missing_annotations_not_imputed():
    report=nominal_alpha([['a','a'],['b','b','b'],['a']])
    assert report['alpha']==1 and report['rated_units']==2 and report['ratings']==5

def test_same_rater_not_counted_twice_and_scope_validated():
    packet={'packet_id':'p','windows':[{'window_id':'M001','target_start':'a','target_end':'b'}]}
    row={'window_id':'M001','target_start':'a','target_end':'b','morphology':'quiet','event_presence':'no',
         'confidence':'unrated','updated_at':'2026-09-15T00:00:00Z','event_start_relative_min':None,'event_end_relative_min':None}
    payload={'schema':'wind_multirater_v15','packet_id':'p','annotator_id':'R01','annotations':[row]}
    rows,duplicates=merge_payloads([payload,payload],packet)
    assert len(rows)==1 and duplicates==1 and agreement(rows)['distinct_annotator_ids']==1
    bad=dict(payload,annotations=[dict(row,target_start='wrong')])
    with pytest.raises(ValueError):merge_payloads([bad],packet)
