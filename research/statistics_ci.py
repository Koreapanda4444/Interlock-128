"""Marginal Wilson score intervals for descriptive binomial reference counts."""
import math
from statistics import NormalDist


def wilson(count, samples, confidence=0.95):
    if samples <= 0 or not 0 <= count <= samples or not 0 < confidence < 1:
        raise ValueError("valid count, positive samples and confidence in (0,1) required")
    z = NormalDist().inv_cdf((1+confidence)/2)
    p = count/samples
    denominator = 1+z*z/samples
    center = (p+z*z/(2*samples))/denominator
    half = z*math.sqrt(p*(1-p)/samples+z*z/(4*samples*samples))/denominator
    lower = 0.0 if count == 0 else max(0.0,center-half)
    upper = 1.0 if count == samples else min(1.0,center+half)
    return lower,upper
