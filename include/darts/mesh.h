/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/surface.h>

/**
    A triangle mesh.

    This class stores a triangle mesh object and provides numerous functions
    for querying the individual triangles. Subclasses of #Mesh implement
    the specifics of how to create its contents (e.g. by loading from an
    external file)

    \ingroup Surfaces
    \ingroup Helpers
*/
struct Mesh : public Surface
{
public:
    /// Create an empty mesh
    Mesh()
    {
    }

    /// Try to load a mesh from an OBJ file
    Mesh(const json &j);

    Box3f bounds() const override
    {
        return bbox_w;
    }

    bool empty() const
    {
        return vi.empty() || v.empty();
    }

    /// Report the approximate size (in bytes) of the mesh
    size_t size() const;

    vector<Vec3f>                      v;     ///< Vertex positions
    vector<Vec3f>                      n;     ///< Vertex normals
    vector<Vec2f>                      t;     ///< Vertex texture coordinates
    vector<Color3f>                    c;     ///< Vertex colors
    vector<shared_ptr<const Material>> m;     ///< All materials in the mesh
    vector<Vec3i>                      vi;    ///< Vertex indices per face (triangle)
    vector<Vec3i>                      ni;    ///< Normal indices per face (triangle)
    vector<Vec3i>                      ti;    ///< Texture indices per face (triangle)
    vector<uint32_t>                   mi;    ///< One material index per face (triangle)
    Transform                          xform; ///< Transformation that the data has already been transformed by
    Transform object_to_texture;              ///< Transformation from object space to texture (bounding box) space
    Box3f     bbox_w;                         ///< The bounds, after transformation (in world space)
    Box3f     bbox_o;                         ///< The bounds, before transformation (in object space)

    virtual void add_to_parent(Surface *parent, shared_ptr<Surface> self, const json &j) override;
};

/**
    \file
    \brief Class #Mesh
*/
