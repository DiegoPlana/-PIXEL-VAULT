"""Miniatura isométrica real de mallas FBX (binario o ASCII), usando Assimp/Pillow."""
import hashlib
import math
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

SIZE=(384,288)
MAX_FBX_BYTES=350*1024*1024
MAX_TRIANGLES=18000
MAX_POINTS=30000

def cache_path(record, directory):
    identity=f'mesh3|{record["path"]}|{record["size_bytes"]}|{record["mtime_ns"]}'
    return Path(directory)/("fbx-"+hashlib.sha256(identity.encode("utf-8")).hexdigest()+".png")

def read_geometry(path):
    import assimp_py
    flags=assimp_py.Process_Triangulate | assimp_py.Process_PreTransformVertices
    scene=assimp_py.import_file(str(path),flags)
    if not scene.meshes: raise ValueError("No hay geometría 3D en este FBX")
    points, triangles=[],[]
    for mesh in scene.meshes[:100]:
        verts=mesh.vertices
        if not len(verts): continue
        stride=max(1,math.ceil(len(verts)/max(1,MAX_POINTS//min(len(scene.meshes),10))))
        for i in range(0,len(verts),stride):
            if len(points)>=MAX_POINTS: break
            v=tuple(float(k) for k in verts[i][:3])
            if len(v)==3 and all(math.isfinite(k) for k in v): points.append(v)
        faces=getattr(mesh,"faces",None)
        if faces is None: continue
        remaining=MAX_TRIANGLES-len(triangles)
        if remaining<=0: break
        stride=max(1,math.ceil(len(faces)/remaining))
        for i in range(0,len(faces),stride):
            face=faces[i]
            if len(face)<3: continue
            try:
                tri=[tuple(float(v) for v in verts[int(k)][:3]) for k in face[:3]]
            except (IndexError,ValueError,TypeError): continue
            if all(math.isfinite(v) for p in tri for v in p):
                triangles.append(tri)
                if len(triangles)>=MAX_TRIANGLES: break
    return points,triangles

def render_mesh(points, triangles, size=SIZE):
    if not points and not triangles: raise ValueError("Modelo vacío")
    width,height=size
    image=Image.new("RGB",size,"#f0e7dc")
    painter=ImageDraw.Draw(image,"RGBA")
    painter.rounded_rectangle((12,12,width-12,height-12),radius=24,fill=(255,252,247,255))
    vertices=points or [v for tri in triangles for v in tri]
    vertices=[v for v in vertices if len(v)>=3 and all(math.isfinite(a) for a in v[:3])]
    if not vertices: raise ValueError("Geometría inválida")
    lo=[min(v[i] for v in vertices) for i in range(3)]
    hi=[max(v[i] for v in vertices) for i in range(3)]
    center=[(a+b)/2 for a,b in zip(lo,hi)]
    scale=max(1e-9,max(b-a for a,b in zip(lo,hi)))
    def project(v):
        x,y,z=((v[i]-center[i])/scale for i in range(3))
        return (width/2+(x-z)*width*.48,height/2+(-y*.84+(x+z)*.36)*height*.62,(x+z)*.67+y*.1)
    if triangles:
        polys=[]
        for face in triangles:
            if not all(math.isfinite(k) for v in face for k in v): continue
            coords=[project(p) for p in face]
            ax,ay,az=(face[1][i]-face[0][i] for i in range(3))
            bx,by,bz=(face[2][i]-face[0][i] for i in range(3))
            nx,ny,nz=ay*bz-az*by,az*bx-ax*bz,ax*by-ay*bx
            n=math.sqrt(nx*nx+ny*ny+nz*nz) or 1
            brightness=.4+.6*abs((nx*.35+ny*.72+nz*.61)/n)
            color=(int(193*brightness),int(112*brightness),int(135*brightness),255)
            polys.append((sum(p[2] for p in coords)/3,coords,color))
        polys.sort(key=lambda item:item[0],reverse=True)
        for _,coords,color in polys:
            painter.polygon([(p[0],p[1]) for p in coords],fill=color,outline=(68,40,66,130),width=1)
    else:
        for vertex in points:
            u,v,_=project(vertex)
            painter.ellipse((u-1.5,v-1.5,u+1.5,v+1.5),fill=(197,99,111,220))
    painter.rounded_rectangle((22,height-52,98,height-22),radius=10,fill=(53,33,61,255))
    painter.text((40,height-44),"FBX",fill=(255,237,222,255))
    return image

def render_fbx(record, directory):
    source=Path(record["path"])
    if not source.is_file(): raise FileNotFoundError(source)
    if source.stat().st_size>MAX_FBX_BYTES: raise ValueError("FBX demasiado grande")
    result=cache_path(record,directory)
    if result.exists(): return result
    points,triangles=read_geometry(source)
    image=render_mesh(points,triangles)
    result.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=result.parent,suffix=".png",delete=False) as handle:
            temporary=Path(handle.name)
        image.save(temporary,format="PNG",optimize=True)
        os.replace(temporary,result)
    finally:
        if temporary and temporary.exists(): temporary.unlink()
    return result
