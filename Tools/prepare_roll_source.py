"""Add a small skinned skeleton preview to an animation-only binary FBX.

Preserves source nodes, animation and connections. Never modifies the input.
"""
import math
import struct
import zlib
from pathlib import Path

SOURCE = Path(r"C:\Users\10645\Downloads\Stand To Roll.fbx")
DEST = Path(__file__).resolve().parents[1] / "Saved/RollImport/StandToRoll_SourcePreview.fbx"
b = SOURCE.read_bytes()
assert b.startswith(b"Kaydara FBX Binary")
version = struct.unpack_from("<I", b, 23)[0]
assert version >= 7500

class Node:
    def __init__(self, name, props=(), children=()):
        self.name, self.props, self.children = name, list(props), list(children)
    def child(self, name):
        return next(n for n in self.children if n.name == name)

def read_prop(p):
    start = p
    t = chr(b[p]); p += 1
    if t in "YCFDIL":
        f = dict(Y="h", C="?", F="f", D="d", I="i", L="q")[t]
        value = struct.unpack_from("<" + f, b, p)[0]; p += struct.calcsize(f)
    elif t in "SR":
        size = struct.unpack_from("<I", b, p)[0]; p += 4
        value = b[p:p+size]; p += size
        if t == "S": value = value.decode("utf8")
    elif t in "fdlibc":
        count, encoding, size = struct.unpack_from("<III", b, p); p += 12
        value = None; p += size
    else:
        raise ValueError(t)
    return (value, b[start:p]), p

def read_node(p):
    end, count, size, length = struct.unpack_from("<QQQB", b, p)
    if not end: return None, p + 25
    name = b[p+25:p+25+length].decode(); q = p+25+length
    props = []
    for _ in range(count):
        v, q = read_prop(q); props.append(v)
    children = []
    while q+25 <= end and any(b[q:q+25]):
        n, q = read_node(q); children.append(n)
    return Node(name, props, children), end

def P(value, kind=None):
    if kind in ("d", "i"):
        raw = struct.pack("<" + str(len(value)) + kind, *value)
        return (value, kind.encode()+struct.pack("<III", len(value), 0, len(raw))+raw)
    if isinstance(value, str):
        raw = value.encode(); return value, b"S"+struct.pack("<I", len(raw))+raw
    if isinstance(value, int): return value, b"L"+struct.pack("<q", value)
    return value, b"D"+struct.pack("<d", value)

def N(name, *values, children=()): return Node(name, [P(v) for v in values], children)
def A(name, values, kind="d"): return Node(name, [P(values, kind)])
def encode(n, start):
    name = n.name.encode(); props = b"".join(raw for _, raw in n.props)
    pos = start+25+len(name)+len(props); chunks=[]
    for child in n.children:
        chunk = encode(child, pos); chunks.append(chunk); pos += len(chunk)
    tail = b"\0"*25 if n.children else b""
    return struct.pack("<QQQB", pos+len(tail), len(n.props), len(props), len(name))+name+props+b"".join(chunks)+tail

roots=[]; pos=27
while any(b[pos:pos+25]):
    n,pos=read_node(pos); roots.append(n)
footer=b[pos+25:]
objects=next(n for n in roots if n.name=="Objects")
connections=next(n for n in roots if n.name=="Connections")
bones={n.props[0][0]:n for n in objects.children if n.name=="Model" and n.props[2][0]=="LimbNode"}
parents={c.props[1][0]:c.props[2][0] for c in connections.children if c.name=="C" and c.props[0][0]=="OO"}

def identity(): return [[float(i==j) for j in range(4)] for i in range(4)]
def mul(a,c): return [[sum(a[i][k]*c[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def rotation(v):
    x,y,z=map(math.radians,v); cx,sx=math.cos(x),math.sin(x); cy,sy=math.cos(y),math.sin(y); cz,sz=math.cos(z),math.sin(z)
    return mul(mul([[cz,-sz,0,0],[sz,cz,0,0],[0,0,1,0],[0,0,0,1]],[[cy,0,sy,0],[0,1,0,0],[-sy,0,cy,0],[0,0,0,1]]),[[1,0,0,0],[0,cx,-sx,0],[0,sx,cx,0],[0,0,0,1]])
world={}
def transform(bid):
    if bid in world:return world[bid]
    n=bones[bid]; props={p.props[0][0]:[v for v,_ in p.props[4:]] for p in n.child("Properties70").children}
    assert props.get("RotationOrder",[0])[0]==0
    assert all(abs(v)<1e-6 for v in props.get("PostRotation",[0,0,0]))
    m=mul(rotation(props.get("PreRotation",[0,0,0])),rotation(props.get("Lcl Rotation",[0,0,0])))
    for i,v in enumerate(props.get("Lcl Translation",[0,0,0])):m[i][3]=v
    for j,v in enumerate(props.get("Lcl Scaling",[1,1,1])):
        for i in range(3):m[i][j]*=v
    if parents.get(bid) in bones:m=mul(transform(parents[bid]),m)
    world[bid]=m;return m
def flat(m): return [m[i][j] for j in range(4) for i in range(4)]

base=900000000000
geo,model,skin,pose=base,base+1,base+2,base+3
vertices=[]; indices=[]; clusters=[]; poses=[]
for k,bid in enumerate(bones):
    m=transform(bid); x,y,z=[m[i][3] for i in range(3)]; start=len(vertices)//3
    for dx,dy,dz in [(0,0,1),(1,0,-1),(-1,0,-1),(0,1,0)]:vertices.extend([x+dx,y+dy,z+dz])
    for face in [(0,1,2),(0,3,1),(0,2,3),(1,3,2)]:indices.extend([start+face[0],start+face[1],-(start+face[2]+1)])
    cid=base+100+k
    clusters.append(N("Deformer",cid,f"PreviewCluster{k}\0\1SubDeformer","Cluster",children=[N("Version",100),N("UserData","",""),A("Indexes",list(range(start,start+4)),"i"),A("Weights",[1.0]*4),A("Transform",flat(identity())),A("TransformLink",flat(m))]))
    connections.children.extend([N("C","OO",cid,skin),N("C","OO",bid,cid)])
    poses.append(N("PoseNode",children=[N("Node",bid),A("Matrix",flat(m))]))
objects.children.extend([N("Geometry",geo,"SkeletonPreview\0\1Geometry","Mesh",children=[N("GeometryVersion",124),A("Vertices",vertices),A("PolygonVertexIndex",indices,"i")]),N("Model",model,"SkeletonPreview\0\1Model","Mesh",children=[N("Version",232),N("Properties70"),N("Shading",True),N("Culling","CullingOff")]),N("Deformer",skin,"SkeletonPreview\0\1Deformer","Skin",children=[N("Version",101),N("Link_DeformAcuracy",50.0)]),*clusters,N("Pose",pose,"PreviewBindPose\0\1Pose","BindPose",children=[N("Type","BindPose"),N("Version",100),N("NbPoseNodes",len(poses)+1),*poses,N("PoseNode",children=[N("Node",model),A("Matrix",flat(identity()))])])])
connections.children.extend([N("C","OO",geo,model),N("C","OO",model,0),N("C","OO",skin,geo)])
definitions=next(n for n in roots if n.name=="Definitions")
for typ in ['Geometry','Model','Deformer','Pose']:
    count=sum(n.name==typ for n in objects.children)
    entry=next((n for n in definitions.children if n.name=='ObjectType' and n.props[0][0]==typ),None)
    if entry:
        entry.child('Count').props=[P(count)]
    else:
        definitions.children.append(N('ObjectType',typ,children=[N('Count',count)]))
definitions.child('Count').props=[P(len(objects.children))]
chunks=[b[:27]]; pos=27
for n in roots:
    chunk=encode(n,pos);chunks.append(chunk);pos+=len(chunk)
chunks.extend([b"\0"*25,footer]);DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_bytes(b"".join(chunks))
print(f"Created {DEST}; {len(bones)} original bones, {len(vertices)//3} preview vertices. Original unchanged.")
