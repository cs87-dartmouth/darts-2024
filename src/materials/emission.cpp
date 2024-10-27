/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/

#include <darts/factory.h>
#include <darts/material.h>
#include <darts/scene.h>

/// A material that emits light equally in all directions from the front side of a surface. \ingroup Materials
class Emission : public Material
{
public:
    Emission(const json &j = json::object());

    /// Returns a constant Color3f if the ray hits the surface on the front side.
    Color3f emitted(const Ray3f &ray, const HitRecord &hit) const override;

    bool is_emissive() const override
    {
        return true;
    }


    Color3f color; ///< The emissive color of the light
};

Emission::Emission(const json &j) : Material(j)
{
    color = j.value("color", color);
}

Color3f Emission::emitted(const Ray3f &ray, const HitRecord &hit) const
{
    // only color from the normal-facing side
    if (dot(ray.d, hit.sn) > 0)
        return Color3f(0, 0, 0);
    else
        return color;
}


DARTS_REGISTER_CLASS_IN_FACTORY(Material, Emission, "emission")

/**
    \file
    \brief Emission emissive Material
*/
