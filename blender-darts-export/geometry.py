import os
import bpy

# from mathutils import Matrix, Vector, Euler


def write_obj(ctx, obj_name):
    """Export meshes to "meshes/" and then point to them in the scene file"""

    relative_path = os.path.join("meshes", obj_name + ".obj")

    # skip if we've already exported this object
    obj_id = f"obj-{relative_path}"
    if obj_id in ctx.already_exported.keys():
        ctx.report({"WARNING"}, f"Exporting OBJ file '{relative_path}' again!")

    if ctx.write_obj_files:
        if bpy.app.version >= (3, 3, 0):
            # new, faster C++ OBJ exporter
            ctx.info(f"  Writing '{relative_path}' using C++ exporter.")
            bpy.ops.wm.obj_export(
                filepath=os.path.join(ctx.directory, relative_path),
                export_selected_objects=True,
                export_eval_mode="DAG_EVAL_RENDER",
                apply_modifiers=True,
                export_normals=True,
                export_colors=True,
                export_uv=True,
                export_materials=ctx.material_mode != "OFF",
                export_triangulated_mesh=True,
                check_existing=False,
                forward_axis="Y",
                up_axis="Z",
            )
        else:
            # legacy python exporter
            ctx.info(f"  Writing '{relative_path}' using legacy Python exporter.")
            bpy.ops.export_scene.obj(
                filepath=os.path.join(ctx.directory, relative_path),
                use_selection=True,
                use_mesh_modifiers=True,
                use_normals=True,
                use_uvs=True,
                use_materials=ctx.material_mode != "OFF",
                use_triangles=True,
                use_edges=False,
                use_smooth_groups=False,
                check_existing=False,
                axis_forward="Y",
                axis_up="Z",
            )

    obj_params = {
        "type": "mesh",
        "name": obj_name,
        "filename": f"meshes/{obj_name}.obj",
        "material": "default",
        "vertex colorspace": "srgb",
    }

    ctx.already_exported[obj_id] = obj_params

    return obj_params


def write_meshes(ctx, meshes, obj_name):

    # first, save the selection, then select the single mesh we want to export
    viewport_selection = ctx.context.selected_objects
    bpy.ops.object.select_all(action="DESELECT")

    for mesh in meshes:
        mesh.select_set(True)

    obj_json = write_obj(ctx, obj_name)

    # Now restore the previous selection
    bpy.ops.object.select_all(action="DESELECT")
    for ob in viewport_selection:
        ob.select_set(True)

    return obj_json


def export(ctx, objects):
    if not os.path.exists(ctx.directory + "/meshes"):
        os.makedirs(ctx.directory + "/meshes")

    surfaces_json = []
    if ctx.mesh_mode == "SINGLE":
        ctx.info("Exporting a single scene-wide OBJ file.")
        obj_name, _ = os.path.splitext(ctx.filepath)
        obj_name = os.path.basename(obj_name)
        surfaces_json.append(write_meshes(ctx, objects, obj_name))
    else:
        ctx.info("Exporting each Blender object as a separate OBJ file.")
        for object in objects:

            # write_obj by default exports meshes in world coordinates
            # to save in local coordinates we temporarily transform all vertices by the inverse of matrix_world
            to_world = object.matrix_world.copy()

            # save and turn off constraints
            influences = []
            for i, c in enumerate(object.constraints):
                influences.append(c.influence)
                c.influence = 0.0

            object.matrix_world.identity()

            bpy.context.view_layer.update()

            params = write_meshes(ctx, [object], object.name)
            params["transform"] = ctx.transform_matrix(to_world)

            object.matrix_world = to_world
            for i, c in enumerate(object.constraints):
                c.influence = influences[i]

            bpy.context.view_layer.update()

            surfaces_json.append(params)

    return surfaces_json
