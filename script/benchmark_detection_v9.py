"""Controlled episode-localization benchmark with exhaustive synthetic labels.

TimesNet: Wu et al., ICLR 2023, https://arxiv.org/abs/2210.02186,
Temporal 2D-variation blocks; KAN-AD: Zhou et al., ICML 2025,
https://doi.org/10.48550/arXiv.2411.00278, Fourier-based reconstruction.
Implementations are imported from pinned upstream TSLib, not re-created here.
These are adapted controlled-task runs, not replications of published rankings.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import copy
import json
import sys
import time
import subprocess
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/detection_benchmark_v9'
UPSTREAM=ROOT/'temp/tslib_official'
L=96


def generate(n, seed, normal_only=False, shifted=False):
    rng=np.random.default_rng(seed); x=np.empty((n,L),np.float32); y=np.zeros((n,L),bool); meta=[]
    for i in range(n):
        t=np.arange(L); level=rng.uniform(.25,.65)
        noise=rng.normal(0,.015 if not shifted else .027,L)
        for j in range(1,L): noise[j]=.65*noise[j-1]+noise[j]
        baseline=level+rng.uniform(-.08,.08)*t/L+rng.uniform(.01,.06)*np.sin(t/rng.uniform(15,40)+rng.uniform(0,6))
        x[i]=baseline+noise
        positive=(i%2==0) and not normal_only
        amplitude=float(rng.choice([.08,.15,.30,.50])); duration=int(rng.choice([2,4,8,16])); sign=int(rng.choice([-1,1])); profile=str(rng.choice(['trapezoid','triangular']))
        start=int(rng.integers(24,60-duration)); width=2*duration+4
        if positive:
            if profile=='trapezoid': shape=np.r_[np.linspace(0,1,duration+1)[1:],np.ones(4),np.linspace(1,0,duration+1)[:-1]]
            else: shape=np.sin(np.linspace(0,np.pi,width+2)[1:-1])
            x[i,start:start+width]+=sign*amplitude*shape
            y[i,start:start+width]=True
        meta.append({'sequence_id':f'{seed}-{i}','positive':positive,'amplitude':amplitude if positive else 0.,'duration_steps':duration if positive else 0,'sign':sign if positive else 0,'profile':profile if positive else 'normal','start':start if positive else -1,'end':start+width if positive else -1})
    return x,y,pd.DataFrame(meta)


def segments(mask):
    edge=np.diff(np.r_[False,mask,False].astype(np.int8))
    return list(zip(np.flatnonzero(edge==1),np.flatnonzero(edge==-1)))


def event_counts(pred, truth, cutoff=.3):
    """Greedy one-to-one IoU matching within one completely labelled sequence."""
    a,b=segments(pred),segments(truth); edges=[]
    for i,(s,e) in enumerate(a):
        for j,(u,v) in enumerate(b):
            score=max(0,min(e,v)-max(s,u))/(max(e,v)-min(s,u))
            if score>=cutoff: edges.append((-score,i,j))
    ua=set();ub=set();delays=[]
    for _,i,j in sorted(edges):
        if i in ua or j in ub: continue
        ua.add(i);ub.add(j);delays.append(a[i][0]-b[j][0])
    return len(ua),len(a)-len(ua),len(b)-len(ub),delays


def postprocess(score, threshold, ratio=1., gap=0, minimum=1):
    high=score>=threshold; low=score>=threshold*ratio
    if gap:
        for a,b in segments(~low):
            if a>0 and b<len(low) and b-a<=gap: low[a:b]=True
    result=np.zeros(len(score),bool)
    for a,b in segments(low):
        if b-a>=minimum and high[a:b].any(): result[a:b]=True
    return result


def evaluate(scores, truth, config, cutoff=.3, detailed=False):
    rows=[];tp=fp=fn=0; delays=[]
    for i in range(len(scores)):
        p=postprocess(scores[i],**config); a,b,c,d=event_counts(p,truth[i],cutoff)
        tp+=a;fp+=b;fn+=c;delays.extend(d)
        if detailed: rows.append({'row':i,'tp':a,'fp':b,'fn':c,'delay_steps':float(np.mean(d)) if d else None})
    precision=tp/(tp+fp) if tp+fp else 0.; recall=tp/(tp+fn) if tp+fn else 0.
    out={'tp':tp,'fp':fp,'fn':fn,'precision':precision,'recall':recall,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.,'mean_delay_steps':float(np.mean(delays)) if delays else None,'sequences':len(scores),'truth_events':tp+fn}
    return (out,rows) if detailed else out


class SequenceAE(nn.Module):
    def __init__(self,kind,hidden=24,latent_dim=16):
        super().__init__(); self.kind=kind
        if kind=='tcn_ae':
            self.enc=nn.Sequential(nn.Conv1d(1,hidden,5,padding=2),nn.GELU(),nn.Conv1d(hidden,hidden,3,padding=2,dilation=2),nn.GELU(),nn.AdaptiveAvgPool1d(8),nn.Flatten(),nn.Linear(hidden*8,latent_dim))
        else:
            self.proj=nn.Linear(1,hidden); self.pos=nn.Parameter(torch.randn(1,L,hidden)*.02)
            layer=nn.TransformerEncoderLayer(hidden,4,max(hidden*2,32),dropout=.1,batch_first=True,activation='gelu')
            self.enc=nn.Sequential(nn.TransformerEncoder(layer,2),nn.Flatten(),nn.Linear(L*hidden,latent_dim))
        self.dec=nn.Sequential(nn.Linear(latent_dim,96),nn.GELU(),nn.Linear(96,L))

    def forward(self,x):
        x=self.enc(x.transpose(1,2)) if self.kind=='tcn_ae' else self.enc(self.proj(x)+self.pos)
        return self.dec(x).unsqueeze(-1)


class UpstreamAE(nn.Module):
    def __init__(self,kind,hidden=None,latent_dim=16):
        super().__init__(); sys.path.insert(0,str(UPSTREAM))
        from models import TimesNet, KANAD
        cfg=SimpleNamespace(task_name='anomaly_detection',seq_len=L,label_len=0,pred_len=0,d_model=hidden or (16 if kind=='timesnet' else 4),d_ff=max((hidden or (16 if kind=='timesnet' else 4))*2,32),enc_in=1,c_out=1,e_layers=1,top_k=3,num_kernels=3,embed='fixed',freq='h',dropout=.1)
        self.model=(TimesNet if kind=='timesnet' else KANAD).Model(cfg)

    def forward(self,x): return self.model(x,None,None,None)


def infer(model,x,mu,sd,device):
    model.eval(); scores=[]
    with torch.no_grad():
        for a in range(0,len(x),64):
            z=torch.as_tensor((x[a:a+64]-mu)/sd,device=device).unsqueeze(-1)
            r=model(z)
            if r.shape!=z.shape: raise ValueError((r.shape,z.shape))
            scores.append(((r-z)**2).squeeze(-1).cpu().numpy())
    score=np.concatenate(scores)
    if not np.isfinite(score).all(): raise ValueError('nonfinite reconstruction scores')
    return score


def fit_model(kind,seed,train,val_normal,epochs,device,hidden=24,latent_dim=16,lr=.001):
    torch.manual_seed(seed); rng=np.random.default_rng(seed)
    model=UpstreamAE(kind,hidden,latent_dim) if kind in ['timesnet','kanad'] else SequenceAE(kind,hidden,latent_dim)
    model.to(device); mu=float(train.mean());sd=float(train.std());sd=max(sd,1e-6)
    opt=torch.optim.Adam(model.parameters(),lr=lr); best=np.inf;best_state=None;bad=steps=0; log=[]
    for epoch in range(epochs):
        model.train(); order=rng.permutation(len(train)); losses=[]
        for a in range(0,len(train),64):
            x=torch.as_tensor((train[order[a:a+64]]-mu)/sd,device=device).unsqueeze(-1)
            opt.zero_grad(set_to_none=True); pred=model(x); loss=(pred-x).square().mean()
            if not torch.isfinite(loss): raise ValueError('nonfinite training loss')
            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();steps+=1;losses.append(float(loss.detach()))
        v=float(infer(model,val_normal,mu,sd,device).mean());log.append({'epoch':epoch+1,'optimizer_steps':steps,'train_mse':float(np.mean(losses)),'validation_normal_mse':v})
        if v<best-1e-6: best=v;best_state=copy.deepcopy(model.state_dict());bad=0
        else: bad+=1
        if bad>=5: break
    model.load_state_dict(best_state)
    torch.save({'state_dict':best_state,'mean':mu,'std':sd,'kind':kind,'seed':seed,'train_rows':len(train),'optimizer_steps':steps},OUT/f'model_{kind}_{seed}.pt')
    pd.DataFrame(log).to_csv(OUT/f'training_{kind}_{seed}.csv',index=False)
    return model,mu,sd,steps


def rule_scores(x,name):
    d=np.abs(np.diff(x,axis=1,prepend=x[:,:1]))
    if name in ['rate_rule','tail_rule']: return d
    p=pd.DataFrame(x.T)
    m=(p.rolling(4,min_periods=4).mean()-p.shift(4).rolling(4,min_periods=4).mean()).abs().fillna(0).to_numpy().T
    return m.astype(np.float32)


def calibrate(scores,truth):
    best=None; best_key=None
    # Selection is entirely on validation labels; test labels never enter here.
    for threshold in np.unique(np.quantile(scores,[.5,.7,.8,.9,.95,.97,.98,.99,.995])):
        for ratio in [1.,.5]:
            for gap in [0,2]:
                for minimum in [1,3]:
                    c={'threshold':float(threshold),'ratio':ratio,'gap':gap,'minimum':minimum}
                    r=evaluate(scores,truth,c);key=(r['f1'],r['precision'],threshold,-gap,-minimum)
                    if best_key is None or key>best_key:best=c;best_key=key
    return best


def tests():
    a=np.zeros(20,bool);a[4:10]=1
    assert event_counts(a,a)[:3]==(1,0,0)
    b=a.copy();b[14:17]=1
    assert event_counts(b,a)[:3]==(1,1,0)
    assert event_counts(np.zeros(20,bool),a)[:3]==(0,0,1)
    assert event_counts(np.ones(20,bool),a,.5)[:3]==(0,1,1)
    x=np.array([0,3,1,0,0,3,0],float)
    assert postprocess(x,2,.5,0,1).tolist()==[False,True,True,False,False,True,False]
    xx,yy,m=generate(20,1,True);assert not yy.any()
    xx,yy,m=generate(20,2);assert yy.any(1).sum()==10
    print('PASS: matching, missing predictions, all-normal labels, hysteresis')


def main(args):
    tests();OUT.mkdir(parents=True,exist_ok=True);torch.set_num_threads(2)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    train,_,_=generate(1600,9101,True); val,yval,_=generate(400,9102)
    test,ytest,metatest=generate(800,9103);shift,yshift,metashift=generate(800,9104,shifted=True)
    np.savez_compressed(OUT/'dataset.npz',train_normal=train,validation=val,validation_mask=yval,test=test,test_mask=ytest,shift=shift,shift_mask=yshift)
    metatest.to_csv(OUT/'test_meta.csv',index=False);metashift.to_csv(OUT/'shift_meta.csv',index=False)
    allrows=[];costs=[];conditions=[];configuration={}; t0=time.monotonic()
    for name in args.models:
        seeds=[0] if name.endswith('_rule') else args.seeds
        for seed in seeds:
            if name.endswith('_rule'):
                train_s=rule_scores(train,name);v=rule_scores(val,name);ts=rule_scores(test,name);ss=rule_scores(shift,name);steps=0
            else:
                model,mu,sd,steps=fit_model(name,seed,train,val[~yval.any(1)],args.epochs,device,args.hidden,args.latent_dim,args.learning_rate)
                train_s=infer(model,train,mu,sd,device);v=infer(model,val,mu,sd,device);ts=infer(model,test,mu,sd,device);ss=infer(model,shift,mu,sd,device)
            base={'threshold':float(np.quantile(train_s,.99)),'ratio':1.,'gap':0,'minimum':1}
            best=calibrate(v,yval); configuration[f'{name}-{seed}']={'default':base,'calibrated':best,'optimizer_steps':steps,'train_rows':len(train),'validation_rows':len(val),'test_rows':len(test)}
            np.savez_compressed(OUT/f'scores_{name}_{seed}.npz',validation=v,test=ts,shift=ss)
            for split,scores,truth,metadata in [('test',ts,ytest,metatest),('shift',ss,yshift,metashift)]:
                for mode,cfg in [('default',base),('calibrated',best)]:
                    for cutoff in [.1,.3,.5]:
                        result,detail=evaluate(scores,truth,cfg,cutoff,True)
                        result.update(model=name,seed=seed,split=split,protocol=mode,iou_cutoff=cutoff,optimizer_steps=steps)
                        result['window_auroc']=roc_auc_score(truth.any(1),np.quantile(scores,.95,axis=1))
                        result['window_ap']=average_precision_score(truth.any(1),np.quantile(scores,.95,axis=1))
                        allrows.append(result)
                        if cutoff==.3:
                            det=pd.DataFrame(detail).join(metadata)
                            for (amp,duration),g in det.groupby(['amplitude','duration_steps']):
                                conditions.append({'model':name,'seed':seed,'split':split,'protocol':mode,'amplitude':amp,'duration_steps':duration,'sequences':len(g),'tp':g.tp.sum(),'fp':g.fp.sum(),'fn':g.fn.sum()})
                            for ratio in [.1,1.,10.]:
                                costs.append({'model':name,'seed':seed,'split':split,'protocol':mode,'miss_to_false_alarm_cost_ratio':ratio,'cost_per_100_sequences':100*(result['fp']+ratio*result['fn'])/len(scores),'interpretation':'dimensionless synthetic alarm cost; not money, MWh or storage profit'})
            pd.DataFrame(allrows).to_csv(OUT/'metrics.csv',index=False)
            (OUT/'calibration.json').write_text(json.dumps(configuration,indent=2),encoding='utf8')
            print(name,seed,'steps',steps,'seconds',round(time.monotonic()-t0),flush=True)
    pd.DataFrame(conditions).to_csv(OUT/'application_conditions.csv',index=False)
    pd.DataFrame(costs).to_csv(OUT/'alarm_cost_sensitivity.csv',index=False)
    d=pd.DataFrame(allrows);p=d[(d.iou_cutoff==.3)].pivot(index=['model','seed','split'],columns='protocol',values=['f1','precision','recall'])
    gains=pd.DataFrame({m+'_gain':p[(m,'calibrated')]-p[(m,'default')] for m in ['f1','precision','recall']})
    gains.to_csv(OUT/'within_model_protocol_gain.csv')
    commit=subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip()
    (OUT/'manifest.json').write_text(json.dumps({'status':'CONTROLLED_SYNTHETIC_COMPLETE_NOT_REAL_FIELD_ACCURACY','models':args.models,'seeds':args.seeds,'upstream_commit':commit,'label_semantics':'entire finite injected episode, not WPRE edge or physical cause','training':'normal-only reconstruction, full minibatch epochs','calibration':'validation only, same grid all methods','point_adjustment':False,'time_points':L,'economic_scope':'alarm cost ratio sensitivity only; storage economic benefit remains separate','runtime_seconds':time.monotonic()-t0},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--epochs',type=int,default=30);ap.add_argument('--seeds',type=int,nargs='+',default=[41,42,43]);ap.add_argument('--models',nargs='+',default=['rate_rule','mean_rule','tcn_ae','transformer_ae','timesnet','kanad']);ap.add_argument('--output-dir',type=Path,default=OUT);ap.add_argument('--hidden',type=int,default=24);ap.add_argument('--latent-dim',type=int,default=16);ap.add_argument('--learning-rate',type=float,default=.001);args=ap.parse_args();OUT=args.output_dir
    tests() if args.test else main(args)
