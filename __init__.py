import bpy
import mathutils

bl_info = {
    "name": "Auto Parent Bone",
    "author": "@va2ron1",
    "version": (1, 0, 1),
    "blender": (3, 1, 0),
    "location": "View 3D > Object > Parent",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View",
}

class ABone_OT_abone_init(bpy.types.Operator):
    bl_idname = 'abone.abone_init'
    bl_label = 'Auto Bone'
 
    def execute(self, context):
        bpy.ops.object.posemode_toggle()

        selected_objects = bpy.context.selected_objects
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

def register():
    bpy.utils.register_class(ABone_OT_abone_init)
    bpy.types.VIEW3D_MT_object_parent.append(draw_context)

def unregister():
    bpy.utils.unregister_class(ABone_OT_abone_init)

if __name__ == "__main__":
    register()
