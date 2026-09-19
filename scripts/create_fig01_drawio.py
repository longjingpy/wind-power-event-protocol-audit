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
    attrs={'id':ident,'value':value,'style':style}
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
    mx=ET.Element('mxGraphModel',{'dx':'1600','dy':'1000','grid':'1','gridSize':'10','guides':'1','tooltips':'1','connect':'1','arrows':'1','fold':'1','page':'1','pageScale':'1','pageWidth':'1600','pageHeight':'1000','math':'0','shadow':'0'})
    root=ET.SubElement(mx,'root');ET.SubElement(root,'mxCell',{'id':'0'});ET.SubElement(root,'mxCell',{'id':'1','parent':'0'})
    title='fontFamily=Arial;fontSize=28;fontStyle=1;align=center;verticalAlign=middle;html=1;whiteSpace=wrap;'
    section='rounded=1;arcSize=12;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=20;fontStyle=1;strokeWidth=2;'
    body='rounded=1;arcSize=10;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=18;strokeWidth=2;'
    note='rounded=1;arcSize=8;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=16;strokeWidth=1.5;'
    text='whiteSpace=wrap;html=1;align=center;verticalAlign=middle;fontFamily=Arial;fontSize=18;'
    cell(root,'title','Event measurement → independent validation',100,25,1400,55,title+'fontColor=#172A3A;')
    cell(root,'china','China<br>4 archives · 298 turbines',90,110,620,85,section+'fillColor=#E9F3F9;strokeColor=#23749B;')
    cell(root,'europe','Europe<br>4 archives · 42 turbines',890,110,620,85,section+'fillColor=#FFF1E5;strokeColor=#C47731;')
    cell(root,'shared','Shared clock · quality flags · training-only scaling',430,215,740,48,text+'fontSize=17;fontColor=#425363;')
    cell(root,'detector','1  Detection<br>Intervals + turns',70,320,410,120,section+'fillColor=#E1F0F5;strokeColor=#95C8D5;')
    cell(root,'matching','2  Matching<br>One-to-one IoU',595,320,410,120,section+'fillColor=#E9F1DC;strokeColor=#AFC68D;')
    cell(root,'representation','3  Representation<br>Shapes + partitions',1120,320,410,120,section+'fillColor=#FFF0CB;strokeColor=#DFC16A;')
    cell(root,'evaltitle','4  Evaluation and decision',70,480,600,52,title+'align=left;fontSize=22;fontColor=#1B2430;')
    cell(root,'structure','Structural survival<br>ARI · NMI · coverage',70,570,410,115,section+'fillColor=#F0E9F5;strokeColor=#B49DC4;')
    cell(root,'physical','External process tracking<br>Wind · LiDAR',595,570,410,115,section+'fillColor=#F0E9F5;strokeColor=#B49DC4;')
    cell(root,'decision','Forecast-to-cost validation<br>Prices · storage',1120,570,410,115,section+'fillColor=#F0E9F5;strokeColor=#B49DC4;')
    cell(root,'references','Independent references: blind ratings · weather · LiDAR · prices',220,760,1160,72,note+'fillColor=#F5F6F7;strokeColor=#CCD2D8;fontSize=17;')
    edge(root,'e1','china','detector',[(400,260),(270,260),(270,320)])
    edge(root,'e2','europe','detector',[(1200,260),(270,260),(270,320)])
    edge(root,'e3','detector','matching')
    edge(root,'e4','matching','representation')
    edge(root,'e5','matching','structure',[(800,440),(800,525),(275,525),(275,570)])
    edge(root,'e6','representation','physical',[(1325,440),(1325,525),(800,525),(800,570)])
    edge(root,'e7','representation','decision',[(1325,440),(1325,570)])
    edge(root,'e8','references','structure',[(275,760),(275,685)],'edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;html=1;strokeWidth=1.5;endArrow=block;')
    edge(root,'e9','references','physical',[(800,760),(800,685)],'edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;html=1;strokeWidth=1.5;endArrow=block;')
    edge(root,'e10','references','decision',[(1325,760),(1325,685)],'edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;html=1;strokeWidth=1.5;endArrow=block;')
    tree=ET.ElementTree(mx);ET.indent(tree,space=' ');OUT.write_bytes(ET.tostring(mx,encoding='utf-8',xml_declaration=True))
    print(OUT)

if __name__=='__main__':main()
