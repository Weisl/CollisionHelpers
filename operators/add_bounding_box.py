import bmesh
import bpy
from bpy.types import Operator
from bpy_extras.object_utils import object_data_add
from mathutils import Vector

from CollisionHelpers.operators.collision_helpers import alignObjects, getBoundingBox
from .add_bounding_primitive import OBJECT_OT_add_bounding_object


# TODO: Global, local switch works only in edit mode
# TODO: Add transparency also to material display
# TODO: Turn rendering off for colliders
# TODO: Additional spaces: view and optimal heuristic blablabla
# TODO: Support multi edit for collision creation (connected, and individual generation)
# TODO: Parenting -> add collisions to useful place in the hierarchy
# TODO: Naming -> check current naming options
# TODO: SELECT all collisions after finishing operation

def add_box_object(context, vertices, newName):
    """Generate a new object from the given vertices"""
    verts = vertices
    edges = []
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [5, 6, 2, 1], [0, 3, 7, 4], [3, 2, 6, 7], [4, 5, 1, 0]]

    mesh = bpy.data.meshes.new(name=newName)
    mesh.from_pydata(verts, edges, faces)

    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    newObj = object_data_add(context, mesh, operator=None, name=None)  # links to object instance

    return newObj


def add_box(context, space):
    """ """

    obj = context.edit_object
    me = obj.data

    # Get a BMesh representation
    bm = bmesh.from_edit_mesh(me)

    selected_verts = [v for v in bm.verts if v.select]
    vertsLoc = []

    # Modify the BMesh, can do anything here...
    positionsX = []
    positionsY = []
    positionsZ = []

    if space == 'GLOBAL':
        for v in selected_verts:
            v_local = v
            v_global = obj.matrix_world @ v_local.co

            positionsX.append(v_global[0])
            positionsY.append(v_global[1])
            positionsZ.append(v_global[2])

        # for v in selected_verts:
        #     mat = obj.matrix_world
        #     vertsLoc.append(v.transform(mat))
    else:
        for v in selected_verts:
            positionsX.append(v.co.x)
            positionsY.append(v.co.y)
            positionsZ.append(v.co.z)

    verts = [
        (max(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), max(positionsY), max(positionsZ)),
        (max(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), max(positionsY), max(positionsZ)),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]

    return verts, faces


def box_Collider_from_Editmode(self, context, verts_loc, faces, nameSuf):
    """ """
    active_ob = bpy.context.object
    root_col = bpy.context.scene.collection

    mesh = bpy.data.meshes.new("Box")
    bm = bmesh.new()

    for v_co in verts_loc:
        bm.verts.new(v_co)

    bm.verts.ensure_lookup_table()
    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])

    bm.to_mesh(mesh)
    mesh.update()

    # # add the mesh as an object into the scene with this utility module
    # from bpy_extras import object_utils
    # object_utils.object_data_add(context, mesh, operator=self)
    newCollider = bpy.data.objects.new(active_ob.name + nameSuf, mesh)
    root_col.objects.link(newCollider)

    if self.my_space == 'LOCAL':
        alignObjects(newCollider, active_ob)

    return newCollider


def box_Collider_from_Objectmode(context, name, obj, i):
    """Create box collider for every selected object in object mode"""
    colliderOb = []

    bBox = getBoundingBox(obj)  # create BoundingBox object for collider
    newCollider = add_box_object(context, bBox, name)

    # local_bbox_center = 1/8 * sum((Vector(b) for b in obj.bound_box), Vector())
    # global_bbox_center = obj.matrix_world @ local_bbox_center
    centreBase = sum((Vector(b) for b in obj.bound_box), Vector())
    centreBase /= 8
    # newCollider.matrix_world = centreBase

    alignObjects(newCollider, obj)

    return newCollider


class OBJECT_OT_add_bounding_box(OBJECT_OT_add_bounding_object, Operator):
    """Create a new Mesh Object"""
    bl_idname = "mesh.add_bounding_box"
    bl_label = "Add Box Collision"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        super().invoke(context, event)
        return self.execute(context)

    def execute(self, context):
        nameSuf = self.name_suffix
        matName = self.physics_material_name

        if context.object.mode == "EDIT":
            verts_loc, faces = add_box(context, self.my_space)
            newCollider = box_Collider_from_Editmode(self, context, verts_loc, faces, nameSuf)

            self.setColliderSettings(context, newCollider, matName)
        else:
            for i, obj in enumerate(context.selected_objects.copy()):
                newCollider = box_Collider_from_Objectmode(context, nameSuf, obj, i)

                self.setColliderSettings(context, newCollider, matName)

        return {'FINISHED'}