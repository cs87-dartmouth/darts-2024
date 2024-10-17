/*
    This file is part of darts – the Dartmouth Academic Ray Tracing Skeleton.

    Copyright (c) 2017-2024 by Wojciech Jarosz
*/

#include <darts/sampler.h>
#include <darts/sampling.h>

/**
    Independent sampling - returns independent uniformly distributed random numbers in \f$[0, 1)\f$.

    This class is essentially just a wrapper around a pseudorandom number generator. For more details on what
    sample generators do in general, refer to the #Sampler class.

    \ingroup Samplers
*/
class IndependentSampler : public Sampler
{
public:
    IndependentSampler(const json &j)
    {
        m_sample_count = j.at("samples").get<int>();
    }

    /**
        Create an exact clone of the current instance

        This is useful if you want to duplicate a sampler to use in multiple threads
    */
    std::unique_ptr<Sampler> clone() const override
    {
        std::unique_ptr<IndependentSampler> cloned(new IndependentSampler());
        cloned->m_sample_count      = m_sample_count;
        cloned->m_base_seed         = m_base_seed;
        cloned->m_sample_count      = m_sample_count;
        cloned->m_current_sample    = m_current_sample;
        cloned->m_current_dimension = m_current_dimension;

        cloned->m_rng = m_rng;
        return std::move(cloned);
    }

    void set_base_seed(uint32_t s) override
    {
        Sampler::set_base_seed(s);
        m_rng.seed(m_base_seed);
    }

    void start_pixel(int x, int y) override
    {
        Sampler::start_pixel(x, y);
        m_rng.seed(hash(current_sample(), m_base_seed, x, y));
    }

    float next1f() override
    {
        m_current_dimension++;
        return m_rng.rand1f();
    }

    Vec2f next2f() override
    {
        m_current_dimension += 2;
        return m_rng.rand2f();
    }

protected:
    IndependentSampler()
    {
    }

    RNG m_rng;
};

DARTS_REGISTER_CLASS_IN_FACTORY(Sampler, IndependentSampler, "independent")

/**
    \file
    \brief IndependentSampler Sampler
*/
