/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/math.h>
#include <tuple>
#include <vector>

/**
    \name Perlin noise
    @{
*/
float        perlin_noise(const Vec1f &p);
inline float perlin_noise(float x)
{
    return perlin_noise(Vec1f{x});
}
float perlin_noise(const Vec2f &p);
float perlin_noise(const Vec3f &p);
float perlin_noise(const Vec4f &p);

static constexpr float vector_noise_offsets[4][4] = {
    {227.f, 49.f, 81.f, 73.f}, {34.f, 53.f, 23.f, -142.f}, {17.f, 113.f, 93.f, 292.f}, {23.f, 31.f, 113.f, 29.f}};

/** @}*/


/**
    \file
    \brief Perlin noise
*/
