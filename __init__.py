import bpy
import mathutils

bl_info = {
    "name": "Auto Parent Bone",
    "author": "va2ron1",
    "version": (1, 0, 3),
    "blender": (3, 1, 0),
    "location": "Object > Parent",
    "description": "Auto Parenting Bones with Objects",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
}

# selection order methods and handler
# https://blender.stackexchange.com/a/253488

def get_ordered_selection_objects():
    tagged_objects = []
    for o in bpy.data.objects:
        order_index = o.get("selection_order", -1)
        if order_index >= 0:
            tagged_objects.append((order_index, o))
    tagged_objects = sorted(tagged_objects, key=lambda item: item[0])
    return [o for i, o in tagged_objects]

def clear_order_flag(obj):
    try:
        del obj["selection_order"]
    except KeyError:
        pass

def update_selection_order():
    if not bpy.context.selected_objects:
        for o in bpy.data.objects:
            clear_order_flag(o)
        return
    selection_order = get_ordered_selection_objects()
    idx = 0
    for o in selection_order:
        if not o.select_get():
            selection_order.remove(o)
            clear_order_flag(o)
        else:
            o["selection_order"] = idx
            idx += 1
    for o in bpy.context.selected_objects:
        if o not in selection_order:
            o["selection_order"] = len(selection_order)
            selection_order.append(o)

def selection_change_handler(scene):
    if bpy.context.mode != "OBJECT":
        return
    is_selection_update = any(
        not u.is_updated_geometry
        and not u.is_updated_transform
        and not u.is_updated_shading
        for u in bpy.context.view_layer.depsgraph.updates
    )
    if is_selection_update:
        update_selection_order()


class ABone_OT_abone_init(bpy.types.Operator):
    bl_idname = 'abone.abone_init'
    bl_label = 'Auto Parent Bone'
 
    def execute(self, context):
        selected_objects = get_ordered_selection_objects()
        print(selected_objects)
        armature = bpy.data.objects[selected_objects[0].name]
        objects = selected_objects[1:]

        if armature.type != 'ARMATURE':
            raise Exception('No armature selected first')

        for object in objects:
            if object.type != 'MESH':
                raise Exception('No objects are MESH')
                
        objects = []

        for object in selected_objects[1:]:
            objects.append(object.name)

        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)

        bpy.ops.object.posemode_toggle()

        bones = []

        for bone in bpy.context.selected_pose_bones:
            bones.append(bone.name)
            armature.data.bones[bone.name].select = False


        if len(bones) != len(objects):
            raise Exception('No same amount of bones/objects are selected')

        length = len(objects)

        for index in range(length):
            bone = armature.data.bones[bones[index]]
            bone.select = True
            
            bpy.ops.object.posemode_toggle()
            bpy.data.objects[objects[index]].select_set(True)
            armature.select_set(True)
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.parent_set(type='BONE', keep_transform=False)
            bpy.data.objects[objects[index]].parent_bone = bones[index]

            if bone.parent is None:
                vec = bone.head - bone.tail
                trans = mathutils.Matrix.Translation(vec)
                bpy.data.objects[objects[index]].matrix_parent_inverse = bone.matrix_local.inverted() @ trans
            else:
                bone.use_relative_parent = True

            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            bpy.ops.object.posemode_toggle()
            bone.select = False
            
        bpy.ops.object.posemode_toggle()
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

def draw_context(self, context):
    self.layout.separator()
    self.layout.operator('abone.abone_init')

addon_keymaps = []

def register():
    bpy.utils.register_class(ABone_OT_abone_init)
    bpy.types.VIEW3D_MT_object_parent.append(draw_context)
    bpy.app.handlers.depsgraph_update_post.append(selection_change_handler)

    # Add the hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(ABone_OT_abone_init.bl_idname, type='P', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(ABone_OT_abone_init)
    bpy.types.VIEW3D_MT_object_parent.remove(draw_context)

        # Remove the hotkey
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    for f in bpy.app.handlers.depsgraph_update_post:
        if f.__name__ == "selection_change_handler":
            bpy.app.handlers.depsgraph_update_post.remove(f)
    register()
