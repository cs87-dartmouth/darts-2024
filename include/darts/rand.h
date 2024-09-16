/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/hash.h>
#include <darts/math.h>

/** \addtogroup Random
    @{

    The Random module provides a random number generator suitable for ray tracing (based on the PCG32 random number
    generator), and several functions to generate points and directions useful in path tracing and procedural
    generation.
*/

/// Pseudorandom number generator
/**
    Adapted from minimal PCG32 code / (c) 2014 M.E. O'Neill / pcg-random.org
    Licensed under Apache License 2.0 (NO WARRANTY, etc. see https://www.pcg-random.org/download.html)

    Also the [PBRTv4](https://github.com/mmp/pbrt-v4) and Wenzel Jakob's [pcg32](https://github.com/wjakob/pcg32)
    libraries.

    Adapted to include some convenience functions for darts types like Vec2f, and Vec3f.
*/
class RNG
{
private:
    uint64_t state; // RNG state.  All values are possible.
    uint64_t inc;   // Controls which RNG sequence (stream) is selected. Must *always* be odd.

public:
    enum Constants : uint64_t
    {
        PCG32_DEFAULT_STATE  = 0x853c49e6748fea9bULL,
        PCG32_DEFAULT_STREAM = 0xda3e39cb94b95bdbULL,
        PCG32_MULT           = 0x5851f42d4c957f2dULL,
    };

    RNG() : state(PCG32_DEFAULT_STATE), inc(PCG32_DEFAULT_STREAM)
    {
    }
    RNG(uint64_t sequence_index, uint64_t init_state)
    {
        seed(sequence_index, init_state);
    }
    RNG(uint64_t sequence_index)
    {
        seed(sequence_index);
    }

    void seed(uint64_t sequence_index, uint64_t initial_state)
    {
        state = 0U;
        inc   = (sequence_index << 1u) | 1u;
        rand1u();
        state += initial_state;
        rand1u();
    }

    void seed(uint64_t sequence_index)
    {
        seed(sequence_index, mix_bits(sequence_index));
    }

    /// Generate a uniformly distributed unsigned 32-bit integer
    uint32_t rand1u()
    {
        uint64_t oldstate = state;
        // Advance internal state
        state = oldstate * PCG32_MULT + inc;
        // Calculate output function (XSH RR), uses old state for max ILP
        uint32_t xorshifted = (uint32_t)(((oldstate >> 18u) ^ oldstate) >> 27u);
        uint32_t rot        = (uint32_t)(oldstate >> 59u);
        return (xorshifted >> rot) | (xorshifted << ((~rot + 1u) & 31));
    }

    /// Generate a uniformly distributed unsigned 32-bit integer in [0, range[
    uint32_t rand1u(uint32_t range)
    {
        // Lemire's method for unbiased division-free bounded integers (with an extra tweak from M.E. O'Neill)
        // from https://www.pcg-random.org/posts/bounded-rands.html
        uint32_t x = rand1u();
        uint64_t m = uint64_t(x) * uint64_t(range);
        uint32_t l = uint32_t(m);
        if (l < range)
        {
            uint32_t t = -range;
            if (t >= range)
            {
                t -= range;
                if (t >= range)
                    t %= range;
            }
            while (l < t)
            {
                x = rand1u();
                m = uint64_t(x) * uint64_t(range);
                l = uint32_t(m);
            }
        }
        return m >> 32;
    }

    /// Generate a Vec2u where each component is a uniformly distributed unsigned 32-bit integer
    Vec2u rand2u()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1u(), rand1u()};
    }

    /// Generate a Vec3u where each component is a uniformly distributed unsigned 32-bit integer
    Vec3u rand3u()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1u(), rand1u(), rand1u()};
    }

    /// Generate a Vec4u where each component is a uniformly distributed unsigned 32-bit integer
    Vec4u rand4u()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1u(), rand1u(), rand1u(), rand1u()};
    }

    /// Generate a single precision floating point value on the interval [0, 1)
    float rand1f()
    {
        return bit_cast<float>((rand1u() >> 9) | 0x3f800000u) - 1.0f;
    }

    /// Generate a Vec2f where each component is uniformly distributed in [0, 1)
    Vec2f rand2f()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1f(), rand1f()};
    }

    /// Generate a Vec3f where each component is uniformly distributed in [0, 1)
    Vec3f rand3f()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1f(), rand1f(), rand1f()};
    }

    /// Generate a Vec4f where each component is uniformly distributed in [0, 1)
    Vec4f rand4f()
    {
        // C++'s list-initialization rules force these to be executed left-to-right
        return {rand1f(), rand1f(), rand1f(), rand1f()};
    }

    /**
        Draw uniformly distributed permutation and permute the given STL container

        From: Knuth, TAoCP Vol. 2 (3rd 3d), Section 3.4.2
    */
    template <typename Iterator>
    void shuffle(Iterator begin, Iterator end)
    {
        for (Iterator it = end - 1; it > begin; --it)
            std::iter_swap(it, begin + rand1u((uint32_t)(it - begin + 1)));
    }

    /**
        Multi-step advance function (jump-ahead, jump-back)

        The method used here is based on Brown, "Random Number Generation with Arbitrary Stride", Transactions of the
        American Nuclear Society (Nov. 1994). The algorithm is very similar to fast exponentiation.
    */
    void advance(int64_t delta_)
    {
        uint64_t cur_mult = PCG32_MULT, cur_plus = inc, acc_mult = 1u, acc_plus = 0u;

        // Even though delta is an unsigned integer, we can pass a signed integer to go backwards, it just goes "the
        // long way round".
        uint64_t delta = (uint64_t)delta_;

        while (delta > 0)
        {
            if (delta & 1)
            {
                acc_mult *= cur_mult;
                acc_plus = acc_plus * cur_mult + cur_plus;
            }
            cur_plus = (cur_mult + 1) * cur_plus;
            cur_mult *= cur_mult;
            delta /= 2;
        }
        state = acc_mult * state + acc_plus;
    }

    /// Compute the distance between two PCG32 pseudorandom number generators
    int64_t operator-(const RNG &other) const
    {
        assert(inc == other.inc);

        uint64_t cur_mult = PCG32_MULT, cur_plus = inc, cur_state = other.state, the_bit = 1u, distance = 0u;

        while (state != cur_state)
        {
            if ((state & the_bit) != (cur_state & the_bit))
            {
                cur_state = cur_state * cur_mult + cur_plus;
                distance |= the_bit;
            }
            assert((state & the_bit) == (cur_state & the_bit));
            the_bit <<= 1;
            cur_plus = (cur_mult + 1ULL) * cur_plus;
            cur_mult *= cur_mult;
        }

        return (int64_t)distance;
    }

    /// Equality operator
    bool operator==(const RNG &other) const
    {
        return state == other.state && inc == other.inc;
    }

    /// Inequality operator
    bool operator!=(const RNG &other) const
    {
        return state != other.state || inc != other.inc;
    }
};

/** @}*/

/**
    \file
    \brief Random number generator
*/