import numpy as np
import bpy

from . import textures

RoughnessMode = {
    "GGX": "ggx",
    "BECKMANN": "beckmann",
    "ASHIKHMIN_SHIRLEY": "blinn",
    "MULTI_GGX": "ggx",
}


def make_two_sided(ctx, bsdf):
    if ctx.force_two_sided:
        ctx.info(f"  Wrapping '{bsdf['type']}' material in a 'two sided' adapter.")
        return {"type": "two sided", "both sides": bsdf}
    else:
        return bsdf


def convert_diffuse_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeBsdfDiffuse.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/diffuse.html
    """
    params = {
        "type": "diffuse",
        "color": textures.convert_texture_node(ctx, node.inputs["Color"]),
        "roughness": textures.convert_texture_node(ctx, node.inputs["Roughness"]),
    }
    return make_two_sided(ctx, params)


def convert_glossy_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeBsdfAnisotropic.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glossy.html
    """
    params = {}

    roughness = textures.convert_texture_node(ctx, node.inputs["Roughness"])

    if ctx.glossy_mode == "rough conductor":
        if node.distribution == "SHARP" or (
            not node.inputs["Roughness"].is_linked
            and node.inputs["Roughness"].default_value <= 0
        ):
            params.update({"type": "conductor"})
        else:
            params.update(
                {
                    "type": ctx.glossy_mode,
                    "distribution": RoughnessMode[node.distribution],
                }
            )

            params.update(
                {
                    "roughness": roughness,
                }
            )
            if "Anisotropy" in node.inputs:
                params.update(
                    {
                        "anisotropy": textures.convert_texture_node(
                            ctx, node.inputs["Anisotropy"]
                        ),
                    }
                )
            if "Rotation" in node.inputs:
                params.update(
                    {
                        "rotation": textures.convert_texture_node(
                            ctx, node.inputs["Rotation"]
                        ),
                    }
                )

        params.update(
            {
                "color": textures.convert_texture_node(ctx, node.inputs["Color"]),
            }
        )

    elif ctx.glossy_mode == "blinn-phong" or ctx.glossy_mode == "phong":
        if node.inputs["Roughness"].is_linked:
            raise NotImplementedError(
                "Phong and Blinn-Phong roughness parameter doesn't support textures in Darts"
            )
        else:

            def roughness_to_blinn_exponent(alpha):
                return max(2.0 / (alpha * alpha) - 1.0, 0.0)

            exponent = roughness_to_blinn_exponent(
                pow(node.inputs["Roughness"].default_value, 2)
            )
            if ctx.glossy_mode == "phong":
                exponent = exponent / 4

        if node.distribution == "SHARP" or exponent <= 0:
            params.update({"type": "metal", "roughness": 0})
        else:
            params.update(
                {
                    "type": ctx.glossy_mode,
                    "exponent": exponent,
                    "distribution": RoughnessMode[node.distribution],
                }
            )

        params.update(
            {
                "color": textures.convert_texture_node(ctx, node.inputs["Color"]),
            }
        )
    elif ctx.glossy_mode == "metal":
        params.update(
            {
                "type": ctx.glossy_mode,
                "roughness": (
                    textures.convert_texture_node(ctx, node.inputs["Roughness"])
                    if node.distribution != "SHARP"
                    else 0
                ),
                "color": textures.convert_texture_node(ctx, node.inputs["Color"]),
            }
        )

    return make_two_sided(ctx, params)


def convert_glass_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeBsdfGlass.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glass.html
    """
    params = {}

    if node.inputs["IOR"].is_linked:
        ctx.report(
            {"WARNING"},
            f"{node.name}: Textured IOR values are not supported in Darts. Using the default value instead.",
        )

    ior = node.inputs["IOR"].default_value

    roughness = textures.convert_texture_node(ctx, node.inputs["Roughness"])

    if roughness and node.distribution != "SHARP":
        params.update(
            {
                "type": "rough dielectric",
                "roughness": roughness,
                "distribution": RoughnessMode[node.distribution],
            }
        )
    else:
        params["type"] = "thin dielectric" if ior == 1.0 else "dielectric"

    params["ior"] = ior
    params["reflectance"] = params["transmittance"] = textures.convert_texture_node(
        ctx, node.inputs["Color"]
    )

    return params


def convert_emission_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeEmission.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/emission.html
    """
    if node.inputs["Strength"].is_linked:
        raise NotImplementedError("Only default emitter strength value is supported")
    else:
        radiance = node.inputs["Strength"].default_value

    if node.inputs["Color"].is_linked:
        raise NotImplementedError(
            "Only default emitter color is supported"
        )  # TODO: rgb input
    else:
        radiance = [x * radiance for x in node.inputs["Color"].default_value[:]]

    if np.sum(radiance) == 0:
        ctx.report(
            {"WARN"},
            "  Emitter has zero emission, this may cause Darts to fail! Creating a 'diffuse' material instead.",
        )
        return {"type": "diffuse", "color": ctx.color(0)}

    return {
        "type": "emission",
        "color": ctx.color(radiance),
    }


def convert_transparent_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeBsdfTransparent.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/transparent.html
    """
    return {
        "type": "transparent",
        "color": textures.convert_texture_node(ctx, node.inputs["Color"]),
    }


def convert_mix_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeMixShader.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/mix.html
    """
    if not node.inputs[1].is_linked or not node.inputs[2].is_linked:
        raise NotImplementedError("Mix shader is not linked to two materials")

    mat_I = ctx.follow_link(node.inputs[1]).links[0].from_node
    mat_II = ctx.follow_link(node.inputs[2]).links[0].from_node

    return {
        "type": "mix",
        "factor": textures.convert_texture_node(ctx, node.inputs["Fac"]),
        "a": cycles_surface_to_dict(ctx, mat_I),
        "b": cycles_surface_to_dict(ctx, mat_II),
    }


def convert_add_material(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeAddShader.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/add.html
    """
    if not node.inputs[1].is_linked or not node.inputs[2].is_linked:
        raise NotImplementedError("Add shader is not linked to two materials")

    mat_I = ctx.follow_link(node.inputs[1]).links[0].from_node
    mat_II = ctx.follow_link(node.inputs[2]).links[0].from_node

    return {
        "type": "add",
        "a": cycles_surface_to_dict(ctx, mat_I),
        "b": cycles_surface_to_dict(ctx, mat_II),
    }


def wrap_with_bump_or_normal_map(ctx, node, nested):
    if (
        (ctx.use_normal_maps or ctx.use_bump_maps)
        and "Normal" in node.inputs
        and node.inputs["Normal"].is_linked
    ):
        n = ctx.follow_link(node.inputs["Normal"]).links[0].from_node

        if n.bl_idname == "ShaderNodeNormalMap":
            if not ctx.use_normal_maps:
                return nested

            if n.space != "TANGENT":
                raise NotImplementedError(
                    f"Darts only supports tangent-space normal maps"
                )
            wrapper = {
                "type": "normal map",
                "normals": textures.convert_texture_node(ctx, n.inputs["Color"]),
                "strength": n.inputs["Strength"].default_value,
            }
        elif n.bl_idname == "ShaderNodeBump":
            if not ctx.use_bump_maps:
                return nested
            wrapper = {
                "type": "bump map",
                "height": textures.convert_texture_node(ctx, n.inputs["Height"]),
                "strength": textures.convert_texture_node(ctx, n.inputs["Strength"]),
                "distance": textures.convert_texture_node(ctx, n.inputs["Distance"]),
                "invert": n.invert,
            }
        else:
            raise NotImplementedError(
                "Only normal map and bump nodes supported for 'Normal' input"
            )

        if "name" in nested:
            wrapper["name"] = nested.pop("name")

        wrapper["nested"] = nested

        ctx.info(f"  Wrapping material with a '{wrapper['type']}'.")
        return wrapper
    else:
        return nested


def convert_volume_scatter_node(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeVolumeScatter.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_scatter.html
    """
    if (
        node.inputs["Color"].is_linked
        or node.inputs["Density"].is_linked
        or node.inputs["Anisotropy"].is_linked
    ):
        raise NotImplementedError(
            "Only homogeneous volume scattering nodes are currently supported"
        )

    return {
        "type": "homogeneous",
        "albedo": ctx.color(node.inputs["Color"].default_value),
        "total": ctx.color(node.inputs["Density"].default_value),
        "real fraction": 1.0,
        "phase function": {"type": "hg", "g": node.inputs["Anisotropy"].default_value},
    }


def convert_volume_absorption_node(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeVolumeAbsorption.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_absorption.html
    """
    if node.inputs["Color"].is_linked or node.inputs["Density"].is_linked:
        raise NotImplementedError(
            "Only homogeneous volume absorption nodes are currently supported"
        )

    return {
        "type": "homogeneous",
        "albedo": 0,
        "total": [
            max(1.0 - pow(max(x, 0.0), 0.5))
            for x in node.inputs["Color"].default_value[:]
        ],
        "real fraction": 1.0,
        "phase function": {"type": "isotropic"},
    }


def convert_volume_vdb_node(ctx, node):
    """
    Python API: https://docs.blender.org/api/latest/bpy.types.ShaderNodeVolumePrincipled.html
    User docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/volume_principled.html
    """

    ctx.info(f"Converting vdb node")

    if (
        node.inputs["Color"].is_linked
        or node.inputs["Density"].is_linked
        or node.inputs["Absorption Color"].is_linked
    ):
        raise NotImplementedError(
            "Textured density, color, or absorption colors are not supported by the nanovdb medium"
        )

    # map Blender colors to RTE coefficients
    scatter_color = np.array(ctx.color(node.inputs["Color"].default_value))
    absorption_color = np.array(
        ctx.color(node.inputs["Absorption Color"].default_value)
    )
    absorption_coeff = np.maximum(1.0 - scatter_color, 0.0) * np.maximum(
        1.0 - absorption_color, 0.0
    )

    params = {
        "type": "nanovdb",
        "density": node.inputs["Density"].default_value,
        "sigma_s": scatter_color.tolist(),
        "sigma_a": absorption_coeff.tolist(),
        "phase function": {"type": "hg", "g": node.inputs["Anisotropy"].default_value},
    }

    if node.inputs["Density Attribute"]:
        params["gridname"] = node.inputs["Density Attribute"].default_value

    return params


def cycles_volume_to_dict(ctx, node, name=None):
    """Converting one Cycles volume shader to a Darts medium"""

    ctx.info("Adding volume")

    cycles_converters = {
        "ShaderNodeVolumeScatter": convert_volume_scatter_node,
        "ShaderNodeVolumeAbsorption": convert_volume_absorption_node,
        "ShaderNodeVolumePrincipled": convert_volume_vdb_node,
    }

    params = {}
    if name is not None:
        params["name"] = ctx.material_name(name)

    if node.bl_idname in cycles_converters:
        ctx.info(f"Converting a '{node.bl_idname}' Blender volume.")
        params.update(cycles_converters[node.bl_idname](ctx, node))
        ctx.info(f"  Created a '{params['type']}' medium.")
    else:
        raise NotImplementedError(
            f"Node type: {node.bl_idname} is not supported in Darts"
        )

    return params


def cycles_surface_to_dict(ctx, node, name=None):
    """Converting a Blender surface node to Darts material format"""

    cycles_converters = {
        "ShaderNodeBsdfDiffuse": convert_diffuse_material,
        "ShaderNodeBsdfGlossy": convert_glossy_material,
        "ShaderNodeBsdfAnisotropic": convert_glossy_material,
        "ShaderNodeBsdfGlass": convert_glass_material,
        "ShaderNodeMixShader": convert_mix_material,
        "ShaderNodeAddShader": convert_add_material,
        "ShaderNodeEmission": convert_emission_material,
        "ShaderNodeBsdfTransparent": convert_transparent_material,
    }

    params = {}
    if name is not None:
        params["name"] = ctx.material_name(name)

    if node.bl_idname in cycles_converters:
        ctx.info(f"Converting a '{node.bl_idname}' Blender material.")
        params.update(cycles_converters[node.bl_idname](ctx, node))
        ctx.info(f"  Created a '{params['type']}' material.")
    else:
        raise NotImplementedError(
            f"Node type: {node.bl_idname} is not supported in Darts"
        )

    return wrap_with_bump_or_normal_map(ctx, node, params)


def get_dummy_material(ctx, name):
    params = {
        "type": "diffuse",
        "color": ctx.color([1.0, 0.0, 0.3]),
    }
    if name is not None:
        params["name"] = ctx.material_name(name)
    return params


def convert_material(ctx, b_mat):
    """Converting one material from Blender / Cycles to Darts"""

    media_params = None

    if b_mat.use_nodes:
        try:
            output_node_id = "Material Output"
            if output_node_id not in b_mat.node_tree.nodes:
                raise NotImplementedError("Cannot find material output node")

            output_node = b_mat.node_tree.nodes[output_node_id]

            if (
                "Surface" in output_node.inputs
                and output_node.inputs["Surface"].is_linked
            ):
                surface_node = (
                    ctx.follow_link(output_node.inputs["Surface"]).links[0].from_node
                )
                mat_params = cycles_surface_to_dict(ctx, surface_node, b_mat.name_full)
            else:
                mat_params = {"type": "transparent"}

            if (
                "Volume" in output_node.inputs
                and output_node.inputs["Volume"].is_linked
            ):
                volume_node = (
                    ctx.follow_link(output_node.inputs["Volume"]).links[0].from_node
                )
                medium_name = b_mat.name_full + " volume"
                media_params = cycles_volume_to_dict(ctx, volume_node, medium_name)
                mat_params["interior medium"] = medium_name

            if (
                "Displacement" in output_node.inputs
                and output_node.inputs["Displacement"].is_linked
            ):
                ctx.report(
                    {"WARNING"},
                    f"Material '{b_mat.name_full}': Displacement maps are not supported. Consider converting them to bump maps first",
                )
        except NotImplementedError as e:
            ctx.report(
                {"WARNING"},
                f"Export of material '{b_mat.name_full}' failed: {e.args[0]}. Exporting a dummy material instead.",
            )
            mat_params = get_dummy_material(ctx, b_mat.name_full)
    else:
        mat_params = get_dummy_material(ctx, b_mat.name_full)
        mat_params.update({"color": ctx.color(b_mat.diffuse_color)})

    return mat_params, media_params


def export(ctx, meshes):
    """Write out the materials to Darts format"""

    ctx.info(f"Writing default diffuse material")
    materials = [{"type": "diffuse", "name": "default", "color": 0.2}]
    media = []

    if ctx.material_mode == "DIFFUSE":
        for mat in bpy.data.materials:
            # skip any materials that aren't being used
            if mat.name_full == "Dots Stroke" or mat.users == 0:
                continue

            ctx.info(f"Writing placeholder for material '{mat.name_full}'")
            name = mat.name_full
            params = get_dummy_material(ctx, mat.name_full)
            materials.append(params)

    elif ctx.material_mode == "CONVERT":
        for mesh in meshes:
            if not mesh.data or not mesh.data.materials:
                continue
            ctx.info(
                f"Object '{mesh.name_full}' of type '{mesh.type}' has {len(mesh.data.materials)} materials."
            )
            for mat in mesh.data.materials:

                # skip any materials that aren't being used
                if not mat:
                    continue
                if mat.name_full == "Dots Stroke" or mat.users == 0:
                    ctx.info(f"Skipping unused material '{mat.name_full}'")
                    continue

                # skip if we've already exported this material
                mat_id = f"mat-{mat.name_full}"
                if mat_id in ctx.already_exported.keys():
                    ctx.info(
                        f"Skipping previously exported material '{mat.name_full}'."
                    )
                    continue

                ctx.info(
                    f"Exporting material '{mat.name_full}', with {mat.users} users."
                )

                mat_params, media_params = convert_material(ctx, mat)
                ctx.already_exported[mat_id] = mat_params

                materials.append(mat_params)
                if media_params:
                    media.append(media_params)

    return materials, media
