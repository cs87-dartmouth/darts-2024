from mathutils import Matrix
from mathutils import Vector
from math import degrees, atan, tan


def export(ctx, b_scene):

    # only exporting one camera
    cameras = [cam for cam in ctx.context.scene.objects
               if cam.type in {'CAMERA'}]

    if len(cameras) == 0:
        ctx.report({"WARNING"}, "No camera to export!")
    elif len(cameras) > 1:
        ctx.report(
            {"WARNING"}, "Multiple cameras found, only exporting the active one.")

    b_camera = ctx.context.scene.camera

    # default camera
    params = {}

    # resolution & fov
    res_x = b_scene.render.resolution_x
    res_y = b_scene.render.resolution_y

    # extract fov
    sensor_fit = b_camera.data.sensor_fit
    if sensor_fit == 'VERTICAL':
        params["vertical fov"] = degrees(b_camera.data.angle)
    elif sensor_fit == 'HORIZONTAL':
        params["vertical fov"] = degrees(2 * atan(res_y / res_x * tan(b_camera.data.angle/2)))
    elif sensor_fit == 'AUTO':
        if res_x >= res_y:
            params["vertical fov"] = degrees(2 * atan(res_y / res_x * tan(b_camera.data.angle/2)))
        else:
            params["vertical fov"] = degrees(b_camera.data.angle)
    else:
        raise ValueError(f"Unknown 'sensor_fit' value when exporting camera: {sensor_fit}")

    percent = b_scene.render.resolution_percentage / 100.0
    params["resolution"] = [int(res_x * percent), int(res_y * percent)]

    # up, lookat, and position
    up = b_camera.matrix_world.to_quaternion() @ Vector((0.0, 1.0, 0.0))
    direction = b_camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    loc = b_camera.matrix_world.to_translation()

    # set the values and return
    params["transform"] = {
        "from": list(loc),
        "up": list(up),
        "at": list(loc + direction)
    }

    if b_camera.data.dof.use_dof:
        # f/# = f / D (where f is the local length and D is the aperture diameter).
        # The units are in mm, so we also divide by 1000.
        params["aperture diameter"] = b_camera.data.lens / \
            b_camera.data.dof.aperture_fstop / 1000.0

        params["aperture blades"] = b_camera.data.dof.aperture_blades
        params["aperture rotation"] = b_camera.data.dof.aperture_rotation
        params["aperture ratio"] = b_camera.data.dof.aperture_ratio

        if b_camera.data.dof.focus_object is not None:
            # compute distance to object location projected along the camera view direction
            params["focus distance"] = abs(b_camera.matrix_world.col[2].to_3d().normalized().dot(
                b_camera.data.dof.focus_object.matrix_world.to_translation() - loc))
        else:
            params["focus distance"] = b_camera.data.dof.focus_distance

    if ctx.world_medium:
        params["medium"] = ctx.world_medium["name"]

    return params
