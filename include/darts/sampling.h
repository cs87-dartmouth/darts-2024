/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/common.h>
#include <darts/rand.h>

/** \addtogroup Random
    @{
*/

/** \name Global RNG and rejection sampling
    @{
*/

/// Global random number generator that produces floats between <tt>[0,1)</tt>
inline float randf()
{
    static RNG rng = RNG();
    return rng.rand1f();
}

/// Sample a random point uniformly within a unit sphere (uses the global randf() RNG and rejection sampling)
inline Vec3f random_in_unit_sphere()
{
    Vec3f p;
    do
    {
        float a = randf();
        float b = randf();
        float c = randf();
        p       = 2.0f * Vec3f(a, b, c) - Vec3f(1);
    } while (length2(p) >= 1.0f);

    return p;
}

/// Sample a random point uniformly within a unit disk (uses the global randf() RNG and rejection sampling)
inline Vec2f random_in_unit_disk()
{
    Vec2f p;
    do
    {
        float a = randf();
        float b = randf();
        p       = 2.0f * Vec2f(a, b) - Vec2f(1);
    } while (length2(p) >= 1.0f);

    return p;
}

/** @}*/


/** \name Sampling a circle and disk
    @{
*/

/// Uniformly sample a point on a unit circle, centered at the origin
inline Vec2f sample_circle(float rv)
{
    auto angle = 2.f * M_PI * rv;
    return {std::cos(angle), std::sin(angle)};
}

/// Probability density of #sample_circle()
inline float sample_circle_pdf()
{
    return 0.5f * INV_PI;
}

/** @}*/

/** \name Sampling a sphere or a ball
    @{
*/

/// Uniformly sample a vector on the unit 3D sphere with respect to solid angles
inline Vec3f sample_sphere(const Vec2f &rv)
{
    float z = 1.f - 2.f * rv.y;
    float r = std::sqrt(std::max(0.f, 1.f - z * z));
    return {sample_circle(rv.x) * r, z};
}

/// Probability density of #sample_sphere()
inline float sample_sphere_pdf()
{
    return INV_FOURPI;
}

/// Uniformly sample a vector on a unit 4-dimensional hypersphere using Marsaglia's (1972) method
inline Vec4f sample_4sphere(const Vec4f &rv)
{
    // If you are interested in supporting 4D Perlin noise, then you would need to implement this function.
    // We provide an implementation below that depends on sample_disk() which you will implement in PA4.
    // Once you have that, you can uncomment the below implementation, but this is not needed for PA3.
    return Vec4f{0.f}; // CHANGEME
    // auto p1 = sample_disk({rv.x, rv.y});
    // auto p2 = sample_disk({rv.z, rv.w});
    // auto r  = std::sqrt((1.f - length2(p1)) / length2(p2));
    // return {p1.x, p1.y, p2.x * r, p2.y * r};
}

/// Probability density of #sample_4sphere()
inline float sample_4sphere_pdf()
{
    return 0.5f * INV_PI * INV_PI;
}

/** @}*/





/** @}*/

/**
    \file
    \brief Random sampling on various domains
*/