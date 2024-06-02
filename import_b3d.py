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

VERTEX_COLORS = 'vertex_colors'
material_mapping = {}
brush_mapping = {}
weighting = {}

armatures = []
weighting = {}
bones_ids = {}
bones_node = None

blender_bones = True

# taken from https://github.com/blitz-research/blitz3d/blob/master/gxruntime/gxscene.h#L38

def make_skeleton(node):
    global armatures

    objName = 'armature'
    a = bpy.data.objects.new(objName, bpy.data.armatures.new(objName))

    armatures.append(a);
    ctx.scene.collection.objects.link(a)

    for i in bpy.context.selected_objects: i.select_set(state=False)

    a.select_set(state=True)
    a.show_in_front = True
    a.data.display_type = 'STICK'

    bpy.context.view_layer.objects.active = a

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
        try:
            bpy.data.objects.remove(bpy.data.objects[name])
        except:
            pass

    bpy.ops.object.mode_set(mode='OBJECT')

    #for i in bpy.context.selected_objects: i.select = False #deselect all objects
    for i in bpy.context.selected_objects: i.select_set(state=False) #deselect all objects #2.8 fails

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
        group = ob.vertex_groups.new(name=bone.name)
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


    ## ANIMATION!
    bone_string = 'Bip01'

    curvesLoc = None
    curvesRot = None
    bone_string = "pose.bones[\"{}\"].".format(bone.name)
    group = action.groups.new(name=bone_string)

    for bone_id, (name, keys, rot, parent_id) in enumerate(bonesdata):
        for frame in range(node.frames):
            # (unoptimized) walk through all keys and select the frame
            for key in keys:
                if key.frame==frame:
                    pass
                    #print(name, key)
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

def select_recursive(root):
    for c in root.children:
        select_recursive(c)
    root.select_set(state=True)

def make_armature_recursive(root, a, parent):
    bone = a.data.edit_bones.new(root.name)
    bone.parent = parent

    # set tail to head with a little offset, similar to smd
    t = root.matrix_world.to_translation()
    bone.head = t
    bone.tail = t + mathutils.Vector((-0.1,0,0))

    # there's no information about bone length so there's some heuristics:
    # * it's 0 children, use a small offset similar to SMD models
    # * it's 1 or 2 children, use average position
    # * it's 3+ children, use average position excluding symmetrical bones
    if blender_bones:
        import re
        n = t-parent.head if parent else mathutils.Vector((1,0,0))
        n.normalize()
        w = [(c.matrix_world.to_translation(),c.name) for c in root.children]
        avg_pos = lambda p:[sum(v[0][i]for v in p)/len(p) for i in range(3)] if len(w) else t+n*0.15
        bone.tail = avg_pos(tuple(filter(lambda v:len(w)<3 or not re.match(r'.*[\s\.\_][L|R][\s$]', v[1], re.IGNORECASE), w)))

    for c in root.children:
        make_armature_recursive(c, a, bone)

def make_armatures():
    global ctx
    global imported_armatures, weighting

    for dummy_root in imported_armatures:
        objName = 'armature'
        a = bpy.data.objects.new(objName, bpy.data.armatures.new(objName))
        ctx.scene.collection.objects.link(a)
        for i in bpy.context.selected_objects: i.select_set(state=False)
        a.select_set(state=True)
        a.show_in_front = True

        a.data.display_type = 'OCTAHEDRAL' if blender_bones else 'STICK'

        bpy.context.view_layer.objects.active = a

        bpy.ops.object.mode_set(mode='EDIT',toggle=False)
        make_armature_recursive(dummy_root, a, None)
        bpy.ops.object.mode_set(mode='OBJECT',toggle=False)

        # set ob to mesh object
        ob = dummy_root.parent
        a.parent = ob

        # delete dummy objects hierarchy
        for i in bpy.context.selected_objects:
            i.select_set(state=False)
        select_recursive(dummy_root)
        bpy.ops.object.delete(use_global=True)

        # apply armature modifier
        modifier = ob.modifiers.new(type="ARMATURE", name="armature")
        modifier.object = a

        # create vertex groups
        for bone in a.data.bones.values():
            group = ob.vertex_groups.new(name=bone.name)
            if bone.name in weighting.keys():
                for vertex_id, weight in weighting[bone.name]:
                    group_indices = [vertex_id]
                    group.add(group_indices, weight, 'REPLACE')
        a.parent.data.update()

def import_bone(node, parent=None):
    global imported_armatures, weighting

    # add dummy objects to calculate bone positions later
    ob = bpy.data.objects.new(node.name, None)

    # fill weighting map for later use
    w = []
    for vert_id, weight in node['bones']:
        w.append((vert_id, weight))
    weighting[node.name] = w

    # check parent, add root armature
    if parent and parent.type=='MESH':
        imported_armatures.append(ob)

    return ob

def import_mesh(node, parent):
    global material_mapping
    global brush_mapping

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
    bpymesh = ob.data
    uvs = [(0,0) if len(uv)==0 else (uv[0], 1-uv[1]) for uv in node.uvs]

    #uvlist = [i for poly in bpymesh.polygons for vidx in poly.vertices for i in uvs[vidx]]

    uvlist = []
    for poly in bpymesh.polygons:
        for vidx in poly.vertices:
            if vidx>=len(uvs):
                continue
            for i in uvs[vidx]:
                uvlist.append(i)

    bpymesh.uv_layers.new().data.foreach_set('uv', uvlist)

    # assign vertex colors
    if node.rgba:
        colattr = ob.data.color_attributes.new(name=VERTEX_COLORS, type='FLOAT_COLOR', domain='POINT')
        colattr.data.foreach_set('color', unpack_list(node.rgba))

    # assign material_indexes
    poly = 0
    mat_ids = {}
    for face in node.faces:
        for _ in face.indices:
            if face.brush_id in material_mapping:
                mat_id = mat_ids.get(face.brush_id, -1)

                if mat_id==-1:
                    # not found, add new material to the lookup table
                    mat_id = len(mat_ids)
                    mat_ids[face.brush_id] = mat_id
                    mat_name = material_mapping[face.brush_id]
                    ob.data.materials.append(bpy.data.materials[mat_name])

                ob.data.polygons[poly].material_index = mat_id

                brush = brush_mapping[face.brush_id]
                ob.data.polygons[poly].use_smooth = brush.fx & FX_FLATSHADED == 0

            poly += 1

    return ob

def import_keys_pre(node, ob, action):
    #ob.animation_data_create()
    #ob.animation_data.action = action
    #bpy.ops.object.mode_set(mode='OBJECT',toggle=False)
    for i in range(len(node['keys'])):
        keyframe = node['keys'][i]
    
        ob.rotation_mode='QUATERNION'

        if keyframe.rotation:
            ob.rotation_quaternion = flip(keyframe.rotation)
            ob.keyframe_insert(data_path='rotation_quaternion', frame=keyframe.frame)

        if keyframe.position:
            ob.location = flip(keyframe.position)
            ob.keyframe_insert(data_path='location', frame=keyframe.frame)

        if keyframe.scale:
            ob.scale = flip(keyframe.scale)
            ob.keyframe_insert(data_path='scale', frame=keyframe.frame)

        #ob.matrix_world = ob.convert_space(matrix=ob.matrix_world, from_space='WORLD', to_space='LOCAL')
    


    #bpy.ops.object.mode_set(mode='EDIT',toggle=False)

def import_node_recursive(node, parent=None, action=None):
    ob = None

    if 'vertices' in node and 'faces' in node:
        ob = import_mesh(node, parent)
    elif 'bones' in node:
        ob = import_bone(node, parent)
    elif node.name:
        ob = bpy.data.objects.new(node.name, None)

    if ob:
        ctx.scene.collection.objects.link(ob)

        if parent:
            ob.parent = parent

        #if 'keys' in node and 'bones' in node:
        #    import_keys_pre(node, ob, action)

        ob.rotation_mode='QUATERNION'
        ob.rotation_quaternion = flip(node.rotation)
        ob.scale = flip(node.scale)
        ob.location = flip(node.position)

    for x in node.nodes:
        import_node_recursive(x, ob)

def load_b3d(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=10.0,
             IMAGE_SEARCH=True,
             APPLY_MATRIX=True,
             global_matrix=None):

    global ctx
    global material_mapping
    global brush_mapping

    ctx = context
    data = B3DTree().parse(filepath)

    # load images
    images = {}
    import_dir = os.path.dirname(filepath)
    for i, texture in enumerate(data['textures'] if 'textures' in data else []):
        texture_path = os.path.normpath(os.path.join(import_dir, texture['name']))
        texture_name = os.path.basename(texture_path)
        texture_dir = os.path.dirname(texture_path)
        for d in (import_dir, texture_dir):
            img = load_image(texture_name, d, check_existing=True, place_holder=False, recursive=IMAGE_SEARCH)
            if img:
                texture = bpy.data.textures.new(name=texture_name, type='IMAGE')
                break
        images[i] = (texture_name, img)

    material_mapping = {}
    brush_mapping = {}

    for i, brush in enumerate(data.materials if 'materials' in data else []):
        # do not create material with the same name, if exists
        material = bpy.data.materials.get(brush.name)
        if material:
            material_mapping[i] = material.name
            brush_mapping[i] = brush
            continue

        material = bpy.data.materials.new(brush.name)
        material.diffuse_color = brush.rgba
        material.blend_method = 'BLEND' if brush.rgba[3] < 1.0 else 'OPAQUE'
        material.use_nodes = True

        bsdf = material.node_tree.nodes["Principled BSDF"]
        color_output = bsdf.inputs['Base Color']
        alpha_output = bsdf.inputs['Alpha']

        color_sockets = []
        alpha_sockets = []

        material_mapping[i] = material.name
        brush_mapping[i] = brush

        # set base color for bsdf (including alpha)
        color_output.default_value = brush.rgba

        # set alpha channel for simple materials
        if brush.rgba[3] < 1.0:
            bsdf.inputs['Alpha'].default_value = max(0.1, brush.rgba[3]) # make alpha slightly visible

        # fullbright (does not support add/multply modes)
        if brush.fx & FX_FULLBRIGHT:
            material.shadow_method = 'NONE'
            #color_output = material.node_tree.nodes['Material Output'].outputs[0] # loses alpha

        # backface culling / double sided materials
        material.use_backface_culling = brush.fx & FX_DOUBLESIDED == 0

        for tid in brush.tids:
            if tid not in images:
                continue

            name, image = images[tid]

            # add texture node
            tex_img = material.node_tree.nodes.new('ShaderNodeTexImage')
            tex_img.image = image
            color_socket = tex_img.outputs['Color']
            alpha_socket = tex_img.outputs['Alpha']

            # enable alpha-blending according for some objects
            # TODO: enable this only if image has alpha layer
            if brush.fx & (FX_FULLBRIGHT | FX_DOUBLESIDED):
                material.blend_method = 'BLEND'
                alpha_sockets.append(alpha_socket)
            else:
                alpha_sockets.append(color_socket)

            # apply brush color to a texture.
            # disable this shit for now, because UE5 hates it
            use_multiply = False
            if brush.rgba[:3] != (1.0, 1.0, 1.0):
                if use_multiply:
                    mix = material.node_tree.nodes.new('ShaderNodeVectorMath')
                    mix.operation = 'MULTIPLY'
                    material.node_tree.links.new(tex_img.outputs['Color'], mix.inputs[0])
                    mix.inputs[1].default_value = brush.rgba[:3]
                    color_socket = mix.outputs[0]
                    # use original color as alpha (e.g. white color mixed to black)
                    # TODO: figure out why it glitches with noparking/Location5.b3d
                    #material.blend_method = 'BLEND'
                    #material.node_tree.links.new(tex_img.outputs['Color'], alpha_output)

            # apply brush scale
            if (t:=data['textures'][tid]).scale != (1.0, 1.0):
                uv_map = material.node_tree.nodes.new('ShaderNodeUVMap')
                mapping = material.node_tree.nodes.new('ShaderNodeMapping')
                material.node_tree.links.new(uv_map.outputs[0], mapping.inputs[0])
                material.node_tree.links.new(mapping.outputs[0], tex_img.inputs[0])
                mapping.inputs['Location'].default_value = (*t.position, 0)
                mapping.inputs['Rotation'].default_value = (0, 0, t.rotation)
                mapping.inputs['Scale'].default_value = (*t.scale, 1)

            # color socket is properly routed now, add it to the output node
            color_sockets.append(color_socket)

        # apply vertex alpha (disabled for now, VERY glitchy in Blender 3.6 viewport)
        apply_vertex_alpha = False
        if apply_vertex_alpha and (brush.fx & (FX_VERTEXCOLOR | FX_VERTEXALPHA)):
            try:
                vertex_color = material.node_tree.nodes.new('ShaderNodeVertexColor')
                vertex_color.layer_name = VERTEX_COLORS
                material.blend_method = 'BLEND'
                material.node_tree.links.new(bsdf.inputs['Alpha'], vertex_color.outputs['Alpha'])
            except Exception as e:
                print('vertex color issue', e)

        if len(color_sockets)==1:
            material.node_tree.links.new(color_sockets[0], color_output)
            material.node_tree.links.new(alpha_sockets[0], alpha_output)
        elif len(color_sockets)>1:
            # the second texture is always used as an alpha layer
            material.blend_method = 'BLEND'
            material.node_tree.links.new(color_sockets[0], color_output)
            material.node_tree.links.new(alpha_sockets[1], alpha_output)

    global imported_armatures, weighting
    imported_armatures = []
    weighting = {}

    action = bpy.data.actions.new('default_action_name')
    action.use_fake_user = True

    import_node_recursive(data, action)

    make_armatures()
    #make_skeleton(data)

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
