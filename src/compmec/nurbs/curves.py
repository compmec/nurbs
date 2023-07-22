from __future__ import annotations

from typing import Optional, Tuple, Union

import numpy as np

from compmec.nurbs import heavy
from compmec.nurbs.__classes__ import Intface_BaseCurve
from compmec.nurbs.functions import Function
from compmec.nurbs.knotspace import KnotVector


class BaseCurve(Intface_BaseCurve):
    def __init__(self, knotvector: KnotVector):
        self.__ctrlpoints = None
        self.__weights = None
        self.__knotvector = KnotVector(knotvector)

    def __call__(self, nodes: np.ndarray) -> np.ndarray:
        return self.eval(nodes)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if self.knotvector[0] != other.knotvector[0]:
            return False
        if self.knotvector[-1] != other.knotvector[-1]:
            return False
        newknotvec = self.knotvector | other.knotvector
        selfcopy = self.deepcopy()
        selfcopy.knotvector = newknotvec
        othercopy = other.deepcopy()
        othercopy.knotvector = newknotvec
        for poi, qoi in zip(self.ctrlpoints, othercopy.ctrlpoints):
            if np.linalg.norm(poi - qoi) > 1e-9:
                return False
        return True

    def __ne__(self, obj: object):
        return not self.__eq__(obj)

    def __neg__(self):
        newcurve = self.deepcopy()
        newctrlpoints = [-1 * ctrlpt for ctrlpt in newcurve.ctrlpoints]
        newcurve.ctrlpoints = newctrlpoints
        return newcurve

    def __add__(self, obj: object):
        if type(self) != type(obj):
            error_msg = f"Cannot sum a {type(obj)} object with"
            error_msg += f" a {self.__class__} object"
            raise TypeError(error_msg)
        if self.knotvector != obj.knotvector:
            raise ValueError("The knotvectors of curves are not the same!")
        newP = [poi + qoi for poi, qoi in zip(self.ctrlpoints, obj.ctrlpoints)]

        return self.__class__(self.knotvector, newP)

    def __sub__(self, obj: object):
        return self + (-obj)

    def __or__(self, other: object):
        umaxleft = self.knotvector[-1]
        uminright = other.knotvector[0]
        if umaxleft != uminright:
            error_msg = f"max(Uleft) = {umaxleft} != {uminright} = min(Uright)"
            raise ValueError(error_msg)
        pointleft = self.ctrlpoints[-1]
        pointright = other.ctrlpoints[0]
        if np.sum((pointleft - pointright) ** 2) > 1e-9:
            error_msg = "Points are not coincident.\n"
            error_msg += f"  Point left = {pointleft}\n"
            error_msg += f" Point right = {pointright}"
            raise ValueError(error_msg)
        othercopy = other.deepcopy()
        selfcopy = self.deepcopy()
        maxdegree = max(self.degree, other.degree)
        selfcopy.degree = maxdegree
        othercopy.degree = maxdegree
        npts0 = selfcopy.npts
        npts1 = othercopy.npts
        newknotvector = [0] * (maxdegree + npts0 + npts1)
        newknotvector[:npts0] = selfcopy.knotvector[:npts0]
        newknotvector[npts0:] = othercopy.knotvector[1:]
        newknotvector = KnotVector(newknotvector)
        newctrlpoints = [0] * (npts0 + npts1 - 1)
        newctrlpoints[:npts0] = selfcopy.ctrlpoints[:npts0]
        newctrlpoints[npts0:] = othercopy.ctrlpoints[1:]
        return self.__class__(newknotvector, newctrlpoints)

    @property
    def knotvector(self):
        return self.__knotvector

    @property
    def degree(self):
        return self.knotvector.degree

    @property
    def npts(self):
        return self.knotvector.npts

    @property
    def knots(self):
        return self.knotvector.knots

    @property
    def weights(self):
        return self.__weights

    @property
    def ctrlpoints(self):
        return self.__ctrlpoints

    @knotvector.setter
    def knotvector(self, value: KnotVector):
        self.update_knotvector(value)

    @degree.setter
    def degree(self, value: int):
        newknotvector = self.knotvector.deepcopy()
        newknotvector.degree = int(value)
        self.knotvector = newknotvector

    @weights.setter
    def weights(self, value: Tuple[float]):
        if value is None:
            self.__weights = None
            return
        array = np.array(value, dtype="float64")
        if array.shape != (self.npts,):
            error_msg = "Weights must be a 1D array with "
            error_msg += f"{self.npts} points"
            raise ValueError(error_msg)
        self.__weights = tuple(value)

    @ctrlpoints.setter
    def ctrlpoints(self, newpoints: np.ndarray):
        if newpoints is None:
            self.__ctrlpoints = None
            return
        if isinstance(newpoints, str):
            raise TypeError
        try:
            iter(newpoints)
        except Exception:
            raise TypeError
        for point in newpoints:  # Verify if operations are valid for each node
            for knot in self.knotvector.knots:
                knot * point
            for otherpoint in newpoints:
                point + otherpoint  # Verify if we can sum every point, same type

        if len(newpoints) != self.npts:
            error_msg = f"The number of control points ({len(newpoints)}) must be "
            error_msg += f"the same as npts of KnotVector ({self.knotvector.npts})\n"
            error_msg += f"  knotvector.npts = {self.npts}"
            error_msg += f"  len(ctrlpoints) = {len(newpoints)}"
            raise ValueError(error_msg)
        
        self.__ctrlpoints = tuple(newpoints)

    def deepcopy(self) -> Curve:
        curve = self.__class__(self.knotvector)
        curve.ctrlpoints = self.ctrlpoints
        curve.weights = self.weights
        return curve

    def update_knotvector(self, newvector: KnotVector, tolerance: float = 1e-9):
        newvector = KnotVector(newvector)
        if newvector == self.knotvector:
            return
        if self.ctrlpoints is None:
            return self.set_knotvector(newvector)
        oldvec, newvec = tuple(self.knotvector), tuple(newvector)
        T, E = heavy.LeastSquare.spline2spline(oldvec, newvec)
        error = np.moveaxis(self.ctrlpoints, 0, -1) @ E @ self.ctrlpoints
        error = np.max(np.abs(error))
        if tolerance and error > tolerance:
            error_msg = "Cannot update knotvector cause error is "
            error_msg += f" {error} > {tolerance}"
            raise ValueError(error_msg)
        self.set_knotvector(newvec)
        self.apply_lineartrans(T)

    def apply_lineartrans(self, matrix: np.ndarray):
        """ """
        if matrix is None:
            raise ValueError
        matrix = np.array(matrix)
        if self.weights is None:
            self.ctrlpoints = matrix @ self.ctrlpoints
            return
        oldweights = self.weights
        self.weights = matrix @ oldweights

        if self.ctrlpoints is not None:
            oldctrlpoints = [point for point in self.ctrlpoints]
            for i, weight in enumerate(oldweights):
                oldctrlpoints[i] *= weight
            newctrlpoints = []
            for i, line in enumerate(matrix):
                newctrlpoints.append(0 * self.ctrlpoints[0])
                for j, point in enumerate(oldctrlpoints):
                    newpoint = line[j] * point
                    newpoint /= self.weights[i]
                    newctrlpoints[i] += newpoint
            self.ctrlpoints = newctrlpoints

    def set_knotvector(self, newknotvector: KnotVector):
        self.__knotvector = KnotVector(newknotvector)


class Curve(BaseCurve):
    def __init__(
        self,
        knotvector: KnotVector,
        ctrlpoints: Optional[np.ndarray] = None,
        weights: Optional[np.ndarray] = None,
    ):
        super().__init__(knotvector)
        self.ctrlpoints = ctrlpoints
        self.weights = weights

    def __str__(self) -> str:
        if self.npts == self.degree + 1:
            msg = "Bezier"
        elif self.weights is None:
            msg = "Spline"
        else:
            msg = "Rational Spline"
        msg += f" curve of degree {self.degree}"
        msg += f" and {self.npts} control points\n"
        msg += f"KnotVector = {self.knotvector}\n"
        if self.ctrlpoints is None:
            return msg
        msg += "ControlPoints = [\n"
        for point in self.ctrlpoints:
            msg += str(point) + "\n"
        msg += "]\n"
        return msg

    def eval(self, nodes: np.ndarray) -> np.ndarray:
        if self.ctrlpoints is None:
            error_msg = "Cannot evaluate: There are no control points"
            raise ValueError(error_msg)
        tempfunction = Function(self.knotvector)
        tempfunction.weights = self.weights
        matrix = tempfunction(nodes)
        return np.moveaxis(matrix, 0, -1) @ self.ctrlpoints

    def knot_insert(self, nodes: Tuple[float]) -> None:
        nodes = tuple(nodes)
        oldvector = tuple(self.knotvector)
        newvector = tuple(self.knotvector + tuple(nodes))
        matrix = heavy.Operations.knot_insert(oldvector, nodes)
        self.set_knotvector(newvector)
        self.apply_lineartrans(matrix)

    def knot_remove(self, nodes: Tuple[float], tolerance: float = 1e-9) -> None:
        nodes = tuple(nodes)
        newknotvec = self.knotvector.deepcopy() - tuple(nodes)
        self.update_knotvector(newknotvec, tolerance)

    def knot_clean(
        self, nodes: Optional[Tuple[float]] = None, tolerance: float = 1e-9
    ) -> None:
        """
        Remove all unnecessary knots.
        If no nodes are given, it tries to remove all internal knots
        Nothing happens if removing error by removing certain knot is
        bigger than the tolerance.
        """
        if nodes is None:
            nodes = self.knotvector.knots
        nodes = tuple(set(nodes) - set(self.knotvector.limits))
        for knot in nodes:
            try:
                while True:
                    self.knot_remove((knot,), tolerance)
            except ValueError:
                pass

    def degree_increase(self, times: Optional[int] = 1):
        """
        The same as mycurve.degree += times
        """
        oldvector = tuple(self.knotvector)
        matrix = heavy.Operations.degree_increase(oldvector, times)
        nodes = self.knotvector.knots
        newnodes = times * nodes
        newvector = heavy.KnotVector.insert_knots(oldvector, newnodes)
        self.set_knotvector(newvector)
        self.apply_lineartrans(matrix)

    def clean(self, tolerance: float = 1e-9):
        self.degree_clean(tolerance=tolerance)
        self.knot_clean(tolerance=tolerance)
        if self.weights is None:
            return
        # Try to reduce to spline
        knotvector = tuple(self.knotvector)
        weights = tuple(self.weights)
        ctrlpoints = tuple(self.ctrlpoints)
        T, E = heavy.LeastSquare.func2func(
            knotvector, weights, knotvector, [1] * self.npts
        )
        error = ctrlpoints @ E @ ctrlpoints
        if error < tolerance:
            self.ctrlpoints = T @ ctrlpoints
            self.weights = None
            self.clean(tolerance)

    def degree_decrease(
        self, times: Optional[int] = 1, tolerance: Optional[float] = 1e-9
    ):
        """
        The same as mycurve.degree -= 1
        But this function forces the degree reductions without looking the error
        """
        newknotvec = self.knotvector.deepcopy()
        newknotvec.degree -= times
        self.update_knotvector(newknotvec, tolerance)

    def degree_clean(self, tolerance: float = 1e-9):
        """
        Reduces au maximum the degree of the curve received the tolerance.
        If the reduced degree error is bigger than the tolerance, nothing happens
        """
        try:
            while True:
                self.degree_decrease(1, tolerance)
        except ValueError:
            pass

    def split(self, nodes: Optional[Tuple[float]] = None) -> Tuple[Curve]:
        """
        Separate the current spline at specified knots
        If no arguments are given, it splits at every knot and
            returns a list of bezier curves
        """
        vector = tuple(self.knotvector)
        if nodes is None:
            nodes = self.knotvector.knots
        nodes = tuple(nodes)
        matrices = heavy.Operations.split_curve(vector, nodes)
        newvectors = heavy.KnotVector.split(vector, nodes)
        newcurves = []
        for newvector, matrix in zip(newvectors, matrices):
            matrix = np.array(matrix)
            newcurve = Curve(newvector)
            newcurve.ctrlpoints = matrix @ self.ctrlpoints
            if self.weights is not None:
                newcurve.weights = matrix @ self.weights
            newcurves.append(newcurve)
        return tuple(newcurves)
