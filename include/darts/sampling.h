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

/// Uniformly sample a vector on a 2D disk with radius 1, centered around the origin
inline Vec2f sample_disk(const Vec2f &rv)
{
    return Vec2f{0.f}; // CHANGEME
}


/// Probability density of #sample_disk()
inline float sample_disk_pdf(const Vec2f &p)
{   
    return 0.0f; // CHANGEME
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

/** \name Sampling the hemisphere
    @{
*/

/// Uniformly sample a vector on the unit hemisphere around the pole (0,0,1) with respect to solid angles
inline Vec3f sample_hemisphere(const Vec2f &rv)
{
    return Vec3f{0.f}; // CHANGEME
}

/// Probability density of #sample_hemisphere()
inline float sample_hemisphere_pdf(const Vec3f &v)
{
    return 0.f; // CHANGEME
}

/// Uniformly sample a vector on the unit hemisphere around the pole (0,0,1) with respect to projected solid
/// angles
inline Vec3f sample_hemisphere_cosine(const Vec2f &rv)
{
    return Vec3f{0.f}; // CHANGEME
}

/// Probability density of #sample_hemisphere_cosine()
inline float sample_hemisphere_cosine_pdf(const Vec3f &v)
{
    return 0.f; // CHANGEME
}

/// Sample a vector on the unit hemisphere with a cosine-power density about the pole (0,0,1)
inline Vec3f sample_hemisphere_cosine_power(float exponent, const Vec2f &rv)
{
    return Vec3f{0.f}; // CHANGEME
}

/// Probability density of #sample_hemisphere_cosine_power()
inline float sample_hemisphere_cosine_power_pdf(float exponent, float cosine)
{
    return 0.f; // CHANGEME
}

/** @}*/

/** \name Sampling a spherical cap
    @{
*/

/**
    Uniformly sample a vector on a spherical cap around (0, 0, 1)

    A spherical cap is the subset of a unit sphere whose directions make an angle of less than 'theta' with the north
    pole. This function expects the cosine of 'theta' as a parameter.
 */
inline Vec3f sample_sphere_cap(const Vec2f &rv, float cos_theta_max)
{
    return Vec3f{0.f}; // CHANGEME
}

/// Probability density of #sample_sphere_cap()
inline float sample_sphere_cap_pdf(float cos_theta, float cos_theta_max)
{
    return 0.f; // CHANGEME
}

/** @}*/

/** \name Sampling a triangle
    @{
*/

/// Sample a point uniformly on a triangle, returning the barycentric coordinates.
inline Vec2f sample_triangle(const Vec2f &rv)
{
    return Vec2f{0.f}; // CHANGEME
}

/**
    Sample a point uniformly on a triangle with vertices `v0`, `v1`, `v2`.

    \param v0,v1,v2 The vertices of the triangle to sample
    \param rv       Two random variables uniformly distributed in [0,1)
*/
inline Vec3f sample_triangle(const Vec3f &v0, const Vec3f &v1, const Vec3f &v2, const Vec2f &rv)
{
    return Vec3f{0.f}; // CHANGEME
}

/// Sampling density of #sample_triangle()
inline float sample_triangle_pdf(const Vec3f &v0, const Vec3f &v1, const Vec3f &v2)
{
    return 0.f; // CHANGEME
}

/** @}*/



/** @}*/

/**
    \file
    \brief Random sampling on various domains
*/