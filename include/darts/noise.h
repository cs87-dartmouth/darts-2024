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

/** @}*/


/**
    \file
    \brief Perlin noise
*/
