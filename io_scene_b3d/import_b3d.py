#!/usr/bin/python3
# by Joric, https://github.com/joric/io_scene_b3d

try:
    from B3DParser import *
except:
    pass

try:
    from .B3DParser import *
    import bpy
    import mathutils
    from bpy_extras.image_utils import load_image
    from bpy_extras.io_utils import unpack_list, unpack_face_list
    import bmesh
except:
    pass

def flip(v):
    return ((v[0],v[2],v[1]) if len(v)<4 else (v[0], v[1],v[3],v[2]))

def flip_all(v):
    return [y for y in [flip(x) for x in v]]

armatures = []
bonesdata = []
weighting = {}
bones_ids = {}
bones_node = None

def make_skeleton(node):

    objName = 'armature'
    a = bpy.data.objects.new(objName, bpy.data.armatures.new(objName))

    armatures.append(a);
    ctx.scene.objects.link(a)

    for i in bpy.context.selected_objects: i.select = False #deselect all objects

    a.select = True
    a.show_x_ray = True
    a.data.draw_type = 'STICK'
    bpy.context.scene.objects.active = a

    bpy.ops.object.mode_set(mode='EDIT',toggle=False)

    bones = {}

    # copy bones positions from precalculated objects
    for bone_id, (name, pos, rot, parent_id) in enumerate(bonesdata):
        if name not in bpy.data.objects:
            return

        ob = bpy.data.objects[name]
        #if parent_id != -1: name = ob.parent.name
        bone = a.data.edit_bones.new(name)
        bones[bone_id] = bone
        v = ob.matrix_world.to_translation()

        # use short segment as a bone (smd-like hierarchy), will convert later
        bone.tail = ob.matrix_world.to_translation()
        bone.head = (v[0]-0.01,v[1],v[2])

        if parent_id != -1:
            bone.parent = bones[parent_id]
            #bone.head = ob.parent.matrix_world.to_translation()

    # delete all objects with the same names as the bones
    for name, pos, rot, parent_id in bonesdata:
        bpy.data.objects.remove(bpy.data.objects[name])

    bpy.ops.object.mode_set(mode='OBJECT')

    for i in bpy.context.selected_objects: i.select = False #deselect all objects

    # get parent mesh (hardcoded so far)
    objName = 'anim'
    if objName in bpy.data.objects.keys():
        ob = bpy.data.objects[objName]
    else:
        return

    # apply armature modifier
    modifier = ob.modifiers.new(type="ARMATURE", name="armature")
    modifier.object = a

    # create vertex groups
    for bone in a.data.bones.values():
        group = ob.vertex_groups.new(bone.name)
        if bone.name in weighting.keys():
            for vertex_id, weight in weighting[bone.name]:
                #vertex_id = remaps[objName][vertex_id]
                group_indices = [vertex_id]
                group.add(group_indices, weight, 'REPLACE')


    actionName = 'default_action'
    action = bpy.data.actions.new(actionName)
    action.use_fake_user = True

    a.animation_data_create()
    a.animation_data.action = action


    #action.fps = 30fps if fps else 30
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 1

    #ops.object.mode_set(mode='POSE')
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = node.frames - 1


    """
    bone_string = 'Bip01'
    bone = {'name' : bone_string}

    curvesLoc = None
    curvesRot = None
    bone_string = "pose.bones[\"{}\"].".format(bone.name)
    group = action.groups.new(name=bone.name)

    for keyframe in range(node.frames):
        if curvesLoc and curvesRot: break
        if keyframe.pos and not curvesLoc:
            curvesLoc = []
            for i in range(3):
                curve = action.fcurves.new(data_path=bone_string + "location",index=i)
                curve.group = group
                curvesLoc.append(curve)
        if keyframe.rot and not curvesRot:
            curvesRot = []
            for i in range(3 if smd.rotMode == 'XYZ' else 4):
                curve = action.fcurves.new(data_path=bone_string + "rotation_" + ("euler" if smd.rotMode == 'XYZ' else "quaternion"),index=i)
                curve.group = group
                curvesRot.append(curve)


    for i in range(3):
        curve = action.fcurves.new(data_path=bone_string + "location",index=i)
        group = action.groups.new(name=bone_name)
        curve.group = group

    location = (10,50,100)
    for frame in range(node.frames):
        for i in range(3):
            curve.keyframe_points.add(1)
            curve.keyframe_points[-1].co = [frame, location[i]]

    curve = action.fcurves.new(data_path=bone_string + "rotation_quaternion",index=i)
    group = action.groups.new(name=bone_name)
    curve.group = group

    rotation = (1,0,1,0)
        for i in range(4):
          curvesRot[i].keyframe_points.add(1)
          curvesRot[i].keyframe_points[-1].co = [keyframe.frame, bone.rotation_quaternion[i]]

    #curve = action.fcurves.new(data_path=bone_string + "rotation_quaternion",index=i)
    """


def assign_material_slots(ob, node, mat_slots):
    bpy.context.scene.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    me = ob.data
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    start = 0
    for face in node.faces:
        numfaces = len(face.indices)
        for i in range(numfaces):
            bm.faces[start+i].material_index = mat_slots[face.brush_id]
        start += numfaces
    bmesh.update_edit_mesh(me, True)
    bpy.ops.object.mode_set(mode='OBJECT')

def postprocess(ob, mesh, node):
    ops = bpy.ops
    bpy.context.scene.objects.active = ob
    ops.object.mode_set(mode='EDIT')
    ops.mesh.select_all(action='SELECT')

    ops.mesh.remove_doubles(threshold=0)
    bpy.ops.mesh.tris_convert_to_quads()

    ops.mesh.select_all(action='DESELECT')
    ops.object.mode_set(mode='OBJECT')

    # smooth normals
    mesh.use_auto_smooth = True
    mesh.auto_smooth_angle = 3.145926*0.2
    ops.object.select_all(action="SELECT")
    ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='OBJECT')

def import_mesh(node):
    mesh = bpy.data.meshes.new(node.name)

    # join face arrays
    faces = []
    for face in node.faces:
        faces.extend(face.indices)

    # create mesh from data
    mesh.from_pydata(flip_all(node.vertices), [], flip_all(faces))

    # assign normals
    mesh.vertices.foreach_set('normal', unpack_list(node.normals))

    # create object from mesh
    ob = bpy.data.objects.new(node.name, mesh)

    # assign uv coordinates
    vert_uvs = [(0,0) if len(uv)==0 else (uv[0], 1-uv[1]) for uv in node.uvs]
    me = ob.data
    me.uv_textures.new()
    me.uv_layers[-1].data.foreach_set("uv", [uv for pair in [vert_uvs[l.vertex_index] for l in me.loops] for uv in pair])

    # assign materials and textures
    mat_slots = {}
    for face in node.faces:
        if face.brush_id in materials:
            mat = materials[face.brush_id]
            ob.data.materials.append(mat)
            mat_slots[face.brush_id] = len(ob.data.materials)-1
            for uv_face in ob.data.uv_textures.active.data:
                if mat.active_texture:
                    uv_face.image = mat.active_texture.image

    # link object to scene
    ctx.scene.objects.link(ob)

    if len(node.faces)>1:
        assign_material_slots(ob, node, mat_slots)

    #postprocess(ob, mesh, node) # breaks weighting

    return ob

def import_node(node, parent):
    global armatures, bonesdata, weighting, bones_ids, bones_node

    if 'vertices' in node and 'faces' in node:
        ob = import_mesh(node)
    else:
        ob = bpy.data.objects.new(node.name, None)
        ctx.scene.objects.link(ob)

    ob.rotation_mode='QUATERNION'
    ob.rotation_quaternion = flip(node.rotation)
    ob.scale = flip(node.scale)
    ob.location = flip(node.position)

    if parent:
        ob.parent = parent

    if 'bones' in node:
        bone_name = node.name

        # we need numeric parent_id for bonesdata
        parent_id = -1
        if parent:
            if parent.name in bones_ids.keys():
                parent_id = bones_ids[parent.name]
        bonesdata.append([bone_name,None,None,parent_id])
        bones_ids[bone_name] = len(bonesdata)-1

        # fill weighting map for later use
        w = []
        for vert_id, weight in node['bones']:
            w.append((vert_id, weight))
        weighting[bone_name] = w

    if 'bones' in node and not bones_node:
        print(bones_node)
        bones_node = node

    return ob

def walk(root, parent=None):
    for node in root.nodes:
        ob = import_node(node, parent)
        walk(node, ob)

def load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=10.0,
             IMAGE_SEARCH=True,
             APPLY_MATRIX=True,
             global_matrix=None):
    global ctx
    ctx = context
    data = B3DTree().parse(filepath)

    global images, materials
    images = {}
    materials = {}

    # load images
    dirname = os.path.dirname(filepath)
    for i, texture in enumerate(data['textures'] if 'textures' in data else []):
        texture_name = os.path.basename(texture['name'])
        for mat in data.materials:
            if mat.tids[0]==i:
                images[i] = load_image(texture_name, dirname, check_existing=True,
                    place_holder=False, recursive=IMAGE_SEARCH)

    # create materials
    for i, mat in enumerate(data.materials if 'materials' in data else []):
        name = mat.name
        material = bpy.data.materials.new(name)
        material.diffuse_color = mat.rgba[:-1]
        material.alpha = mat.rgba[3]
        material.use_transparency = material.alpha < 1
        texture = bpy.data.textures.new(name=name, type='IMAGE')
        tid = mat.tids[0]
        if tid in images:
            texture.image = images[tid]
            mtex = material.texture_slots.add()
            mtex.texture = texture
            mtex.texture_coords = 'UV'
            mtex.use_map_color_diffuse = True
        materials[i] = material

    global armatures, bonesdata, weighting, bones_ids, bones_node
    walk(data)
    if data.frames:
        make_skeleton(data)

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

filepath = 'C:/Games/GnomE/media/models/gnome/model.b3d'
#filepath = 'C:/Games/GnomE/media/levels/level1.b3d'
#filepath = 'C:/Games/GnomE/media/models/gnome/go.b3d'
#filepath = 'C:/Games/GnomE/media/models/flag/flag.b3d'

if __name__ == "__main__":
    p = B3DDebugParser()
    p.parse(filepath)
