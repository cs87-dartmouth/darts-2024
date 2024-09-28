/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/common.h>
#include <darts/ray.h>

/** \addtogroup Math
    @{
*/

/// An N-D axis-aligned bounding box consisting of two N-D points min and max
template <int N, typename T>
struct Box
{
    Vec<N, T> min; ///< The lower-bound of the interval
    Vec<N, T> max; ///< The upper-bound of the interval

    /// Create an empty box by default.
    Box() : min(std::numeric_limits<T>::max()), max(std::numeric_limits<T>::lowest())
    {
    }

    /// Create a box containing a single point in space
    explicit Box(const Vec<N, T> &p) : min(p), max(p)
    {
    }

    /// Create a box by specifying the min and max corners
    Box(const Vec<N, T> &mn, const Vec<N, T> &mx) : min(mn), max(mx)
    {
    }

    bool is_empty() const
    {
        for (int i = 0; i < N; ++i)
            if (min[i] > max[i])
                return true;
        return false;
    }

    void enclose(const Box &box2)
    {
        min = la::min(min, box2.min);
        max = la::max(max, box2.max);
    }

    void enclose(const Vec<N, T> &p)
    {
        min = la::min(min, p);
        max = la::max(max, p);
    }

    /// Check whether the box contains this \p point.
    template <bool Strict = false>
    bool contains(const Vec<N, T> &point) const
    {
        if constexpr (Strict)
            return !(la::any(la::lequal(point, min)) || la::any(la::gequal(point, max)));
        else
            return !(la::any(la::less(point, min)) || la::any(la::greater(point, max)));
    }

    bool is_finite() const
    {
        return !(std::numeric_limits<T>::has_infinity && (la::any(la::equal(std::numeric_limits<T>::infinity(), min)) ||
                                                          la::any(la::equal(std::numeric_limits<T>::infinity(), max))));
    }

    Vec<N, T> center() const
    {
        if (!is_finite())
            return Vec<N, T>();
        else
            return (min + max) / T(2);
    }
    Vec<N, T> diagonal() const
    {
        return max - min;
    }

    /// Calculate the N-dimensional volume of the bounding box
    T volume() const
    {
        return product(diagonal());
    }

    /// Calculate the N-1 dimensional volume of the boundary
    T area() const
    {
        auto d = diagonal();
        T    result(0);
        for (int i = 0; i < N; ++i)
        {
            T term(1);
            for (int j = 0; j < N; ++j)
            {
                if (i == j)
                    continue;
                term *= d[j];
            }
            result += term;
        }
        return 2 * result;
    }

    /**
        Check whether a #Ray intersects this #Box

        \param ray      The ray along which to check for intersection
        \param hitt0    If not null, stores the lower bound of the intersection interval
        \param hitt1    If not null, stores the upper bound of the intersection interval
        \return         \c true if there is an intersection
    */
    bool intersect(const Ray<N, T> &ray, T *hitt0 = nullptr, T *hitt1 = nullptr) const
    {
        // Absolute distances to lower and upper box coordinates
        Vec<N, T> inv_d{1 / ray.d};
        Vec<N, T> t_lower = (min - ray.o) * inv_d;
        Vec<N, T> t_upper = (max - ray.o) * inv_d;
        // The four t-intervals (for x-/y-/z-slabs, and ray p(t))
        Vec<N, T> t_mins{la::min(t_lower, t_upper)};
        Vec<N, T> t_maxes{la::max(t_lower, t_upper)};
        // Easy to remember: ``max of mins, and min of maxes''
        T t_box_min = std::max(ray.mint, la::maxelem(t_mins));
        T t_box_max = std::min(ray.maxt, la::minelem(t_maxes));
        if (t_box_min > t_box_max)
            return false;
        if (hitt0)
            *hitt0 = t_box_min;
        if (hitt1)
            *hitt1 = t_box_max;
        return true;
    }
};

template <typename T>
using Box2 = Box<2, T>;
template <typename T>
using Box3 = Box<3, T>;
template <typename T>
using Box4 = Box<4, T>;

using Box2f = Box2<float>;
using Box2d = Box2<double>;
using Box2i = Box2<int32_t>;
using Box2u = Box2<uint32_t>;
using Box2c = Box2<uint8_t>;

using Box3f = Box3<float>;
using Box3d = Box3<double>;
using Box3i = Box3<int32_t>;
using Box3u = Box3<uint32_t>;
using Box3c = Box3<uint8_t>;

using Box4f = Box4<float>;
using Box4d = Box4<double>;
using Box4i = Box4<int32_t>;
using Box4u = Box4<uint32_t>;
using Box4c = Box4<uint8_t>;

/** @}*/

/**
    \file
    \brief Contains the implementation of a generic, N-dimensional axis-aligned #Box class.
*/