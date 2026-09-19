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
    boxstyle='rounded=1;arcSize=13;whiteSpace=wrap;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=22;spacing=10;strokeWidth=2;'
    text='shape=text;strokeColor=none;fillColor=none;whiteSpace=wrap;html=0;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=21;'
    cell(root,'title','Protocol-aware wind-power event measurement',20,10,840,40,title+'fontColor=#172A3A;')
    # One input panel prevents crossing the common quality-control annotation.
    cell(root,'inputs','',20,65,840,115,boxstyle+'fillColor=#F4F7F9;strokeColor=#C3D1DB;')
    cell(root,'china','China\n4 archives · 298 turbines',40,73,380,64,text+'fontColor=#23688F;')
    cell(root,'europe','Europe\n4 archives · 42 turbines',460,73,380,64,text+'fontColor=#AD681E;')
    cell(root,'shared','Physical time · quality flags · training-only scaling',40,139,800,30,text+'fontSize=19;')
    cell(root,'detector','1  Detection\nIntervals + turns',20,215,245,85,boxstyle+'fillColor=#E1F0F5;strokeColor=#95C8D5;')
    cell(root,'matching','2  Matching\nOne-to-one IoU',317.5,215,245,85,boxstyle+'fillColor=#E9F1DC;strokeColor=#AFC68D;')
    cell(root,'representation','3  Representation\nShapes + partitions',615,215,245,85,boxstyle+'fillColor=#FFF0CB;strokeColor=#DFC16A;')
    cell(root,'evaluation','4  Evaluation and decision',20,340,840,65,boxstyle+'fillColor=#F2EDF6;strokeColor=#B49DC4;fontStyle=1;')
    cell(root,'structure','Structural survival\nARI · NMI · coverage',20,445,245,80,boxstyle+'fillColor=#F2EDF6;strokeColor=#B49DC4;')
    cell(root,'physical','Physical tracking\nWind · LiDAR',317.5,445,245,80,boxstyle+'fillColor=#F2EDF6;strokeColor=#B49DC4;')
    cell(root,'decision','Forecast-to-cost\nPrices · storage',615,445,245,80,boxstyle+'fillColor=#F2EDF6;strokeColor=#B49DC4;')
    cell(root,'references','Independent references\nBlind ratings · weather · LiDAR · prices',20,570,840,65,boxstyle+'fillColor=#F5F6F7;strokeColor=#CCD2D8;fontSize=20;')
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
        if c.get('edge')=='1':assert c.get('source') in vertices and c.get('target') in vertices
    print(OUT)

if __name__=='__main__':main()
