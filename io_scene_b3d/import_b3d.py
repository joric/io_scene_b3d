#!/bin/python3

#2011-04-19 Glogow Poland Mariusz Szkaradek
#Almost completely rewritten by Joric

try:
    import bpy
    import mathutils
    from bpy_extras.image_utils import load_image
    from bpy_extras.io_utils import unpack_list, unpack_face_list
    import bmesh
    blender = True
except:
    blender = False

debug = False
postprocess = True

def indent(level):
     print(' '*level, end='')

data = {'nodes':[],'version':0,'brushes':[],'textures':[]}

images = {}
materials = {}

import struct, os
from struct import *
from math import *

def vertexuv():
    mesh.vertexUV = 1
    for m in range(len(mesh.verts)):
        mesh.verts[m].uvco = Vector(uvcoord[m])
    mesh.update() 
    mesh.faceUV = 1
    for fc in mesh.faces: fc.uv = [v.uvco for v in fc.verts];fc.smooth = 1
    mesh.update()    

def drawmesh(name): 
    global obj,mesh
    mesh = bpy.data.meshes.new(name)
    mesh.verts.extend(vertexes)
    mesh.faces.extend(faceslist,ignoreDups=True)
    if len(uvcoord)!=0:
        #make_faceuv()
        vertexuv()
    scene = bpy.data.scenes.active
    obj = scene.objects.new(mesh,name)
    mesh.recalcNormals()
    make_vertex_group()
    mesh.update()

def make_vertex_group():
    for id_0 in range(len(weighting)):
        data = weighting[id_0]
        #print data
        for id_1 in range(2):
            grint = data[0][id_1]
            #try: 
            #gr = fix_groups[gr]
            gr = str(grint)
            #gr = bonenames[armature_name][gr]
            w  = data[1][id_1]/100.0
            if grint!=-1:
                if gr not in mesh.getVertGroupNames():
                    mesh.addVertGroup(gr)    
                    mesh.update()
                mesh.assignVertsToGroup(gr,[id_0],w,1)
            #except:
            #    pass 
    mesh.update()

def b(n):
    return struct.unpack(n*'b', plik.read(n))
def B(n):
    return struct.unpack(n*'B', plik.read(n))
def h(n):
    return struct.unpack(n*'h', plik.read(n*2))
def H(n):
    return struct.unpack(n*'H', plik.read(n*2))
def i(n):
    return struct.unpack(n*'i', plik.read(n*4))
def f(n):
    return struct.unpack(n*'f', plik.read(n*4))

def word(long):
    s=b''
    for j in range(0,long):
        lit = struct.unpack('c',plik.read(1))[0]
        if ord(lit)!=0:
            s+=lit
            if len(s)>300:
                break
    return s.decode()

def check_armature():
    global armobj,newarm
    armobj=None
    newarm=None
    scn = Scene.GetCurrent()
    scene = bpy.data.scenes.active
    for object in scene.objects:
        if object.getType()=='Armature':
            if object.name == 'armature':
                scene.objects.unlink(object)
    for object in bpy.data.objects:
        if object.name == 'armature':
            armobj = Blender.Object.Get('armature')
            newarm = armobj.getData()
            newarm.makeEditable()    
            for bone in newarm.bones.values():
                del newarm.bones[bone.name]
            newarm.update()
    if armobj==None: 
        armobj = Blender.Object.New('Armature','armature')
    if newarm==None: 
        newarm = Armature.New('armature')
        armobj.link(newarm)
    scn.link(armobj)
    newarm.drawType = Armature.STICK
    armobj.drawMode = Blender.Object.DrawModes.XRAY
    for object in scene.objects:
        if 'model' in object.name and object.getType()=='Mesh':
                armobj.makeParentDeform([object],1,0)

def make_bone(): 
    newarm.makeEditable()
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[bone_id]
        bonename = bonedata[0]
        eb = Armature.Editbone() 
        newarm.bones[bonename] = eb
    newarm.update()

def make_bone_parent():
    newarm.makeEditable()
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[bone_id]
        parent_id = bonedata[3]
        bonename = bonedata[0]    
        if parent_id !=-1:
            bone = newarm.bones[bonename]  
            boneparent = newarm.bones[bonesdata[parent_id][0]]
            bone.parent = boneparent
    newarm.update()

def make_bone_position():
    newarm.makeEditable()
    for bone_id in range(len(bonesdata)):
        bonedata = bonesdata[bone_id]
        namebone = bonedata[0]
        pos = bonedata[1] 
        rot = bonedata[2] 
        qx,qy,qz,qw = rot[0],rot[1],rot[2],rot[3]
        rot = Quaternion(qw,qx,qy,qz)
        rot = rot.toMatrix().invert() 
        bone = newarm.bones[namebone]
        #if bone.parent:
        #    bone.head =    bone.parent.head+Vector(pos) * bone.parent.matrix
            #tempM = rot * bone.parent.matrix 
            #bone.matrix = tempM
        #else:
        bone.head = Vector(pos)
        bone.matrix = rot
        bvec = bone.tail- bone.head
        bvec.normalize()
        bone.tail = bone.head + 0.01 * bvec
    newarm.update()

def skeleton():
    check_armature(),make_bone(),make_bone_parent();make_bone_position()

"""
def find_0():
    s=b''
    while(True):
        litera = struct.unpack('c',plik.read(1))[0]
        if  litera=='\x00':
            break
        else:
            s+=litera
    return str(s)

def s3d():
    global vertexes,faceslist,weighting,uvcoord

    print("Signature:", word(4))
    data = H(9)
    print("Data:", data)
    images = []
    materials = []

    nTextures = data[2]
    print("Textures", nTextures)

    for m in range(nTextures):
        image_name = find_0().split('.')[0]
        images.append(image_name+'.dds')
        for file_name in g:
            if image_name in file_name and '.dds' in file_name:
                print("Texture:", file_name)
                if file_name not in Blender.Image.Get():
                    Blender.Image.Load(dir+os.sep+file_name)     
        B(9)

    nMaterials = data[3]
    print("Materials", nMaterials);
    for m in range(nMaterials):
        material_name = find_0()
        materials.append(material_name)
        mat = Material.New(material_name)
        image_id = H(1)[0] 
        try:
            tex = Texture.New('diff')
            tex.setType('Image')
            #tex.image = Blender.Image.Get(images[image_id])
            tex.image =  Blender.Image.Load(dir+os.sep+images[image_id])
            mat.setTexture(0,tex,Texture.TexCo.UV,Texture.MapTo.COL)
        except:
            pass

        data1 = H(4)
        print("Mat data:", data1)
        f(3)
        if data1[2] == 1: 
            print(B(63))
        elif data1[2] == 3: 
            print(B(64))
        else:
            print(B(55))

    nObjects = data[4]
    print("Objects", nObjects)

    for m in range(nObjects):
        print("Find01", find_0())
        print("Find01", find_0())
        mat_id = H(1)[0]

        print("Objects:", B(24), f(4))

        B(1)
        data2 = H(4)
        print(data2)
        vertexes = []
        faceslist = []
        weighting = []
        uvcoord = []
        for n in range(data2[1]):
            back = plik.tell() 
            #print m,f(3) 
            vertexes.append(f(3))
            f(3)#normals
            uvcoord.append([f(1)[0],-f(1)[0]])
            plik.seek(back+40)
        for n in range(data2[2]):
            faceslist.append(H(3))
        for n in range(data2[1]):
            weighting.append([i(2),B(2)])  
            #break
        #break  
        drawmesh('model-'+str(m))
        mesh.materials+=[Material.Get(materials[mat_id])]
    print(plik.tell())

def b3d():
    global bonesdata
    bonesdata = []

    print("File signature:", word(4))

    B(5)
    nBones = i(1)[0]

    print("Bones:", nBones)

    for m in range(nBones):
        bone_name = find_0()
        f(7)
        pos = f(3)
        rot = f(4)
        f(6)
        i(2)
        parent_id = i(1)[0]
        bonesdata.append([bone_name,pos,rot,parent_id]) 

    skeleton()
    scene = bpy.data.scenes.active
    for object in scene.objects:
        if 'model' in object.name and object.getType()=='Mesh':
            mesh = object.getData(mesh=1)
            for m in range(len(bonesdata)):
                print(object.name,m)
                if str(m) in mesh.getVertGroupNames():
                    mesh.renameVertGroup(str(m),bonesdata[m][0])
            armobj.makeParentDeform([object],1,0)
    print(plik.tell())
"""


def word(long):
    s=b''
    for j in range(0,long):
        lit = struct.unpack('c',plik.read(1))[0]
        if ord(lit)!=0:
            s+=lit
            if len(s)>300:
                break
    return s.decode()

def find_0():
    s=b''
    while(True):
        litera = struct.unpack('c',plik.read(1))[0]
        if  litera==b'\x00':
            break
        else:
            s+=litera
    return s.decode(errors='ignore')


def next_chunk():
    pos = plik.tell()
    try:
        sig = word(4)
        size = i(1)[0]
        #if debug: print ("Chunk: %s, pos: %d, size: %d" % (sig, pos, size))
        return sig, pos, size, pos+size+8
    except struct.error:
        #print("EOF")
        return '',0,0,0

def parse_node(next, level=0):
    name = find_0()
    p, s, r = f(3),f(3),f(4)

    #if debug: indent(level); print(name)
    #print('position/scale/rotation', p,s,r)

    node = {'name':name, 'position':p, 'scale':s,'rotation':r,
        'meshes':[], 'vertices':[]}

    while plik.tell()<next:
        sig, pos, size, nextc = next_chunk()

        if sig=='ANIM':
            flags, frames = i(2)
            fps = f(1)[0]

            node['anim'] = {'flags':flags, 'frames':frames, 'fps':fps}
            #print('flags: %d, frames: %d, fps %.02f' % (flags, frames, fps))

        elif sig=='KEYS':
            flags = i(1)[0]
            keys = []
            while plik.tell()<nextc:
                frame = i(1)[0]
                p = f(3) if flags&1 else []
                s = f(3) if flags&2 else []
                r = f(4) if flags&4 else []
                keys.append((frame,p,s,r))

                key = {'frame':frame}
                if len(p): key['position'] = p
                if len(r): key['rotation'] = r
                if len(s): key['scale'] = s
                if 'keys' not in node.keys():
                    node['keys']=[]
                node['keys'].append(key)

            #print(keys)
            #print('total keys', name, len(keys), keys)

        elif sig=='BONE':
            bones = []
            while plik.tell()<nextc:
                vertex_id = i(1)[0]
                weight = f(1)[0]
                bones.append((vertex_id, weight))
            #print(bones)

            node['bones'] = bones

        elif sig=='MESH':
            brush_id = i(1)[0]

            sig, pos, size, nextv = next_chunk()
            if sig!='VRTS': break

            flags, tcs, tcss = i(3)
            #print(flags, tcs, tcss)

            vertices = []
            while plik.tell()<nextv:
                v = f(3)
                n = f(3) if flags&1 else []
                rgba = f(4) if flags&2 else []
                tex_coords = f(tcs*tcss)
                vertices.append((v,n,rgba,tex_coords))

            #print(vertices)
            #print('brush_id', brush_id, 'vertices', len(vertices))

            node['vertices'] = vertices

            while plik.tell()<nextc:
                sig, pos, size, nextt = next_chunk()
                if sig!='TRIS': break

                brush_id = i(1)[0]
                indices = []
                while plik.tell()<nextt:
                    vertex_id = i(3)
                    indices.append(vertex_id)

                node['meshes'].append({'brush_id':brush_id, 'indices':indices})

                #print('brush_id', brush_id, 'ids', len(ids))

        elif sig=='NODE':
            if 'nodes' not in node.keys():
                node['nodes'] = []
            node['nodes'].append(parse_node(nextc, level+1))

        plik.seek(nextc)

    return(node)

def b3d():
    level = 0
    data['nodes'] = []
    data['brushes'] = []
    data['textures'] = []

    while True:
        sig, pos, size, next = next_chunk()

        if sig=='':
            break

        elif sig=='BB3D':
            ver = i(1)[0]
            data['version'] = ver
            continue

        elif sig=='TEXS':
            while plik.tell()<next:
                name = find_0()
                flags, blend = i(2)
                pos = f(2)
                scale = f(2)
                rot = f(1)[0]
                data['textures'].append({'name':name,'pos':pos,'scale':scale,'rotation':rot})
                #print('Texture', name)

        elif sig=='BRUS':
            n_texs = i(1)[0]
            while plik.tell()<next:
                name = find_0()
                rgba = f(4)
                shine = f(1)[0]
                blend, fx = i(2)
                texture_ids = i(n_texs)
                #print('Brush', name)
                data['brushes'].append({'name':name, 'rgba':rgba,'shine':shine,
                    'blend':blend,'fx':fx,'texture_ids':texture_ids})

        elif sig=='NODE':
            data['nodes'].append(parse_node(next, level))

        plik.seek(next)

def flip(v):
    #return v
    return ((v[0],v[2],v[1]) if len(v)<4 else (v[0], v[1],v[3],v[2]))

def import_node(node, parent):

    objName = node['name']

    verts = []
    coords = {}
    index_tot = 0
    faces_indices = []
    facemats = []
    normals = []

    for v,n,rgba,tex_coords in node['vertices']:
        verts.append(flip(v))
        if n: normals.append(flip(n))

    for m in node['meshes']:
        for i in m['indices']:
            faces_indices.append(flip(i))
            facemats.append(m['brush_id'])

    mesh = bpy.data.meshes.new(objName)
    mesh.from_pydata(verts, [], faces_indices)

    # set normals
    mesh.vertices.foreach_set('normal', unpack_list(normals))

    """
    if len(mesh.polygons): print('poly normal before', mesh.polygons[0].normal)
    mesh.validate()
    mesh.update()
    mesh.calc_normals() # does not work
    #mesh.calc_normals_split()
    #mesh.update(calc_edges=True)
    if len(mesh.polygons): print('poly normal after', mesh.polygons[0].normal)
    """

    ob = bpy.data.objects.new(objName, mesh)

    if parent:
        ob.parent = parent

    pos = node['position']
    rot = node['rotation']
    scale = node['scale']

    ob.rotation_mode='QUATERNION'
    ob.rotation_quaternion = flip(rot)
    ob.scale = flip(scale)
    ob.location = flip(pos)

    # import uv coordinates
    vert_uvs = [(0,0) if len(uv)==0 else (uv[0],1-uv[1]) for v,n,rgba,uv in node['vertices']]
    me = ob.data
    me.uv_textures.new()
    me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [vert_uvs[l.vertex_index] for l in me.loops] for uv in pair])

    ctx.scene.objects.link(ob)
    ops = bpy.ops
    bpy.context.scene.objects.active = ob

#    for i in facemats:
#        if i in images.keys() and i<len(me.uv_textures[0].data):
#            me.uv_textures[0].data[i].image = images[i]

    # assign materials
    mat_id = facemats[0] if len(facemats) else -1
    if mat_id in materials.keys():
        mat = materials[mat_id]
        if ob.data.materials:
            ob.data.materials[0] = mat
        else:
            ob.data.materials.append(mat)

        # assign uv images
        for uv_face in ob.data.uv_textures.active.data:
            if mat.active_texture:
                uv_face.image = mat.active_texture.image

    """
    bpy.ops.object.mode_set(mode = 'EDIT')          # Go to edit mode to create bmesh
    ob = bpy.context.object                         # Reference to selected object

    bm = bmesh.from_edit_mesh(ob.data)              # Create bmesh object from object mesh

    for i, face in enumerate(bm.facemats):        # Iterate over all of the object's faces
        face.material_index = 0

    ob.data.update()                            # Update the mesh from the bmesh data
    bpy.ops.object.mode_set(mode = 'OBJECT')    # Return to object mode</pre>
    """


    """
    # dump vertices
    me = ob.data
    uv_layer = me.uv_layers.active.data
    for poly in me.polygons:
        print("Polygon index: %d, length: %d" % (poly.index, poly.loop_total))

        # range is used here to show how the polygons reference loops,
        # for convenience 'poly.loop_indices' can be used instead.
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            print("    Vertex: %d" % me.loops[loop_index].vertex_index)
            print("    UV: %r" % uv_layer[loop_index].uv)
    """

    if len(node['meshes']) and postprocess:

        ops.object.mode_set(mode='EDIT')
        ops.mesh.select_all(action='SELECT')

        ops.mesh.remove_doubles(threshold=0)
        #bpy.ops.mesh.tris_convert_to_quads()

        ops.mesh.select_all(action='DESELECT')
        ops.object.mode_set(mode='OBJECT')


        # smooth normals
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 3.145926*0.2
        ops.object.select_all(action="SELECT")
        ops.object.shade_smooth()

    return ob

def parse_nodes(nodes, level=0, parent=None):
    for node in nodes:
        ob = None

        if debug:
            keys = '' if 'keys' not in node.keys() else '\tkeys: '+str(len(node['keys']))
            fr = '\trot: '+','.join(['%.2f' % x for x in node['rotation']])
            fp = '\tpos: '+','.join(['%.2f' % x for x in node['position']])
            v = '\tvertices:'+str(len(node['vertices']))
            m = '\tmeshes:'+str(len(node['meshes']))
            indent(level)
            print(node['name'], fr, fp, keys, v, m)

        if blender:
            ob = import_node(node, parent)

        if 'nodes' in node.keys():
            parse_nodes(node['nodes'], level+1, ob)


def load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=10.0,
             IMAGE_SEARCH=True,
             APPLY_MATRIX=True,
             global_matrix=None):
    global plik,g,dir,ctx,data,images,materials
    print('Loading', filepath)
    plik = open(filepath,'rb')
    file = os.path.basename(filepath)
    dir = os.path.dirname(filepath)
    g = os.listdir(dir)
    b3d()
    ctx = context

    # load images
    for i, texture in enumerate(data['textures']):
        texture_name = os.path.basename(texture['name'])
        for brush in data['brushes']:
            if brush['texture_ids'][0]==i:
                images[i] = load_image(texture_name, dir, check_existing=True,
                    place_holder=False, recursive=IMAGE_SEARCH)

    # create materials
    for i, brush in enumerate(data['brushes']):
        name = brush['name']
        material = bpy.data.materials.new(name)
        material.diffuse_color = brush['rgba'][:-1]
        material.alpha = brush['rgba'][3]
        material.use_transparency = material.alpha < 1
        texture = bpy.data.textures.new(name=name, type='IMAGE')
        tid = brush['texture_ids'][0]
        if tid in images.keys():
            texture.image = images[tid]
            mtex = material.texture_slots.add()
            mtex.texture = texture
            mtex.texture_coords = 'UV'
            mtex.use_map_color_diffuse = True
        materials[i] = material

    parse_nodes(data['nodes'])

def load(operator,
         context,
         filepath="",
         constrain_size=0.0,
         use_image_search=True,
         use_apply_transform=True,
         global_matrix=None,
         ):

    load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=constrain_size,
             IMAGE_SEARCH=use_image_search,
             APPLY_MATRIX=use_apply_transform,
             global_matrix=global_matrix,
             )

    return {'FINISHED'}

def import_b3d(filepath):
    global plik,g,dir,data
    plik = open(filepath,'rb')
    b3d()

    import json
    print(json.dumps(data,separators=(',',':'),indent=1))

    parse_nodes(data['nodes'])

#filepath = 'C:/Games/GnomE/media/models/gnome/model.b3d'
filepath = 'C:/Games/GnomE/media/levels/level1.b3d'

if __name__ == "__main__":
    if not blender:
        import_b3d(filepath)

