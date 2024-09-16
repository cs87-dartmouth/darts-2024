/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz

    Adapted from pbrt, Copyright(c) 1998-2020 Matt Pharr, Wenzel Jakob, and Greg Humphreys.
    Licensed under the Apache License, Version 2.0.
    SPDX: Apache-2.0
*/
#pragma once

#include <darts/math.h>

/** \addtogroup Math
    @{
*/

/** \name Hashing

    These hashing functions allow you to map an arbitrary number of parameters to a `uint64_t`, `float`, or vector of
    floats.
    @{
*/

// https://github.com/explosion/murmurhash/blob/master/murmurhash/MurmurHash2.cpp
inline uint64_t MurmurHash64A(const unsigned char *key, size_t len, uint64_t seed)
{
    const uint64_t m = 0xc6a4a7935bd1e995ull;
    const int      r = 47;

    uint64_t h = seed ^ (len * m);

    const unsigned char *end = key + 8 * (len / 8);

    while (key != end)
    {
        uint64_t k;
        std::memcpy(&k, key, sizeof(uint64_t));
        key += 8;

        k *= m;
        k ^= k >> r;
        k *= m;

        h ^= k;
        h *= m;
    }

    switch (len & 7)
    {
    case 7: h ^= uint64_t(key[6]) << 48;
    case 6: h ^= uint64_t(key[5]) << 40;
    case 5: h ^= uint64_t(key[4]) << 32;
    case 4: h ^= uint64_t(key[3]) << 24;
    case 3: h ^= uint64_t(key[2]) << 16;
    case 2: h ^= uint64_t(key[1]) << 8;
    case 1: h ^= uint64_t(key[0]); h *= m;
    };

    h ^= h >> r;
    h *= m;
    h ^= h >> r;

    return h;
}

// Hashing Inline Functions
// http://zimbry.blogspot.ch/2011/09/better-bit-mixing-improving-on.html
inline uint64_t mix_bits(uint64_t v)
{
    v ^= (v >> 31);
    v *= 0x7fb5d329728ea185;
    v ^= (v >> 27);
    v *= 0x81dadef4bc2dd44d;
    v ^= (v >> 33);
    return v;
}

/// Hash an buffer of input values to a single uint64_t
template <typename T>
inline uint64_t hash_buffer(const T *ptr, size_t size, uint64_t seed = 0)
{
    return MurmurHash64A((const unsigned char *)ptr, size, seed);
}

template <typename... Args>
inline uint64_t hash(Args... args);

template <typename... Args>
inline void hash_recursive_copy(char *buf, Args...);

template <>
inline void hash_recursive_copy(char *buf)
{
}

template <typename T, typename... Args>
inline void hash_recursive_copy(char *buf, T v, Args... args)
{
    std::memcpy(buf, &v, sizeof(T));
    hash_recursive_copy(buf + sizeof(T), args...);
}

/// Hash an arbitrary number of input parameters to a single uint64_t
template <typename... Args>
inline uint64_t hash(Args... args)
{
    // C++, you never cease to amaze: https://stackoverflow.com/a/57246704
    constexpr size_t sz = (sizeof(Args) + ... + 0);
    constexpr size_t n  = (sz + 7) / 8;
    uint64_t         buf[n];
    hash_recursive_copy((char *)buf, args...);
    return MurmurHash64A((const unsigned char *)buf, sz, 0);
}

/// Hash an arbitrary number of input parameters to a single float
template <typename... Args>
inline float hash_to_float(Args... args)
{
    return uint32_t(hash(args...)) * 0x1p-32f;
}

/// Hash an arbitrary number of input parameters to a Vec2f
template <typename... Args>
inline Vec2f hash_to_float2(Args... args)
{
    // reuse one 64-bit hash for two 32-bit values
    uint64_t h1 = hash(args...);
    return Vec2u{(uint32_t)((h1 & 0xFFFFFFFF00000000LL) >> 32), (uint32_t)(h1 & 0xFFFFFFFFLL)} * 0x1p-32f;
}

/// Hash an arbitrary number of input parameters to a Vec3f
template <typename... Args>
inline Vec3f hash_to_float3(Args... args)
{
    return {hash_to_float2(args...), hash_to_float(2, args...)};
}

/// Hash an arbitrary number of input parameters to a Vec4f
template <typename... Args>
inline Vec4f hash_to_float4(Args... args)
{
    auto xy = hash_to_float2(args...);
    auto zw = hash_to_float2(2, args...);
    return {xy.x, xy.y, zw.x, zw.y};
}

/** @}*/

/**
    \file
    \brief Contains various hashing functions
*/
