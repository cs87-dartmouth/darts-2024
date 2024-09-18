if "bpy" in locals():
    import importlib

    if "scene" in locals():
        importlib.reload(scene)
    if "materials" in locals():
        importlib.reload(materials)
    if "textures" in locals():
        importlib.reload(textures)
    if "lights" in locals():
        importlib.reload(lights)
    if "geometry" in locals():
        importlib.reload(geometry)
    if "camera" in locals():
        importlib.reload(camera)

import bpy
import bpy_extras
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Darts",
    "author": "Wojciech Jarosz, Baptiste Nicolet, Shaojie Jiao, Adrien Gruson, Delio Vicini, Tizian Zeltner",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Export > Darts exporter (.json)",
    "description": "Export Darts scene format (.json)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export",
}


class DartsExporter(bpy.types.Operator, ExportHelper):
    """Export as a Darts scene"""

    bl_idname = "export_scene.darts"
    bl_label = "Darts Export"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    verbose: BoolProperty(
        name="Verbose output",
        description="Print out extra info in Blender's Info Log",
        default=False,
    )
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )
    use_visibility: BoolProperty(
        name="Visible Only",
        description="We export only objects that are visible for render. If checked, also exclude any objects hidden in the viewport",
        default=True,
    )
    write_obj_files: BoolProperty(
        name="Write OBJ files",
        description="Uncheck this to write out the Darts scene file, but not write out any OBJs to disk",
        default=True,
    )

    # Scene-wide settings
    integrator: EnumProperty(
        name="Integrator",
        items=(
            ("none", "None", "Do not include an integrator at all"),
            ("ao", "ao", "Use the ambient occlusion integrator"),
            ("normals", "normals", "Use the normals integrator"),
            (
                "path tracer mis",
                "path tracer mis",
                "Use the MIS-based path tracing integrator",
            ),
            (
                "volume path tracer mis",
                "volume path tracer mis",
                "Use the MIS-based volume path tracing integrator",
            ),
        ),
        default="path tracer mis",
    )
    sampler: EnumProperty(
        name="Sampler",
        items=(
            ("none", "None", "Do not include a sampler at all"),
            ("independent", "independent", "Independent sampler"),
            ("stratified", "stratified", "Stratified sampler"),
            ("cmj", "cmj", "Correlated multi-jittered sampler"),
            ("oa", "oa", "Orthogonal array sampler"),
            ("psobol2d", "psobol2d", "Padded 2D Sobol sampler"),
            ("ssobol", "ssobol", "Stochastic Sobol sampler"),
        ),
        default="independent",
    )
    use_lights: BoolProperty(
        name="Export lights",
        description="Export Blender lights",
        default=True,
    )

    # Geometry/OBJ export-related settings
    mesh_mode: EnumProperty(
        name="Convert to",
        items=(
            (
                "SINGLE",
                "a single mesh",
                "Write all scene geometry out as a single mesh (OBJ file)",
            ),
            (
                "SPLIT",
                "one mesh per Blender object",
                "Write each Blender object out as a separate mesh (OBJ file)",
            ),
        ),
        default="SINGLE",
    )

    # Material-related settings
    material_mode: EnumProperty(
        name="Materials",
        items=(
            (
                "OFF",
                "None",
                "Do not write materials to OBJ. Include a single default material in the Darts scene to use for all surfaces",
            ),
            (
                "ONE",
                "One default material",
                "Write materials to OBJ and a single default material in the Darts scene to use for all surfaces",
            ),
            (
                "DIFFUSE",
                "Diffuse placeholder materials",
                "Write OBJ materials and create a placeholder diffuse material in Darts for each Blender material",
            ),
            (
                "CONVERT",
                "Convert Blender materials",
                "Write OBJ materials and create an approximately equivalent Darts material for each Blender material",
            ),
        ),
        default="CONVERT",
    )
    glossy_mode: EnumProperty(
        name="Glossy as",
        items=(
            (
                "metal",
                "metal",
                "Convert Blender's `Glossy` material to a `metal` Darts material",
            ),
            (
                "phong",
                "phong",
                "Convert Blender's `Glossy` material to a `phong` Darts material",
            ),
            (
                "blinn-phong",
                "blinn-phong",
                "Convert Blender's `Glossy` material to a `blinn-phong` Darts material",
            ),
            (
                "rough conductor",
                "(rough) conductor",
                "Convert Blender's `Glossy` material to a `conductor` or `rough conductor` Darts material",
            ),
        ),
        default="rough conductor",
    )
    force_two_sided: BoolProperty(
        name="Force two-sided materials",
        description="Wraps all opaque materials in a 'two sided' adapter. Otherwise the back side of opaque materials will be black in Darts by default",
        default=True,
    )
    use_normal_maps: BoolProperty(
        name="Use normal maps",
        description="Wraps the Darts material in a 'normal map' adapter if the Blender material has a normal map",
        default=True,
    )
    use_bump_maps: BoolProperty(
        name="Use bump maps",
        description="Wraps the Darts material in a 'bump map' adapter if the Blender material has a bump map",
        default=False,
    )

    # Texture-related settings
    enable_background: BoolProperty(
        name="Background",
        description="Export background color (constant or envmap). When disabled, Darts' background is set to a fixed 5",
        default=True,
    )
    write_texture_files: BoolProperty(
        name="Write textures",
        description="Uncheck this to write out the Darts scene file, but not write out any textures to disk",
        default=True,
    )
    enable_blackbody: BoolProperty(
        name="Blackbody",
        description="Convert Blender Blackbody texture node to a Darts 'blackbody' texture",
        default=True,
    )
    enable_brick: BoolProperty(
        name="Brick",
        description="Convert Blender Brick texture node to a Darts 'brick' texture",
        default=True,
    )
    enable_checker: BoolProperty(
        name="Checker",
        description="Convert Blender Checker texture node to a Darts 'checker' texture",
        default=True,
    )
    enable_clamp: BoolProperty(
        name="Clamp",
        description="Convert Blender Clamp converter node to a Darts 'clamp' texture",
        default=True,
    )
    enable_color_ramp: BoolProperty(
        name="Color ramp",
        description="Convert Blender Color Ramp converter node to a Darts 'color ramp' texture",
        default=True,
    )
    enable_coord: BoolProperty(
        name="Coord texture",
        description="Convert Blender Texture Coordinate input nodes into Darts 'coord' textures",
        default=True,
    )
    enable_fresnel: BoolProperty(
        name="Fresnel",
        description="Convert Blender Fresnel input node to a Darts 'fresnel' texture. When disabled, Fresnel nodes are converted to a fixed 0.5",
        default=True,
    )
    enable_gradient: BoolProperty(
        name="Gradient",
        description="Convert Blender Gradient texture node to a Darts 'gradient' texture",
        default=True,
    )
    enable_layer_weight: BoolProperty(
        name="Layer Weight",
        description="Convert Blender Layer Weight input node to a Darts 'layer weight' texture. When disabled, Layer Weight nodes are converted to a fixed 0.5",
        default=True,
    )
    enable_mapping: BoolProperty(
        name="Mapping",
        description="Convert Blender Mapping vector nodes to a Dart Texture's 'mapping' field",
        default=True,
    )
    enable_math: BoolProperty(
        name="Math",
        description="Convert Blender Math converter nodes to Darts 'math' textures",
        default=True,
    )
    enable_mix_rgb: BoolProperty(
        name="Mix RGB",
        description="Convert Blender Mix RGB color node to a Darts 'mix' texture",
        default=True,
    )
    enable_mix_node: BoolProperty(
        name="Mix",
        description="Convert Blender Mix converter node to a Darts 'mix' texture",
        default=True,
    )
    enable_musgrave: BoolProperty(
        name="Musgrave",
        description="Convert Blender Musgrave texture node to a Darts 'musgrave' texture. When disabled, Musgrave textures are converted to a fixed 0.5",
        default=True,
    )
    enable_noise: BoolProperty(
        name="Noise",
        description="Convert Blender Noise texture node to a Darts 'noise' texture. When disabled, Noise textures are converted to a fixed 0.5",
        default=True,
    )
    enable_separate: BoolProperty(
        name="Separate",
        description="Convert Blender Separate XYZ/Color converter nodes to a Darts 'separate' texture",
        default=True,
    )
    enable_voronoi: BoolProperty(
        name="Voronoi",
        description="Convert Blender Voronoi texture node to a Darts 'voronoi' texture. When disabled, Voronoi textures are converted to a fixed 0.5",
        default=True,
    )
    enable_wave: BoolProperty(
        name="Wave",
        description="Convert Blender Wave shader node to a Darts 'wave' texture",
        default=True,
    )
    enable_wavelength: BoolProperty(
        name="Wavelength",
        description="Convert Blender Wavelength shader to a Darts 'wavelength' texture",
        default=True,
    )
    enable_wireframe: BoolProperty(
        name="Wireframe",
        description="Convert Blender Wireframe input node to a Darts 'wavelength' texture",
        default=True,
    )

    def execute(self, context):
        from . import scene

        keywords = self.as_keywords(ignore=("check_existing", "filter_glob"))
        converter = scene.SceneWriter(context, self.report, **keywords)
        converter.write()

        return {"FINISHED"}

    def draw(self, context):
        pass


class DARTS_PT_export_include(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_darts"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "verbose")

        sublayout = layout.column(heading="Limit to")
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visibility")


class DARTS_PT_export_scene(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Scene"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_darts"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "integrator")
        layout.prop(operator, "sampler")
        layout.prop(operator, "use_lights")


class DARTS_PT_export_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_darts"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "mesh_mode")
        layout.prop(operator, "write_obj_files")


class DARTS_PT_export_materials(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Material conversion"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_darts"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "material_mode")

        sublayout = layout.column()
        sublayout.enabled = operator.material_mode == "CONVERT"
        sublayout.prop(operator, "use_normal_maps")
        sublayout.prop(operator, "use_bump_maps")
        sublayout.prop(operator, "force_two_sided")
        sublayout.prop(operator, "glossy_mode")


class DARTS_PT_export_textures(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Texture conversion"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_darts"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        sublayout = layout.column(heading="Enable")

        sublayout.prop(operator, "write_texture_files")
        sublayout.prop(operator, "enable_background")
        sublayout.prop(operator, "enable_blackbody")
        sublayout.prop(operator, "enable_brick")
        sublayout.prop(operator, "enable_clamp")
        sublayout.prop(operator, "enable_color_ramp")
        sublayout.prop(operator, "enable_coord")
        sublayout.prop(operator, "enable_checker")
        sublayout.prop(operator, "enable_fresnel")
        sublayout.prop(operator, "enable_gradient")
        sublayout.prop(operator, "enable_layer_weight")
        sublayout.prop(operator, "enable_mapping")
        sublayout.prop(operator, "enable_math")
        sublayout.prop(operator, "enable_mix_rgb")
        sublayout.prop(operator, "enable_mix_node")
        sublayout.prop(operator, "enable_musgrave")
        sublayout.prop(operator, "enable_noise")
        sublayout.prop(operator, "enable_separate")
        sublayout.prop(operator, "enable_voronoi")
        sublayout.prop(operator, "enable_wave")
        sublayout.prop(operator, "enable_wavelength")
        sublayout.prop(operator, "enable_wireframe")


def menu_func_export(self, context):
    self.layout.operator(DartsExporter.bl_idname, text="Darts scene (.json)")


classes = (
    DartsExporter,
    DARTS_PT_export_include,
    DARTS_PT_export_scene,
    DARTS_PT_export_geometry,
    DARTS_PT_export_materials,
    DARTS_PT_export_textures,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
