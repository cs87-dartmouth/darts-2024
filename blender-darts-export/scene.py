import os
import shutil
import time
import bpy
from mathutils import Matrix
from mathutils import Vector
from mathutils import Euler
from mathutils import Quaternion
from math import degrees
import json
import numpy as np
import pyopenvdb as vdb

from . import materials
from . import textures
from . import lights
from . import geometry
from . import camera

SUPPORTED_TYPES = {
    "MESH",
    "CURVE",
    "FONT",
    "META",
    "EMPTY",
    "SURFACE",
}  # Surface types we support

BLENDER_VERSION = f"{bpy.app.version[0]}.{bpy.app.version[1]}"


class SceneWriter:
    """
    Writes a Blender scene to a Darts-compatible json scene file.
    """

    def __init__(
        self,
        context,
        report,
        filepath,
        write_obj_files,
        write_texture_files,
        verbose,
        use_selection,
        use_visibility,
        integrator,
        sampler,
        use_lights,
        mesh_mode,
        material_mode,
        glossy_mode,
        use_normal_maps,
        use_bump_maps,
        force_two_sided,
        enable_background,
        enable_blackbody,
        enable_brick,
        enable_checker,
        enable_clamp,
        enable_color_ramp,
        enable_coord,
        enable_fresnel,
        enable_gradient,
        enable_layer_weight,
        enable_mapping,
        enable_math,
        enable_musgrave,
        enable_mix_rgb,
        enable_mix_node,
        enable_noise,
        enable_separate,
        enable_voronoi,
        enable_wave,
        enable_wavelength,
        enable_wireframe,
    ):
        self.context = context
        self.report = report

        self.write_obj_files = write_obj_files

        self.verbose = verbose
        self.use_selection = use_selection
        self.use_visibility = use_visibility

        self.integrator = integrator
        self.sampler = sampler
        self.use_lights = use_lights

        self.mesh_mode = mesh_mode

        self.material_mode = material_mode
        self.write_texture_files = write_texture_files
        self.use_normal_maps = use_normal_maps
        self.use_bump_maps = use_bump_maps
        self.force_two_sided = force_two_sided
        self.glossy_mode = glossy_mode

        self.enable_background = enable_background
        self.enable_clamp = enable_clamp
        self.enable_color_ramp = enable_color_ramp
        self.enable_coord = enable_coord
        self.enable_mapping = enable_mapping
        self.enable_fresnel = enable_fresnel
        self.enable_gradient = enable_gradient
        self.enable_layer_weight = enable_layer_weight
        self.enable_math = enable_math
        self.enable_mix_rgb = enable_mix_rgb
        self.enable_mix_node = enable_mix_node
        self.enable_noise = enable_noise
        self.enable_musgrave = enable_musgrave
        self.enable_voronoi = enable_voronoi
        self.enable_checker = enable_checker
        self.enable_brick = enable_brick
        self.enable_blackbody = enable_blackbody
        self.enable_separate = enable_separate
        self.enable_wavelength = enable_wavelength
        self.enable_wave = enable_wave
        self.enable_wireframe = enable_wireframe

        self.filepath = filepath
        self.directory = os.path.dirname(filepath)
        self.already_exported = {}
        self.world_medium = None

    def info(self, message):
        if self.verbose:
            self.report({"INFO"}, message)

    def material_name(self, b_name):
        return f"{b_name.replace(' ', '_')}"

    def follow_link(self, socket):
        """
        Recursively follow a link potentially via reroute nodes
        """
        if socket.is_linked and socket.links[0].from_node.bl_idname == "NodeReroute":
            return self.follow_link(socket.links[0].from_node.inputs[0])
        else:
            return socket

    def color(self, value):
        """
        Given a color value, format it for the scene dict.

        Params
        ------

        value: value of the color: can be a an rgb triplet, a single number
        """
        if isinstance(value, (float, int)):
            return value
        else:
            value = list(value)
            if any(not isinstance(x, (float, int, tuple)) for x in value):
                raise ValueError(f"Unknown color entry: {value}")
            if any(type(value[i]) != type(value[i + 1]) for i in range(len(value) - 1)):
                raise ValueError(f"Mixed types in color entry {value}")
            totitems = len(value)
            if isinstance(value[0], (float, int)):
                if totitems == 3 or totitems == 4:
                    return value[:3]
                elif totitems == 1:
                    return value[0]
                else:
                    raise ValueError(
                        f"Expected color items to be 1,3 or 4 got {len(value)}: {value}"
                    )
        return 0

    def transform_matrix(self, matrix):
        if len(matrix) == 4:
            mat = matrix
        else:  # 3x3
            mat = matrix.to_4x4()
        return {"matrix": list(i for j in mat for i in j)}

    def LRS_matrix(self, loc, rot, sca):
        self.info(
            f"Writing matrix as\n\t{loc}\n\t{tuple(degrees(a) for a in rot)}\n\t{sca}"
        )

        params = []
        if sca[:] != (1, 1, 1):
            params.append({"scale": sca[:]})
        if rot[:] != (0, 0, 0):
            params.extend(
                [
                    {"rotate": (degrees(rot.x), 1, 0, 0)},
                    {"rotate": (degrees(rot.y), 0, 1, 0)},
                    {"rotate": (degrees(rot.z), 0, 0, 1)},
                ]
            )
        if loc[:] != (0, 0, 0):
            params.append({"translate": loc[:]})

        return params

    def get_world_input(self, socket_name):
        """
        get node connected to a specific world input socket.
        """

        output_node_id = "World Output"

        world = self.context.scene.world

        if (
            world is None
            or not world.use_nodes
            or world.node_tree is None
            or output_node_id not in world.node_tree.nodes
        ):
            return None

        output_node = world.node_tree.nodes[output_node_id]

        if (
            socket_name not in output_node.inputs
            or not output_node.inputs[socket_name].is_linked
        ):
            return None

        return self.follow_link(output_node.inputs[socket_name]).links[0].from_node

    def make_misc(self):
        """Adds default values to make the scene complete"""

        params = {}

        params["sampler"] = {"samples": self.context.scene.cycles.samples}

        if self.sampler != "none":
            params["sampler"].update({"type": self.sampler})

        if self.integrator != "none":
            params["integrator"] = {"type": self.integrator}

        if self.enable_background:
            params["background"] = textures.convert_background(self)
        else:
            params["background"] = 5

        params["accelerator"] = {"type": "bbh"}

        return params

    def dump(self, obj, name="obj"):
        for attr in dir(obj):
            self.report({"INFO"}, f"{name}.{attr} = {getattr(obj, attr)}")

    def convert_nanovdb(self, volume):

        volumes_folder = os.path.join(self.directory, "volumes")

        # Create directory if it doesn't exist
        if self.write_texture_files and not os.path.exists(volumes_folder):
            os.makedirs(volumes_folder)
            self.info(f"Created directory: {volumes_folder}")

        try:
            if not volume.data.grids.is_loaded:
                volume.data.grids.load()

            # write the bounding box's material
            if not volume.data or not volume.data.materials:
                raise NotImplementedError("Cannot find data or material for volume")

            self.info(
                f"Volume '{volume.name_full}' has {len(volume.data.materials)} materials."
            )

            mat = volume.data.materials[0]

            if not mat or mat.name_full == "Dots Stroke" or mat.users == 0:
                raise NotImplementedError("Invalid material for volume")

            self.info(f"Exporting material '{mat.name_full}', with {mat.users} users.")

            if not mat.use_nodes:
                raise NotImplementedError("Material does not use nodes")

            output_node_id = "Material Output"
            if output_node_id not in mat.node_tree.nodes:
                raise NotImplementedError("Cannot find material output node")

            output_node = mat.node_tree.nodes[output_node_id]

            if (
                "Surface" in output_node.inputs
                and output_node.inputs["Surface"].is_linked
            ):
                surface_node = (
                    self.follow_link(output_node.inputs["Surface"]).links[0].from_node
                )
                mat_params = materials.cycles_surface_to_dict(
                    self, surface_node, mat.name_full
                )
            else:
                mat_params = {"type": "transparent"}

            if (
                "Volume" in output_node.inputs
                and output_node.inputs["Volume"].is_linked
            ):
                volume_node = (
                    self.follow_link(output_node.inputs["Volume"]).links[0].from_node
                )
                mat_params["interior medium"] = materials.convert_volume_vdb_node(
                    self, volume_node
                )

                if not mat_params["interior medium"]:
                    return mat_params

                mat_params["interior medium"]["transform"] = self.transform_matrix(
                    volume.matrix_world.copy()
                )

                vdb_path = volume.data.grids.frame_filepath

                # Get the base name (file name with extension)
                vdb_base_name = os.path.basename(vdb_path)
                self.info(f"OpenVDB base name: {vdb_base_name}")

                # Get the file name without extension
                vdb_file_name, vdb_file_extension = os.path.splitext(vdb_base_name)
                self.info(f"OpenVDB file name: {vdb_file_name}")
                self.info(f"OpenVDB file extension: {vdb_file_extension}")

                mat_params["interior medium"][
                    "filename"
                ] = f"volumes/{vdb_file_name}.nvdb"

                # copy vdb_file into the volumes directory
                if self.write_texture_files:
                    shutil.copy(vdb_path, volumes_folder)

                return mat_params

        except NotImplementedError as e:
            self.report(
                {"WARNING"},
                f"Export of material '{mat.name_full}' failed: {e.args[0]}. Exporting a dummy material instead.",
            )
            return materials.get_dummy_material(self)

    def export_volumes(self, volumes):
        volumes_json = []

        for volume in volumes:

            # save and turn off constraints
            influences = []
            for i, c in enumerate(volume.constraints):
                influences.append(c.influence)
                c.influence = 0.0

            bpy.context.view_layer.update()

            # create a surface for the bounding box of the volume and assign the appropriate material and interior medium
            params = {
                "type": "cube",
                "name": volume.name,
                "transform": self.transform_matrix(volume.matrix_world.copy()),
            }

            # get bounding box
            # volume.bound_box is a multi-dimensoional 8*3 array of floats, print it out as 8 rows of 3 values each
            self.report({"INFO"}, f"bbox1:")
            for i, bb in enumerate(volume.bound_box):
                self.report({"INFO"}, f"volume.bound_box[{i}] = {bb[0], bb[1], bb[2]}")

            min_corner = [min(bb[i] for bb in volume.bound_box) for i in range(3)]
            max_corner = [max(bb[i] for bb in volume.bound_box) for i in range(3)]
            for i, bb in enumerate(volume.bound_box):
                self.report({"INFO"}, f"volume.bound_box[{i}] = {bb[0], bb[1], bb[2]}")
            self.report({"INFO"}, f"min_corner = {min_corner}")
            self.report({"INFO"}, f"max_corner = {max_corner}")
            params["min corner"] = min_corner
            params["max corner"] = max_corner

            params["material"] = self.convert_nanovdb(volume)

            # restore constraints
            for i, c in enumerate(volume.constraints):
                c.influence = influences[i]

            bpy.context.view_layer.update()

            volumes_json.append(params)

        return volumes_json

    def write(self):
        """Main method to write the blender scene into Darts format"""

        start = time.perf_counter()

        # Switch to object mode before exporting stuff, so everything is defined properly
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")

        data_all = {}

        data_all["media"] = []

        volume_node = self.get_world_input("Volume")
        if volume_node is not None:
            self.world_medium = materials.cycles_volume_to_dict(
                self, volume_node, "world medium"
            )
            data_all["media"].extend(self.world_medium)

        data_all["camera"] = camera.export(self, self.context.scene)

        # adding defaults
        data_all.update(self.make_misc())

        # start with just the objects visible to the renderer
        objects = [o for o in self.context.scene.objects if not o.hide_render]

        # figure out the list based on the export settings
        if self.use_selection:
            objects = [o for o in objects if o.select_get()]
        if self.use_visibility:
            objects = [o for o in objects if o.visible_get()]

        b_surfaces = [o for o in objects if o.type in SUPPORTED_TYPES]
        b_volumes = [o for o in objects if o.type in "VOLUME"]

        # export the materials
        mats, media = materials.export(self, b_surfaces)

        data_all["media"].extend(media)
        data_all["materials"] = mats

        # export meshes
        data_all["surfaces"] = geometry.export(self, b_surfaces)

        # add the volumes
        data_all["surfaces"].extend(self.export_volumes(b_volumes))

        # export lights
        if self.use_lights:
            b_lights = [o for o in objects if o.type in {"LIGHT"}]
            data_all["surfaces"].extend(lights.export(self, b_lights))

        # write the json file
        with open(self.filepath, "w") as dump_file:
            exported_json_string = json.dumps(data_all, indent=4)
            dump_file.write(exported_json_string)
            dump_file.close

        end = time.perf_counter()
        self.report(
            {"INFO"},
            f"Scene exported successfully to '{self.filepath}' in {end-start} s!",
        )
