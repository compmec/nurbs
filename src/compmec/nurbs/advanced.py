"""
This file contains Advanced Geometric Algorithms
In Nurbs book, it correspond to chapter 6
"""
from typing import Set, Tuple

import numpy as np

from compmec.nurbs import heavy
from compmec.nurbs.calculus import Derivate
from compmec.nurbs.curves import Curve


class Projection:
    @staticmethod
    def __newton_point_on_curve(
        point: Tuple[float], curves: Tuple[Curve], initparam: float
    ) -> float:
        """
        Returns the parameter ui from newton's iteration
            u_{i+1} = u_{i} - f(u_{i})/f'(u_{i})
        The point is
        """
        tolerance1 = 1e-6
        umin, umax = curves[0].knotvector.limits
        niter = 0
        while True:
            bezui = curves[0](initparam) - point
            dbezui = curves[1](initparam)
            ddbezui = curves[2](initparam)
            upper = np.inner(dbezui, bezui)
            lower = np.inner(ddbezui, bezui)
            lower += np.inner(dbezui, dbezui)
            diff = upper / lower
            initparam -= diff
            if initparam < umin:
                return (umin,)
            if initparam > umax:
                return (umax,)
            if np.abs(diff) < tolerance1:
                return [initparam]
            niter += 1

    @staticmethod
    def point_on_bezier(point: Tuple[float], bezier: Curve) -> Tuple[float]:
        umin, umax = bezier.knotvector.limits
        curves = [bezier]
        curves.append(Derivate.curve(curves[0]))
        curves.append(Derivate.curve(curves[1]))
        tparams = np.linspace(umin, umax, 5)
        tvalues = set()
        for tparam in tparams:
            newt = Projection.__newton_point_on_curve(point, curves, tparam)
            tvalues |= set(newt)
        return tuple(tvalues)

    @staticmethod
    def point_on_curve(point: Tuple[float], curve: Curve) -> Tuple[float]:
        """
        This function finds the parameter tstar in [tmin, tmax] such
        minimizes the distance abs(curve(tstar) - point).
        Trully, it minimizes the distance square, related to the inner
        product < C(u) - P, C(u) - P > = abs(C(u)-P)^2
        This function finds the solution of
            f(u) = < C'(u), C(u) - P > = 0
        Since it's possible to have more than one solution:
            for example, the center of a circle is at equal distance always
        then we return a list of parameters

        First, we decompose the curve in beziers, and try to find
        the minimum distance of each bezier curve.
        We use Newton's method
        """
        point = np.array(point)
        beziers = curve.split()
        for bez in beziers:
            bez.clean()
        tvalues = set()
        for bezier in beziers:
            newtvalues = Projection.point_on_bezier(point, bezier)
            tvalues |= set(newtvalues)
        tvalues = tuple(tvalues)
        tvalues = np.array(tvalues)
        distances = [np.linalg.norm(point - curve(t)) for t in tvalues]
        minimaldistance = np.min(distances)
        indexs = np.where(abs(distances - minimaldistance) < 1e-6)[0]
        tvalues = tvalues[indexs]
        tvalues.sort()
        return tuple(tvalues)


class Intersection:
    @staticmethod
    def filter_pairs(pairs: Tuple[Tuple[float]], tolerance: float = 1e-9):
        pairs = np.array(pairs, dtype="float64")
        filteredpairs = []
        for pair in pairs:
            inside = False
            for filtpair in filteredpairs:
                if np.linalg.norm(pair - filtpair) < tolerance:
                    inside = True
            if not inside:
                filteredpairs.append(pair)
        filteredpairs = tuple([tuple(pair) for pair in filteredpairs])
        return filteredpairs

    @staticmethod
    def pairs_min_distance(
        pairs: Tuple[float], curvea: Curve, curveb: Curve, tolerance: float = 1e-9
    ):
        pairs = heavy.totuple(pairs)
        distances = np.empty(len(pairs), dtype="float64")
        for k, (ti, uj) in enumerate(pairs):
            pointati = curvea.eval(ti)
            pointbuj = curveb.eval(uj)
            distances[k] = np.linalg.norm(pointati - pointbuj)
        distances = np.abs(distances)
        matchs = np.abs(distances - np.min(distances)) < tolerance
        pairs = np.array(pairs, dtype="float64")[matchs]
        return heavy.totuple(pairs)

    @staticmethod
    def __newton_bcurve_and_bcurve(
        pair: Tuple[float],
        curvesa: Tuple[Curve],
        curvesb: Tuple[Curve],
        limits: Tuple[float],
    ):
        """
        We supose pair is inside limits
        """
        tmin, tmax = limits[0]
        umin, umax = limits[1]
        for niter in range(10):
            diff = curvesa[0].eval(pair[0])
            dati = curvesa[1].eval(pair[0])
            ddati = curvesa[2].eval(pair[0])
            diff -= curvesb[0].eval(pair[1])
            dbuj = curvesb[1].eval(pair[1])
            ddbuj = curvesb[2].eval(pair[1])
            grad = np.array([np.inner(dati, diff), -np.inner(dbuj, diff)])
            ggrad = np.zeros((2, 2), dtype="float64")
            ggrad[0, 0] = np.inner(ddati, diff)
            ggrad[0, 0] += np.linalg.norm(dati) ** 2
            ggrad[1, 1] = -np.inner(ddbuj, diff)
            ggrad[1, 1] += np.linalg.norm(dbuj) ** 2
            ggrad[0, 1] = -np.inner(dati, dbuj)
            ggrad[1, 0] = ggrad[0, 1]
            denom = np.linalg.det(ggrad)
            if np.abs(denom) < 1e-9:
                return tuple()  # no convergence
            deltapair = np.linalg.solve(ggrad, grad)
            pair -= deltapair
            if pair[0] < tmin:
                pair[0] = tmin
            elif tmax < pair[0]:
                pair[0] = tmax
            if pair[1] < umin:
                pair[1] = umin
            elif umax < pair[1]:
                pair[1] = umax
            if np.linalg.norm(deltapair) < 1e-9:
                return tuple(pair)  # convergence
        if pair[0] < tmin or tmax < pair[0]:
            return tuple()  # No solution
        if pair[1] < umin or umax < pair[1]:
            return tuple()  # No solution
        return tuple(pair)

    @staticmethod
    def bcurve_and_bcurve(beziera: Curve, bezierb: Curve) -> Tuple[float, float]:
        """
        Given two bezier curves, A(t) and B(u), this function returns the
        intersections between A and B. It can be:
        - If A(t) don't touch B(u), returns empty tuple
        - If A(t) touches B(u) in a finite number of points, it returns
            the pairs [(ta, ua), (tb, ub), ..., (tk, uk)]
        - If A(t) overlaps B(u) in some interval, it returns
            The interval [(ta, tb), (ua, ub)]
            Still needs implementation
        """
        curvesa = [beziera]
        curvesa.append(Derivate.curve(curvesa[0]))
        curvesa.append(Derivate.curve(curvesa[1]))
        curvesb = [bezierb]
        curvesb.append(Derivate.curve(curvesb[0]))
        curvesb.append(Derivate.curve(curvesb[1]))
        limits = np.array([beziera.knotvector.limits, bezierb.knotvector.limits])
        tsample = np.linspace(limits[0, 0], limits[0, 1], 2)
        usample = np.linspace(limits[1, 0], limits[1, 1], 2)
        pairs = set()
        for ti in tsample:
            for uj in usample:
                # Newton's iteration
                pair = np.array((ti, uj), dtype="float64")
                pair = Intersection.__newton_bcurve_and_bcurve(
                    pair, curvesa, curvesb, limits
                )
                if len(pair):
                    pairs |= set((pair,))
        if len(pairs) == 0:
            return tuple()
        pairs = tuple(pairs)
        pairs = Intersection.filter_pairs(pairs)
        pairs = Intersection.pairs_min_distance(pairs, curvesa[0], curvesb[0])
        return heavy.totuple(pairs)

    @staticmethod
    def curve_and_curve(curvea: Curve, curveb: Curve) -> Tuple[Curve]:
        """
        Given two curves, A(t) and B(u), this function returns the
        intersections between A and B. It can be:
        - If A(t) don't touch B(u), returns empty tuple
        - If A(t) touches B(u) in a finite number of points, it returns
            the pairs [(ta, ua), (tb, ub), ..., (tk, uk)]
        - If A(t) overlaps B(u) in some interval, it returns
            The interval [(ta, tb), (ua, ub)]
            Still needs implementation
        """
        beziersa = curvea.split()
        beziersb = curveb.split()
        for bez in beziersa:
            bez.clean()
        for bez in beziersb:
            bez.clean()
        pairs = set()
        for beziera in beziersa:
            for bezierb in beziersb:
                newpair = Intersection.bcurve_and_bcurve(beziera, bezierb)
                pairs |= set(newpair)
        pairs = tuple(pairs)
        pairs = Intersection.filter_pairs(pairs)
        pairs = Intersection.pairs_min_distance(pairs, curvea, curveb)
        return pairs
