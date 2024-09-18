/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/
#include <darts/camera.h>
#include <darts/stats.h>

STAT_COUNTER("Integrator/Camera rays traced", num_camera_rays);

Camera::Camera(const json &j)
{
    m_camera_to_world   = j.value("transform", m_camera_to_world);
    m_resolution        = j.value("resolution", m_resolution);
    m_focal_distance    = j.value("focus distance", m_focal_distance);
    m_aperture_diameter = j.value("aperture diameter", m_aperture_diameter);

    float vfov = 90.f; // Default vfov value. Override this with the value from json
    // TODO: Assignment 1: read the vertical field of view from j ("vertical fov"),
    // and compute the width and height of the image plane. Remember that
    // the "vertical fov" parameter is specified in degrees, but C++ math functions
    // assume radians. You can use deg2rad() from common.h to convert from one to
    // the other
    put_your_code_here("Assignment 1: Compute the image plane size.");
    m_size = Vec2f(2.f, 1.f);
}

Ray3f Camera::generate_ray(const Vec2f &pixel, const Vec2f &lens) const
{
    ++num_camera_rays;
    // TODO: Assignment 1: Implement camera ray generation
    // You may initially ignore the lens parameter until you implement defocus blur
    put_your_code_here("Assignment 1: Insert your camera ray generation code here");
    return Ray3f(Vec3f(0.f), Vec3f(1.f));