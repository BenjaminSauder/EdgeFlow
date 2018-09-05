import numpy as np
import math
import mathutils


def catmullrom(P0, P1, P2, P3, a, nPoints=100):
    """
    P0, P1, P2, and P3 should be (x,y,z) point pairs that define the Catmull-Rom spline.
    nPoints is the number of points to include in this curve segment.
    """
    # Convert the points to numpy so that we can do array multiplication
    P0, P1, P2, P3 = map(np.array, [P0, P1, P2, P3])

    # Calculate t0 to t4
    alpha = a

    def tj(ti, Pi, Pj):
        xi, yi, zi = Pi
        xj, yj, zj = Pj

        # ( ( (xj-xi)**2 + (yj-yi)**2 )**0.5 )**alpha + ti
        a = (xj - xi) ** 2 + (yj - yi) ** 2 + (zj - zi) ** 2
        b = a ** 0.5
        c = b ** alpha
        return c + ti

    t0 = 0
    t1 = tj(t0, P0, P1)
    t2 = tj(t1, P1, P2)
    t3 = tj(t2, P2, P3)

    # Only calculate points between P1 and P2
    t = np.linspace(t1, t2, nPoints)

    # Reshape so that we can multiply by the points P0 to P3
    # and get a point for each value of t.
    t = t.reshape(len(t), 1)

    A1 = (t1 - t) / (t1 - t0) * P0 + (t - t0) / (t1 - t0) * P1
    A2 = (t2 - t) / (t2 - t1) * P1 + (t - t1) / (t2 - t1) * P2
    A3 = (t3 - t) / (t3 - t2) * P2 + (t - t2) / (t3 - t2) * P3

    B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
    B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3

    C = (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2
    return C


def hermite_1d(y0, y1, y2, y3, mu, tension, bias):
    mu2 = mu * mu
    mu3 = mu2 * mu

    m0 = (y1 - y0) * (1 + bias) * (1 - tension) / 2
    m0 += (y2 - y1) * (1 - bias) * (1 - tension) / 2
    m1 = (y2 - y1) * (1 + bias) * (1 - tension) / 2
    m1 += (y3 - y2) * (1 - bias) * (1 - tension) / 2
    a0 = 2 * mu3 - 3 * mu2 + 1
    a1 = mu3 - 2 * mu2 + mu
    a2 = mu3 - mu2
    a3 = -2 * mu3 + 3 * mu2

    return a0 * y1 + a1 * m0 + a2 * m1 + a3 * y2


def hermite_3d(p1, p2, p3, p4, mu, tension, bias):
    '''
    Mu: For interpolated values between p2 and p3 mu ranges between 0 and 1
    Tension: 1 is high, 0 normal, -1 is low
    Bias: 0 is even,
         positive is towards first segment,
         negative towards the other
    
    :return: List
    '''
    x = hermite_1d(p1[0], p2[0], p3[0], p4[0], mu, tension, bias)
    y = hermite_1d(p1[1], p2[1], p3[1], p4[1], mu, tension, bias)
    z = hermite_1d(p1[2], p2[2], p3[2], p4[2], mu, tension, bias)

    return [x, y, z]
