"""Create an editable draw.io source for the Fig. 1 study workflow.

The local runtime exposes no drawio_live MCP backend. The file is generated as
standard mxGraph XML with one editable cell per label/panel/edge; draw.io can
open it without flattening the figure.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'manuscript/figures_v22/fig01_workflow.drawio'

def cell(root, ident, value, x, y, w, h, style, vertex=True):
    attrs={'id':ident,'value':value,'style':style,'parent':'1'}
    if vertex: attrs['vertex']='1'
    c=ET.SubElement(root,'mxCell',attrs)
    ET.SubElement(c,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})
    return c

def edge(root, ident, source, target, points=None, style='edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;endArrow=block;'):
    attrs={'id':ident,'value':'','style':style,'edge':'1','parent':'1','source':source,'target':target}
    c=ET.SubElement(root,'mxCell',attrs)
    geo=ET.SubElement(c,'mxGeometry',{'relative':'1','as':'geometry'})
    if points:
        arr=ET.SubElement(geo,'Array',{'as':'points'})
        for x,y in points: ET.SubElement(arr,'mxPoint',{'x':str(x),'y':str(y)})
    return c

def main():
    mx=ET.Element('mxGraphModel',{'dx':'880','dy':'655','grid':'1','gridSize':'10','guides':'1','tooltips':'1','connect':'1','arrows':'1','fold':'1','page':'1','pageScale':'1','pageWidth':'880','pageHeight':'655','math':'0','shadow':'0'})
    root=ET.SubElement(mx,'root');ET.SubElement(root,'mxCell',{'id':'0'});ET.SubElement(root,'mxCell',{'id':'1','parent':'0'})
    title='shape=text;strokeColor=none;fillColor=none;fontFamily=Arial;fontSize=25;fontStyle=1;align=center;verticalAlign=middle;html=0;whiteSpace=wrap;'
    boxstyle='rounded=1;arcSize=13;whiteSpace=wrap;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=22;spacing=10;strokeWidth=0;'
    text='shape=text;strokeColor=none;fillColor=none;whiteSpace=wrap;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=21;'
    cell(root,'title','Protocol-aware wind-power event measurement',20,10,840,40,title+'fontColor=#172A3A;')
    # One input panel prevents crossing the common quality-control annotation.
    cell(root,'inputs','',20,65,840,115,boxstyle+'fillColor=#EDF3F5;strokeColor=none;')
    cell(root,'china','China\n4 archives · 298 turbines',40,73,380,64,text+'fontColor=#23688F;')
    cell(root,'europe','Europe\n4 archives · 42 turbines',460,73,380,64,text+'fontColor=#AD681E;')
    cell(root,'shared','Physical time · quality flags · training-only scaling',40,139,800,30,text+'fontSize=19;')
    for ident,x,heading,body in [('detector',20,'1  Detection','Ramps · V / inverted V'),('matching',317.5,'2  Correspondence','One-to-one + overlap graph'),('representation',615,'3  Representation','Raw · PCA · angular + sign')]:
        cell(root,ident,'',x,215,245,110,boxstyle+'fillColor=#DCEEF0;strokeColor=none;')
        cell(root,ident+'_heading',heading,x+7,222,231,28,text+'fontStyle=1;fontColor=#173C4D;')
        cell(root,ident+'_body',body,x+6,292,233,25,text+'fontSize=18;fontColor=#355560;')
    # Miniatures are illustrative editable primitives, not empirical data.
    def line(ident,coords,color='#277E87',width=2,dashed=False):
        style=f'edgeStyle=none;endArrow=none;strokeColor={color};strokeWidth={width};'+('dashed=1;' if dashed else '')
        c=ET.SubElement(root,'mxCell',{'id':ident,'edge':'1','parent':'1','style':style})
        geo=ET.SubElement(c,'mxGeometry',{'relative':'1','as':'geometry'})
        ET.SubElement(geo,'mxPoint',{'x':str(coords[0][0]),'y':str(coords[0][1]),'as':'sourcePoint'})
        ET.SubElement(geo,'mxPoint',{'x':str(coords[-1][0]),'y':str(coords[-1][1]),'as':'targetPoint'})
        if len(coords)>2:
            arr=ET.SubElement(geo,'Array',{'as':'points'})
            for xx,yy in coords[1:-1]:ET.SubElement(arr,'mxPoint',{'x':str(xx),'y':str(yy)})
    line('rise_icon',[(44,280),(63,278),(78,260),(94,254)])
    line('valley_icon',[(110,255),(132,283),(154,255)])
    line('peak_icon',[(174,282),(196,254),(222,281)])
    for side,x in [('left',365),('right',506)]:
        for i,y in enumerate([260,280]):cell(root,f'{side}_{i}','',x,y,9,9,'ellipse;fillColor=#277E87;strokeColor=none;')
    for i,(ya,yb) in enumerate([(264,264),(264,284),(284,284)]):line('overlap_link'+str(i),[(374,ya),(506,yb)],width=1.5)
    line('raw_icon',[(638,283),(649,258),(662,280),(676,265)])
    palette=['#D5E8EB','#A7CDD2','#6EABB5','#337984']
    for i in range(4):
        for j in range(4):cell(root,f'angular_{i}_{j}','',699+j*8,255+i*8,8,8,f'fillColor={palette[abs(i-j)]};strokeColor=none;')
    cell(root,'sign_icon','±',753,253,35,33,text+'fontSize=28;fontStyle=1;fontColor=#277E87;')
    cell(root,'shape_dim','25 → 6',794,258,59,30,text+'fontSize=17;')
    cell(root,'evaluation','4  Evaluation and decision',20,362,840,44,boxstyle+'fillColor=#DBE4EE;strokeColor=none;fontStyle=1;')
    for ident,x,heading,body in [('structure',20,'Structural survival','ARI · NMI · coverage\nSplit / merge composition'),('physical',317.5,'Physical tracking','ERA5 · independent LiDAR\nDirection · calibrated probability'),('decision',615,'Forecast-to-cost','Issued forecast → settlement\nDebit · credit · storage')]:
        cell(root,ident,'',x,446,245,110,boxstyle+'fillColor=#EEF3F7;strokeColor=none;')
        cell(root,ident+'_head',heading,x+5,451,235,30,text+'fontStyle=1;fontColor=#173C4D;')
        cell(root,ident+'_detail',body,x+4,481,237,65,text+'fontSize=18;')
    cell(root,'references','Independent references\nBlind ratings · weather · LiDAR · prices',20,590,840,62,boxstyle+'fillColor=#EDF3F5;strokeColor=none;fontSize=20;')
    plain='edgeStyle=none;html=0;rounded=0;strokeColor=#405564;strokeWidth=2;endArrow=block;endFill=1;'
    def connect(ident,source,target,ex,ey,ix,iy,dashed=False):
        edge(root,ident,source,target,style=plain+f'exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={ix};entryY={iy};entryDx=0;entryDy=0;'+('dashed=1;' if dashed else ''))
    left=.1458333333333333;right=.8541666666666666
    connect('data_to_detection','inputs','detector',left,1,.5,0)
    connect('detection_to_matching','detector','matching',1,.5,0,.5)
    connect('matching_to_representation','matching','representation',1,.5,0,.5)
    connect('representation_to_evaluation','representation','evaluation',.5,1,right,0)
    for ident,target,x in [('structure','structure',left),('physical','physical',.5),('decision','decision',right)]:
        connect('evaluate_'+ident,'evaluation',target,x,1,.5,0)
        connect('reference_'+ident,'references',target,x,0,.5,1,True)
    file=ET.Element('mxfile',{'host':'draw.io','version':'28.0.0','type':'device'})
    diagram=ET.SubElement(file,'diagram',{'id':'wind-measurement','name':'Figure 1'});diagram.append(mx)
    ET.indent(file,space=' ');OUT.write_bytes(ET.tostring(file,encoding='utf-8',xml_declaration=True))
    # Each geometry-bearing cell must belong to the default layer; each edge
    # has a real source and target. This catches the prior orphan-cell file.
    vertices={c.attrib['id'] for c in root if c.get('vertex')=='1'}
    for c in root:
        if c.get('vertex')=='1' or c.get('edge')=='1':assert c.get('parent')=='1'
        if c.get('edge')=='1' and c.get('source'):
            assert c.get('source') in vertices and c.get('target') in vertices
    print(OUT)

if __name__=='__main__':main()
