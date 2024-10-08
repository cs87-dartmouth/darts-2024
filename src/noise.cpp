/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz

    This implementation uses pure hashing and random sampling with no precomputed arrays.
*/
#include <darts/common.h>
#include <darts/noise.h>
#include <darts/sampling.h>

namespace
{

// from: https://digitalfreepen.com/2017/06/20/range-perlin-noise.html
// The maximum range using unit length gradient vectors is [-sqrt(N/4), sqrt(N/4)]
// normalization factor to make noise range from [-1, 1]
static const float perlin_normalization[4] = {std::sqrt(4.f / 1.f), std::sqrt(4.f / 2.f), std::sqrt(4.f / 3.f),
                                              std::sqrt(4.f / 4.f)};

inline Vec1f rand_dir(const Vec1i &i)
{
    return Vec1f{2.f * hash_to_float(i) - 1.f};
}

inline Vec2f rand_dir(const Vec2i &i)
{
    return sample_circle(hash_to_float(i));
}

inline Vec3f rand_dir(const Vec3i &i)
{
    return sample_sphere(hash_to_float2(i));
}

inline Vec4f rand_dir(const Vec4i &i)
{
    return sample_4sphere(hash_to_float4(i));
}

// 5th order interpolation
// first and second derivatives are continuous
inline float f(float t)
{
    t = std::fabs(t);
    return t >= 1.0f ? 0.0f : 1.f - t * t * t * (t * (t * 6 - 15) + 10);
}

template <int N>
inline float surflet(const Vec<N, float> &offset, const Vec<N, float> &grad)
{
    return la::product(la::apply(f, offset)) * dot(offset, grad);
}

template <int N>
inline float perlin_noise_nd(const Vec<N, float> &p)
{
    float       result = 0.f;
    Vec<N, int> cell{la::floor(p)};
    for (auto grid : range(cell, cell + Vec<N, int>{2}))
        result += surflet(p - grid, rand_dir(grid));
    return result * perlin_normalization[N - 1];
}

} // namespace

//
// Perlin noise
//

float perlin_noise(const Vec1f &p)
{
    return perlin_noise_nd(p);
}

float perlin_noise(const Vec2f &p)
{
    return perlin_noise_nd(p);
}

float perlin_noise(const Vec3f &p)
{
    return perlin_noise_nd(p);
}

float perlin_noise(const Vec4f &p)
{
    return perlin_noise_nd(p);
}

