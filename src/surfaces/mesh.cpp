/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.
    Copyright (c) 2017-2024 by Wojciech Jarosz
*/

#include <darts/factory.h>
#include <darts/mesh.h>
#include <darts/progress.h>
#include <darts/stats.h>
#include <darts/triangle.h>
#include <filesystem/resolver.h>
#include <fstream>
#include <unordered_map>

#define TINYOBJLOADER_IMPLEMENTATION // define this in only *one* .cpp file
#include <tiny_obj_loader.h>

STAT_RATIO("Geometry/Triangles per mesh", num_triangles, num_tri_meshes);
STAT_MEMORY_COUNTER("Memory/Triangles", triangle_bytes);

Mesh::Mesh(const json &j)
{
    xform           = j.value("transform", xform);
    string filename = get_file_resolver().resolve(j.at("filename").get<string>()).str();

    std::ifstream is(filename);
    if (is.fail())
        throw DartsException("Unable to open OBJ file '{}'!", filename);

    Progress progress(fmt ::format("Loading '{}'", filename));

    string warn, err;
    struct UserData
    {
        Mesh            *mesh;
        uint32_t         current_material_idx;
        map<string, int> material_map;
        string           material_prefix;
        bool             all_have_colors = true;
        bool             raw             = false;
    } data;

    data.mesh                 = this;
    data.current_material_idx = 0;
    string colorspace         = j.value("vertex colorspace", "srgb");
    data.raw                  = (colorspace == "linear" || colorspace == "raw");

    data.material_prefix = j.value("material prefix", "");
    if (data.material_prefix != "")
        spdlog::info("Prepending the string \"{}\" to all mesh material names", data.material_prefix);

    // create a default material used for any faces that don't have a material set
    // this will be the material with index 0
    auto default_material = DartsFactory<Material>::find(j);
    m.push_back(default_material);

    tinyobj::callback_t cb;

    cb.vertex_color_cb = [](void *user_data, float x, float y, float z, float r, float g, float b, bool has_color)
    {
        UserData *data = reinterpret_cast<UserData *>(user_data);
        Mesh     *mesh = data->mesh;
        Vec3f     v{x, y, z};
        mesh->bbox_o.enclose(v);
        mesh->v.push_back(mesh->xform.point(v));
        mesh->bbox_w.enclose(mesh->v.back());

        data->all_have_colors &= has_color;
        if (data->all_have_colors)
        {
            Color3f color{r, g, b};
            mesh->c.push_back(data->raw ? color : to_linear_RGB(color));
        }
    };

    cb.normal_cb = [](void *user_data, float x, float y, float z)
    {
        UserData *data = reinterpret_cast<UserData *>(user_data);
        Mesh     *mesh = data->mesh;
        // spdlog::trace("vn[{}] = {}, {}, {}", mesh->n.size(), x, y, z);

        mesh->n.push_back(normalize(mesh->xform.normal(Vec3f(x, y, z))));
    };

    cb.texcoord_cb = [](void *user_data, float x, float y, float z)
    {
        UserData *data = reinterpret_cast<UserData *>(user_data);
        Mesh     *mesh = data->mesh;
        // spdlog::trace("vt[{}] = {}, {}, {}", mesh->t.size(), x, y, z);

        mesh->t.push_back(Vec2f(x, y));
    };

    cb.index_cb = [](void *user_data, tinyobj::index_t *indices, int num_indices)
    {
        UserData *data = reinterpret_cast<UserData *>(user_data);
        Mesh     *mesh = data->mesh;

        tinyobj::warning_context context;
        context.warn        = nullptr;
        context.line_number = 0;

        if (num_indices < 3)
            throw DartsException("OBJ: Polygons must have at least 3 indices");

        tinyobj::index_t idx0 = indices[0], idx1 = indices[1], idx2;
        int              num_v = int(mesh->v.size());
        int              num_n = int(mesh->n.size());
        int              num_t = int(mesh->t.size());

        auto fix_index = [&context](int &i, int size)
        { return tinyobj::fixIndex(i, size, &i, false, context) && i >= 0 && i < size; };

        // compute the indices for the first two vertices outside the loop
        bool valid_v = true, valid_n = true, valid_t = true;
        valid_v &= fix_index(idx0.vertex_index, num_v);
        valid_n &= fix_index(idx0.normal_index, num_n);
        valid_t &= fix_index(idx0.texcoord_index, num_t);
        valid_v &= fix_index(idx1.vertex_index, num_v);
        valid_n &= fix_index(idx1.normal_index, num_n);
        valid_t &= fix_index(idx1.texcoord_index, num_t);

        // just create a naive triangle fan from the first vertex
        // each iteration just computes the indices for the one additional vertex
        for (int i = 2; i < num_indices; i++)
        {
            idx2 = indices[i];

            valid_v &= fix_index(idx2.vertex_index, num_v);
            valid_n &= fix_index(idx2.normal_index, num_n);
            valid_t &= fix_index(idx2.texcoord_index, num_t);

            // add the vertex and material indices
            mesh->vi.push_back({idx0.vertex_index, idx1.vertex_index, idx2.vertex_index});
            mesh->mi.push_back(data->current_material_idx);

            // now optionally add the normal and texture indices
            if (valid_n)
                mesh->ni.push_back({idx0.normal_index, idx1.normal_index, idx2.normal_index});

            if (valid_t)
                mesh->ti.push_back({idx0.texcoord_index, idx1.texcoord_index, idx2.texcoord_index});

            idx1 = idx2;
        }

        if (!valid_v)
            throw DartsException("OBJ: encountered an invalid vertex index");
    };

    cb.usemtl_cb = [](void *user_data, const char *name, int material_idx)
    {
        UserData *data = reinterpret_cast<UserData *>(user_data);
        Mesh     *mesh = data->mesh;

        string full_name = data->material_prefix + name;

        // check if we've already added a material with this name to the mesh
        auto it = data->material_map.find(full_name);
        if (it != data->material_map.end())
            data->current_material_idx = it->second;
        else
        {
            // try to find a material with the given name in the scene description and add it to the mesh's materials
            try
            {
                data->mesh->m.push_back(DartsFactory<Material>::find(json::object({{"material", string(full_name)}})));
                data->material_map[full_name] = data->current_material_idx = data->mesh->m.size() - 1;
            }
            catch (const std::exception &e)
            {
                spdlog::warn("When parsing OBJ file: {}\n\tUsing default material instead.\n", e.what());
                data->material_map[full_name] = data->current_material_idx = 0;
            }
        }
    };

    bool ret = tinyobj::LoadObjWithCallback(is, cb, &data, nullptr, &warn, &err);

    progress.set_done();

    // not all vertices have colors? -> clear colors
    if (!data.all_have_colors)
        c.clear();

    if (n.size() && ni.size() != vi.size())
    {
        spdlog::error("Number of normal indices does not match number of faces. Ignoring normals.");
        n.clear();
        ni.clear();
    }

    if (t.size() && ti.size() != vi.size())
    {
        spdlog::error("Number of texture indices does not match number of faces. Ignoring texture coordinates.");
        t.clear();
        ti.clear();
    }

    // compute object_to_texture space transform
    auto d            = bbox_o.diagonal();
    auto M            = mul(scaling_matrix(select(equal(d, 0.f), 1.f, 1.f / d)), translation_matrix(-bbox_o.min));
    object_to_texture = Transform(M);

    if (!warn.empty())
        spdlog::warn("Warning OBJ \"{}\": {}\n", filename, warn);

    if (!err.empty() || !ret)
        throw DartsException("Unable to open OBJ file '{}'!\n\t{}", filename, err);

    spdlog::debug(
        R"(
    # of vertices         = {}
    # of normals          = {}
    # of texcoords        = {}
    # of vertex colors    = {}
    # of vertex indices   = {}
    # of normal indices   = {}
    # of texcoord indices = {}
    # of materials        = {} + default
    xform : {}
    min: {}
    max: {}
    bottom: {}
)",
        v.size(), n.size(), t.size(), c.size(), vi.size(), ni.size(), ti.size(), m.size() - 1,
        indent(fmt::format("{}", xform.m), string("    xform : ").length()), bbox_w.min, bbox_w.max,
        (bbox_w.min + bbox_w.max) / 2.f - Vec3f(0, bbox_w.diagonal()[1] / 2.f, 0));

    ++num_tri_meshes;
    num_triangles += vi.size();
    triangle_bytes += size();
}

size_t Mesh::size() const
{
    return v.capacity() * sizeof(Vec3f) + c.capacity() * sizeof(Color3f) + n.capacity() * sizeof(Vec3f) +
           t.capacity() * sizeof(Vec2f) + vi.capacity() * sizeof(Vec3i) + ni.capacity() * sizeof(Vec3i) +
           ti.capacity() * sizeof(Vec3i) + mi.capacity() * sizeof(uint32_t);
}

void Mesh::add_to_parent(Surface *parent, shared_ptr<Surface> self, const json &j)
{
    auto mesh = std::dynamic_pointer_cast<Mesh>(self);

    if (!mesh && mesh->empty())
        return;

    for (auto index : range(mesh->vi.size()))
        parent->add_child(make_shared<Triangle>(j, mesh, int(index)));
}

DARTS_REGISTER_CLASS_IN_FACTORY(Surface, Mesh, "mesh")

/**
    \file
    \brief Mesh Surface
*/