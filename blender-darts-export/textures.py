import numpy as np
from mathutils import Matrix
from collections.abc import Iterable
import os


def dummy_color(ctx):
    return ctx.color([0.0, 1.0, 0.3])


def export_image(ctx, image):
    """
    Return the path to a texture.
    Ensure the image is on disk and of a correct type

    image : The Blender Image object
    """

    texture_exts = {
        "BMP": ".bmp",
        "HDR": ".hdr",
        "JPEG": ".jpg",
        "JPEG2000": ".jpg",
        "PNG": ".png",
        "OPEN_EXR": ".exr",
        "OPEN_EXR_MULTILAYER": ".exr",
        "TARGA": ".tga",
        "TARGA_RAW": ".tga",
    }

    convert_format = {"CINEON": "EXR", "DPX": "EXR", "TIFF": "PNG", "IRIS": "PNG"}

    textures_folder = os.path.join(ctx.directory, "textures")
    if image.file_format in convert_format:
        ctx.info(
            f"Image format of '{image.name}' is not supported. Converting it to {convert_format[image.file_format]}."
        )
        image.file_format = convert_format[image.file_format]
    original_name = os.path.basename(image.filepath)
    # Try to remove extensions from names of packed files to avoid stuff like 'Image.png.001.png'
    if original_name != "" and image.name.startswith(original_name):
        base_name, _ = os.path.splitext(original_name)
        name = image.name.replace(original_name, base_name, 1)  # Remove the extension
        name += texture_exts[image.file_format]
    else:
        name = f"{image.name}{texture_exts[image.file_format]}"
    if ctx.write_texture_files:
        target_path = os.path.join(textures_folder, name)
        if not os.path.isdir(textures_folder):
            os.makedirs(textures_folder)
        old_filepath = image.filepath
        image.filepath_raw = target_path
        image.save()
        image.filepath_raw = old_filepath
    return f"textures/{name}"


def convert_image_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexImage.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html
    """
    node = out_socket.node
    params = {
        "type": "image",
        "filename": export_image(ctx, node.image),
        "interpolation": node.interpolation.lower(),
        "projection": node.projection.lower(),
        "projection blend": node.projection_blend,
    }

    if node.image.colorspace_settings.name in ["Non-Color", "Raw", "Linear"]:
        # non color data, tell Darts not to apply gamma conversion to it
        params["raw"] = True
    elif node.image.colorspace_settings.name != "sRGB":
        ctx.report(
            {"WARNING"},
            f"Texture '{node.image}' uses {node.image.colorspace_settings.name} colorspace. Darts only supports sRGB textures for color data.",
        )

    if out_socket.name == "Color":
        params["output"] = "color"
    elif out_socket.name == "Alpha":
        params["output"] = "alpha"
    else:
        raise NotImplementedError(
            f"Unrecognized output socket '{out_socket.name}' on image texture node"
        )

    if node.extension == "CLIP":
        ctx.report(
            {"WARNING"},
            f"'CLIP' extension mode behaves differently in Blender than in Darts.",
        )
    modes = {"REPEAT": "repeat", "EXTEND": "CLAMP", "CLIP": "black"}
    params["wrap mode x"] = params["wrap mode y"] = modes[node.extension]

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_environment_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexEnvironment.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/environment.html
    """
    node = out_socket.node
    params = {
        "type": "envmap",
        "filename": export_image(ctx, node.image),
        "output": "color",
        "interpolation": node.interpolation.lower(),
    }

    if node.image.colorspace_settings.name in ["Non-Color", "Raw", "Linear"]:
        # non color data, tell Darts not to apply gamma conversion to it
        params["raw"] = True
    elif node.image.colorspace_settings.name != "sRGB":
        ctx.report(
            {"WARNING"},
            f"Texture '{node.image}' uses {node.image.colorspace_settings.name} colorspace. Darts only supports sRGB textures for color data.",
        )

    if node.projection != "EQUIRECTANGULAR":
        ctx.report(
            {"WARNING"},
            f"Darts only supports 'EQUIRECTANGULAR' envmaps. Ignoring {node.projection}.",
        )

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_checker_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexChecker.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/checker.html
    """
    if not ctx.enable_checker:
        return dummy_color(ctx)

    node = out_socket.node
    if node.inputs["Scale"].is_linked:
        raise NotImplementedError("Textured 'Scale' values are not supported")
    params = {
        "type": "checker",
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "color1": convert_texture_node(ctx, node.inputs["Color1"]),
        "color2": convert_texture_node(ctx, node.inputs["Color2"]),
    }

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_brick_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexBrick.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/brick.html
    """
    if not ctx.enable_brick:
        return dummy_color(ctx)

    node = out_socket.node
    params = {
        "type": "brick",
        "offset": node.offset,
        "offset frequency": node.offset_frequency,
        "squash": node.squash,
        "squash frequency": node.squash_frequency,
        "color1": convert_texture_node(ctx, node.inputs["Color1"]),
        "color2": convert_texture_node(ctx, node.inputs["Color2"]),
        "mortar": convert_texture_node(ctx, node.inputs["Mortar"]),
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "mortar size": convert_texture_node(ctx, node.inputs["Mortar Size"]),
        "mortar smooth": convert_texture_node(ctx, node.inputs["Mortar Smooth"]),
        "bias": convert_texture_node(ctx, node.inputs["Bias"]),
        "brick width": convert_texture_node(ctx, node.inputs["Brick Width"]),
        "row height": convert_texture_node(ctx, node.inputs["Row Height"]),
        "output": "float" if out_socket.name == "Fac" else "color",
    }

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_wave_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexWave.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/wave.html
    """
    if not ctx.enable_wave:
        return ctx.color(0.5)

    node = out_socket.node
    profiles = {"SIN": "sine", "SAW": "saw", "TRI": "triangle"}
    params = {
        "type": "wave",
        "wave type": node.wave_type.lower(),
        "direction": (
            node.bands_direction.lower()
            if node.wave_type == "BANDS"
            else node.rings_direction.lower()
        ),
        "profile": profiles[node.wave_profile],
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "distortion": convert_texture_node(ctx, node.inputs["Distortion"]),
        "detail": convert_texture_node(ctx, node.inputs["Detail"]),
        "detail scale": convert_texture_node(ctx, node.inputs["Detail Scale"]),
        "detail roughness": convert_texture_node(ctx, node.inputs["Detail Roughness"]),
        "phase offset": convert_texture_node(ctx, node.inputs["Phase Offset"]),
    }

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_white_noise_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexWhiteNoise.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/white_noise.html
    """

    node = out_socket.node
    dimensions = {"1D": 1, "2D": 2, "3D": 3, "4D": 4}
    dims = dimensions[node.noise_dimensions]
    params = {
        "type": "white noise",
        "dimensions": dims,
        "output": "float" if out_socket.name == "Value" else "color",
    }

    if dims == 1 or dims == 4:
        params["w"] = convert_texture_node(ctx, node.inputs["W"])

    if dims != 1 and node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_noise_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexNoise.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/noise.html
    """
    if not ctx.enable_noise:
        return ctx.color(0.5)

    node = out_socket.node
    dimensions = {"1D": 1, "2D": 2, "3D": 3, "4D": 4}
    dims = dimensions[node.noise_dimensions]
    params = {
        "type": "noise",
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "detail": convert_texture_node(ctx, node.inputs["Detail"]),
        "roughness": convert_texture_node(ctx, node.inputs["Roughness"]),
        "lacunarity": convert_texture_node(ctx, node.inputs["Lacunarity"]),
        "distortion": convert_texture_node(ctx, node.inputs["Distortion"]),
        "dimensions": dims,
        "normalize": node.normalize,
        "output": "float" if out_socket.name == "Fac" else "color",
    }

    if dims == 1 or dims == 4:
        params["w"] = convert_texture_node(ctx, node.inputs["W"])

    if dims != 1 and node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_voronoi_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexVoronoi.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/voronoi.html
    """
    if not ctx.enable_voronoi:
        return ctx.color(0.5)

    node = out_socket.node
    dimensions = {"1D": 1, "2D": 2, "3D": 3, "4D": 4}
    dims = dimensions[node.voronoi_dimensions]
    params = {
        "type": "voronoi",
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "randomness": convert_texture_node(ctx, node.inputs["Randomness"]),
        "dimensions": dims,
        "feature": node.feature.lower().replace("_", " "),
        "distance": node.distance.lower(),
        "output": out_socket.name.lower(),
    }

    if params["feature"] == "smooth f1":
        params["smoothness"] = convert_texture_node(ctx, node.inputs["Smoothness"])

    if dims == 1 or dims == 4:
        params["w"] = convert_texture_node(ctx, node.inputs["W"])

    if dims != 1 and node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_musgrave_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexMusgrave.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/musgrave.html
    """
    if not ctx.enable_musgrave:
        return ctx.color(0.5)

    node = out_socket.node
    dimensions = {"1D": 1, "2D": 2, "3D": 3, "4D": 4}
    dims = dimensions[node.noise_dimensions]
    params = {
        "type": "musgrave",
        "fractal type": node.musgrave_type.lower().replace("_", " "),
        "scale": convert_texture_node(ctx, node.inputs["Scale"]),
        "detail": convert_texture_node(ctx, node.inputs["Detail"]),
        "dimension": convert_texture_node(ctx, node.inputs["Dimension"]),
        "lacunarity": convert_texture_node(ctx, node.inputs["Lacunarity"]),
        "offset": convert_texture_node(ctx, node.inputs["Offset"]),
        "gain": convert_texture_node(ctx, node.inputs["Gain"]),
        "dimensions": dims,
    }

    if dims == 1 or dims == 4:
        params["w"] = convert_texture_node(ctx, node.inputs["W"])

    if dims != 1 and node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_layer_weight_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeLayerWeight.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/layer_weight.html
    """
    if not ctx.enable_layer_weight:
        return ctx.color(0.5)

    node = out_socket.node
    if out_socket.name == "Fresnel":
        if node.inputs["Blend"].is_linked:
            ctx.report(
                {"WARNING"},
                "Textured Blend values for Fresnel are not currently supported in Darts. Using the default value instead.",
            )
        return {
            "type": "fresnel",
            "ior": 1.0 / max(1.0 - node.inputs["Blend"].default_value, 1e-5),
        }
    elif out_socket.name == "Facing":
        return {
            "type": "facing",
            "blend": convert_texture_node(ctx, node.inputs["Blend"]),
        }
    else:
        raise NotImplementedError(
            "Unsupported Layer Weight type, expecting either 'Fresnel' or 'Facing'"
        )


def convert_mix_rgb_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeMixRGB.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/color/mix.html
    """
    if not ctx.enable_mix_rgb:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "mix",
        "blend type": node.blend_type.lower().replace("_", " "),
        "clamp result": node.use_clamp,
        "factor": convert_texture_node(ctx, node.inputs["Fac"]),
        "a": convert_texture_node(ctx, node.inputs["Color1"]),
        "b": convert_texture_node(ctx, node.inputs["Color2"]),
    }


def convert_mix_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeMix.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/mix.html
    """
    if not ctx.enable_mix_node:
        return dummy_color(ctx)

    node = out_socket.node

    if node.data_type != "RGBA" and node.data_type != "FLOAT":
        raise NotImplementedError(
            "Only Color and Float mix nodes are currently supported in Darts"
        )
    return {
        "type": "mix",
        "blend type": node.blend_type.lower().replace("_", " "),
        "clamp factor": node.clamp_factor,
        "clamp result": node.clamp_result,
        "factor": convert_texture_node(ctx, node.inputs["Fac"]),
        "a": convert_texture_node(ctx, node.inputs["Color1"]),
        "b": convert_texture_node(ctx, node.inputs["Color2"]),
    }


def convert_clamp_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeClamp.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/clamp.html
    """
    if not ctx.enable_clamp:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "clamp",
        "clamp type": node.clamp_type.lower(),
        "value": convert_texture_node(ctx, node.inputs["Value"]),
        "min": convert_texture_node(ctx, node.inputs["Min"]),
        "max": convert_texture_node(ctx, node.inputs["Max"]),
    }


def convert_fresnel_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeFresnel.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/fresnel.html
    """
    if not ctx.enable_fresnel:
        return ctx.color(0.5)

    node = out_socket.node
    if node.inputs["IOR"].is_linked:
        ctx.report(
            {"WARNING"},
            "Textured IOR values are not supported in Darts. Using the default value instead.",
        )

    return {"type": "fresnel", "ior": node.inputs["IOR"].default_value}


def convert_rgb_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeRGB.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/rgb.html
    """
    node = out_socket.node
    return ctx.color(node.color)


def convert_blackbody_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeBlackbody.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/blackbody.html
    """
    if not ctx.enable_blackbody:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "blackbody",
        "temperature": convert_texture_node(ctx, node.inputs["Temperature"]),
    }


def convert_wavelength_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeWavelength.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/wavelength.html
    """
    if not ctx.enable_wavelength:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "wavelength",
        "wavelength": convert_texture_node(ctx, node.inputs["Wavelength"]),
    }


def convert_coord_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexCoord.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/texture_coordinate.html
    """
    if not ctx.enable_coord:
        return dummy_color(ctx)

    node = out_socket.node

    if node.object is not None:
        ctx.report(
            {"WARNING"},
            "Darts does not currently support texture coordinates from other objects. Ignoring.",
        )

    return {"type": "coord", "coordinate": out_socket.name.lower()}


def convert_mapping_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeMapping.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/vector/mapping.html
    """
    if not ctx.enable_mapping:
        return None

    node = out_socket.node

    params = {"type": "mapping", "vector type": node.vector_type.lower()}
    ctx.info(f"Writing '{params['vector type']}' mapping node.")

    if (
        node.inputs["Location"].is_linked
        or node.inputs["Rotation"].is_linked
        or node.inputs["Scale"].is_linked
    ):
        raise NotImplementedError(
            "Location, Rotation, and Scale inputs shouldn't be linked"
        )

    params["transform"] = ctx.LRS_matrix(
        node.inputs["Location"].default_value,
        node.inputs["Rotation"].default_value,
        node.inputs["Scale"].default_value,
    )

    if node.inputs["Vector"].is_linked:
        params["vector"] = convert_texture_node(ctx, node.inputs["Vector"])

    return params


def convert_wireframe_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeWireframe.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/wireframe.html
    """
    if not ctx.enable_wireframe:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "wireframe",
        "size": convert_texture_node(ctx, node.inputs["Size"]),
        "pixel size": node.use_pixel_size,
    }


def convert_light_path_texture_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeLightPath.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/light_path.html
    """

    return {"type": "light path", "output": out_socket.name.lower()}


def convert_color_attrib_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeVertexColor.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/input/vertex_color.html
    """

    node = out_socket.node
    return {
        "type": "vertex colors",
    }


def convert_val_to_rgb_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeValToRGB.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/color_ramp.html
    """
    if not ctx.enable_color_ramp:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "color ramp",
        "factor": convert_texture_node(ctx, node.inputs["Fac"]),
        "color mode": node.color_ramp.color_mode.lower(),
        "interpolation": node.color_ramp.interpolation.lower().replace("_", "-"),
        "hue interpolation": node.color_ramp.hue_interpolation.lower(),
        "elements": [
            {
                "position": e.position,
                "color": ctx.color(e.color),
                "alpha": e.alpha,
            }
            for e in node.color_ramp.elements
        ],
        "output": "float" if out_socket.name == "Alpha" else "color",
    }


def convert_separate_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeSeparateXYZ.html
                https://docs.blender.org/api/latest/bpy.types.ShaderNodeSeparateColor.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/separate_xyz.html
               https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/separate_color.html
    """
    if not ctx.enable_separate:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "separate",
        "input": convert_texture_node(
            ctx, node.inputs["Color"] if node.inputs["Color"] else node.inputs["Vector"]
        ),
        "mode": node.mode.lower() if node.mode else "xyz",
        "component": out_socket.name.lower(),
    }


def convert_gradient_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeTexGradient.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/gradient.html
    """
    if not ctx.enable_gradient:
        return dummy_color(ctx)

    node = out_socket.node
    return {
        "type": "gradient",
        "vector": convert_texture_node(ctx, node.inputs["Vector"]),
        "gradient type": node.gradient_type.lower().replace("_", " "),
    }


def convert_math_node(ctx, out_socket):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeMath.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/converter/math.html
    """
    if not ctx.enable_math:
        return dummy_color(ctx)

    node = out_socket.node
    params = {
        "type": "math",
        "operation": node.operation.lower().replace("_", " "),
        "clamp": node.use_clamp,
    }

    if len(node.inputs) > 0:
        params["a"] = convert_texture_node(ctx, node.inputs[0])
    if len(node.inputs) > 1:
        params["b"] = convert_texture_node(ctx, node.inputs[1])
    if len(node.inputs) > 2:
        params["c"] = convert_texture_node(ctx, node.inputs[2])

    return params


def convert_texture_node(ctx, socket):
    texture_converters = {
        "ShaderNodeBlackbody": convert_blackbody_node,
        "ShaderNodeTexBrick": convert_brick_texture_node,
        "ShaderNodeClamp": convert_clamp_node,
        "ShaderNodeTexChecker": convert_checker_texture_node,
        "ShaderNodeTexCoord": convert_coord_texture_node,
        "ShaderNodeTexEnvironment": convert_environment_texture_node,
        "ShaderNodeMapping": convert_mapping_node,
        "ShaderNodeFresnel": convert_fresnel_node,
        "ShaderNodeTexImage": convert_image_texture_node,
        "ShaderNodeLayerWeight": convert_layer_weight_node,
        "ShaderNodeMixRGB": convert_mix_rgb_node,
        "ShaderNodeMix": convert_mix_node,
        "ShaderNodeTexMusgrave": convert_musgrave_texture_node,
        "ShaderNodeTexNoise": convert_noise_texture_node,
        "ShaderNodeRGB": convert_rgb_node,
        "ShaderNodeTexVoronoi": convert_voronoi_texture_node,
        "ShaderNodeTexWave": convert_wave_texture_node,
        "ShaderNodeWavelength": convert_wavelength_node,
        "ShaderNodeTexWhiteNoise": convert_white_noise_texture_node,
        "ShaderNodeWireframe": convert_wireframe_texture_node,
        "ShaderNodeLightPath": convert_light_path_texture_node,
        "ShaderNodeVertexColor": convert_color_attrib_node,
        "ShaderNodeValToRGB": convert_val_to_rgb_node,
        "ShaderNodeSeparateXYZ": convert_separate_node,
        "ShaderNodeSeparateColor": convert_separate_node,
        "ShaderNodeTexGradient": convert_gradient_node,
        "ShaderNodeMath": convert_math_node,
    }

    params = None
    if socket.is_linked:
        s = ctx.follow_link(socket)
        node = s.links[0].from_node
        from_socket = s.links[0].from_socket

        if node.bl_idname in texture_converters:
            ctx.info(f"Converting a '{node.bl_idname}' Blender shader node.")
            params = texture_converters[node.bl_idname](ctx, from_socket)
            if params and isinstance(params, Iterable) and "type" in params:
                ctx.info(f"  Created a '{params['type']}' texture.")
        else:
            raise NotImplementedError(
                f"Shader node type {node.bl_idname} is not supported"
            )
    else:
        params = ctx.color(socket.default_value)

    return params


def convert_background(ctx):
    """
    convert environment lighting. Constant emitter and envmaps are supported
    """

    try:
        surface_node = ctx.get_world_input("Surface")
        if surface_node is not None:

            if "Strength" not in surface_node.inputs:
                raise NotImplementedError(
                    "Expecting a material with a 'Strength' parameter for a background"
                )

            if surface_node.inputs["Strength"].is_linked:
                raise NotImplementedError(
                    "Only default emitter 'Strength' value is supported"
                )

            strength = surface_node.inputs["Strength"].default_value
            if strength == 0:  # Don't add an emitter if it emits nothing
                ctx.info("Ignoring envmap with zero strength.")
                return 0

            if surface_node.bl_idname in ["ShaderNodeBackground", "ShaderNodeEmission"]:
                return {
                    "type": "background",
                    "color": convert_texture_node(ctx, surface_node.inputs["Color"]),
                }
            else:
                raise NotImplementedError(
                    f"Only Background and Emission nodes are supported as final nodes for background export, got '{surface_node.name}'"
                )
        else:
            # Single color field for emission, no nodes
            return ctx.color(ctx.context.scene.world.color)

    except NotImplementedError as err:
        ctx.report(
            {"WARNING"},
            f"Error while converting background: {err.args[0]}. Using default.",
        )
        return 5
