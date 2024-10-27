/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#pragma once

#include <darts/factory.h>
#include <darts/fwd.h>
#include <darts/material.h>
#include <darts/stats.h>
#include <darts/transform.h>

/** \addtogroup Surfaces
    @{
*/

/**
    Contains information about a ray intersection hit point.

    Used by surface intersection routines to return more than just a single value. Includes the position, traveled ray
    distance, uv coordinates, the geometric and interpolated shading normals, and a pointer to the intersected surface
    and underlying material.
*/
struct HitRecord
{
    float t;  ///< Ray parameter for the hit
    Vec3f p;  ///< World-space hit position
    Vec3f gn; ///< Geometric normal
    Vec3f sn; ///< Interpolated shading normal
    Vec2f uv; ///< UV texture coordinates

    const Material *mat = nullptr; ///< Material at the hit point

    /// Default constructor that leaves all members uninitialized
    HitRecord() = default;
};

/// Data record for conveniently querying and sampling emitters.
struct EmitterRecord
{
    const Surface *emitter = nullptr; ///< Emitter this sample was generated by
    const Ray3f   *parent  = nullptr; ///< Pointer to parent ray
    Vec3f          o;                 ///< Origin point from which we sample the emitter
    Vec3f          wi;                ///< Direction vector from 'o' to 'hit.p'
    float          pdf;               ///< Solid angle density wrt. 'o'
    HitRecord        hit;               ///< Hit information at the sampled point

    /// Default constructor that sets the parent ray, but leaves all other members uninitialized
    EmitterRecord(const Ray3f &parent) : emitter(nullptr), parent(&parent)
    {
    }

    /// Initialize the parent ray and just the origin point
    EmitterRecord(const Ray3f &parent, const Vec3f o) : emitter(nullptr), parent(&parent), o(o)
    {
    }
};

/**
    This is the abstract superclass for all surfaces.

    Surfaces represent the geometry of the scene. A Surface could be an individual primitive like a #Sphere, or it could
    be composed of many smaller primitives, e.g. the triangles composing a #Mesh.
*/
class Surface
{
public:
    virtual ~Surface() = default;

    /**
        Perform any necessary precomputation before ray tracing.

        If a surface requires some precomputation (e.g. building an acceleration structure) overload this function. This
        will be called after the last child has been added and before any call to #intersect().

        The base class implementation just does nothing.
    */
    virtual void build(const Scene *scene) {};

    /**
        Add a child surface.

        This function will become useful once we create groups of objects. The base class implementation just throws an
        error.

        This function should only be used before #build() is called.
    */
    virtual void add_child(shared_ptr<Surface> surface)
    {
        throw DartsException("This surface does not support children.");
    }

    /**
        Add this surface to the \p parent surface.

        By default this function just calls #add_child() on the parent.

        This function is used by aggregate surfaces that shouldn't themselves be added to the scene (like a mesh), but
        instead need to create other surfaces (individual triangles) that get added to the scene.

        \param [in,out] parent  The parent Surface (typically the scene) to add to.
        \param [in]     self    A shared_ptr version of this
        \param [in]     j       The #json parameters used to create \p self
     */
    virtual void add_to_parent(Surface *parent, shared_ptr<Surface> self, const json &j)
    {
        parent->add_child(self);
    }

    /**
        Ray-Surface intersection test.

        Intersect a ray against this surface and return detailed intersection information.

        \param [in] ray     A 3-dimensional ray data structure with minimum/maximum extent information
        \param [out] hit    A detailed intersection record, which will be filled by the intersection query
        \return             True if an intersection was found
     */
    virtual bool intersect(const Ray3f &ray, HitRecord &hit) const
    {
        throw DartsException("Surface intersection method not implemented.");
    }
    /// Return the surface's world-space AABB.
    virtual Box3f bounds() const = 0;

    /**
        Sample a direction from \p rec.o towards this surface.

        Store result in \p rec, and return importance weight (i.e. the color of the Surface divided by the probability
        density of the sample with respect to solid angle).

        \param [in,out] rec     An emitter query record. Only \p rec.o is used as input, the remaining fields are used
                                as output.
        \param [in]     rv      Two uniformly distributed random variables on [0,1)
        \return                 The surface color value divided by the probability density of the sample.
                                A zero value means that sampling failed.
    */
    virtual Color3f sample(EmitterRecord &rec, const Vec2f &rv) const
    {
        throw DartsException("This surface does not support sampling.");
    }

    /// Return the probability density of the sample generated by #sample
    virtual float pdf(const Vec3f &o, const Vec3f &v) const
    {
        throw DartsException("This surface does not support sampling.");
    }

    /// Return whether or not this Surface's Material is emissive.
    virtual bool is_emissive() const
    {
        return false;
    }

    /**
        Sample a random child.

        For Surfaces with no children this just returns the surface itself with probability 1.

        \param [in,out] rv1 Random variable distribute uniformly in [0,1)
        \return             Pointer to a random child along with its probability of being chosen
    */
    virtual pair<const Surface *, float> sample_child(float &rv1) const
    {
        return {this, 1.f};
    }

    /// Return the probability of a child generated by #sample_child
    virtual float child_prob() const
    {
        return 1.f;
    }

};

/**
    A convenience subclass of #Surface for surfaces with a #Transform.

    Explicitly stores a #Transform which positions/orients the surface in the scene.
*/
class XformedSurface : public Surface
{
public:
    XformedSurface(const Transform &xform = Transform()) : m_xform(xform)
    {
    }

    XformedSurface(const json &j = json::object());
    virtual ~XformedSurface() = default;

    /// The world-space bounds: obtained by simply applying #m_xform to the result of #local_bounds()
    virtual Box3f bounds() const override;

    /// Return the surface's local-space AABB.
    virtual Box3f local_bounds() const = 0;

protected:
    Transform m_xform = Transform(); ///< Local-to-world Transformation
};

/**
    Adds a #Material to #XformedSurface.

    Explicitly stores a #Transform which positions/orients the surface in the scene and pointer to a single #Material
    which specifies the light reflectance properties.
*/
class XformedSurfaceWithMaterial : public XformedSurface
{
public:
    XformedSurfaceWithMaterial(shared_ptr<const Material> material, const Transform &xform = Transform()) :
        XformedSurface(xform), m_material(material)
    {
    }

    XformedSurfaceWithMaterial(const json &j = json::object());
    virtual ~XformedSurfaceWithMaterial() = default;

    /// Return whether or not this Surface's #Material is emissive.
    bool is_emissive() const override;

protected:
    shared_ptr<const Material> m_material;
};

STAT_RATIO("Intersections/Total intersection tests per ray", g_num_total_intersection_tests, g_num_traced_rays);

/** @}*/

/**
    \file
    \brief Class #HitRecord, #Surface, and #XformedSurfaceWithMaterial.
*/
