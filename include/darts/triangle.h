/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/mesh.h>

/// An instance of a triangle for a given face in a mesh. \ingroup Surfaces
class Triangle : public Surface
{
public:
    /// Parse and construct a single triangle
    Triangle(const json &j);

    /// Construct a single triangle of an existing mesh
    Triangle(const json &j, shared_ptr<const Mesh> mesh, uint32_t tri_number);

    bool intersect(const Ray3f &ray, HitRecord &hit) const override;

    Box3f bounds() const override;


    bool is_emissive() const override
    {
        return m_mesh && m_mesh->m[m_mesh->mi[m_face_idx]] && m_mesh->m[m_mesh->mi[m_face_idx]]->is_emissive();
    }

    // convenience function to access the i-th vertex (i must be 0, 1, or 2)
    Vec3f vertex_position(size_t i) const
    {
        return m_mesh->v[m_mesh->vi[m_face_idx][i]];
    }

    /// Return the three vertices of the triangle as columns of a 3x3 matrix
    Mat33f vertices() const
    {
        return {m_mesh->v[m_mesh->vi[m_face_idx].x], m_mesh->v[m_mesh->vi[m_face_idx].y],
                m_mesh->v[m_mesh->vi[m_face_idx].z]};
    }

    /// Return the three texture coordinates of the triangle as the columns of a 2x3 matrix
    Mat23f texture_coords() const
    {
        if (m_mesh->ti.size() > m_face_idx)
            return {m_mesh->t[m_mesh->ti[m_face_idx].x], m_mesh->t[m_mesh->ti[m_face_idx].y],
                    m_mesh->t[m_mesh->ti[m_face_idx].z]};

        // use coordinates of canonical triangle as a fallback if no texture coordinates are provided,
        return {{0, 0}, {1, 0}, {0, 1}};
    }

    /// Return the three vertex colors of the triangle as the columns of a 3x3 matrix
    Mat33f colors() const
    {
        if (m_mesh->c.size() > 0)
            return {m_mesh->c[m_mesh->vi[m_face_idx][0]], m_mesh->c[m_mesh->vi[m_face_idx][1]],
                    m_mesh->c[m_mesh->vi[m_face_idx][2]]};

        // use white as a fallback when no vertex colors are specified
        return Mat33f{1.f};
    }

    const shared_ptr<const Mesh> mesh() const
    {
        return m_mesh;
    }

    uint32_t face_index() const
    {
        return m_face_idx;
    }

protected:
    shared_ptr<const Mesh> m_mesh;
    uint32_t               m_face_idx;
};

/// Intersect a ray with a single triangle. \ingroup Surfaces
bool single_triangle_intersect(const Ray3f &ray, const Vec3f &v0, const Vec3f &v1, const Vec3f &v2, const Vec3f *n0,
                               const Vec3f *n1, const Vec3f *n2, const Vec2f &t0, const Vec2f &t1, const Vec2f &t2,
                               HitRecord &hit, const Material *material = nullptr, const Surface *surface = nullptr,
                               const Mesh *mesh = nullptr);

/**
    \file
    \brief Class #Triangle
*/