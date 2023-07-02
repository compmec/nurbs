import numpy as np
import pytest

from compmec.nurbs import GeneratorKnotVector, KnotVector


@pytest.mark.order(1)
@pytest.mark.dependency()
def test_begin():
    pass


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_begin"])
def test_Creation():
    """
    Tests if creates a knotvector correctly
    """
    KnotVector([0, 0, 1, 1])
    KnotVector([0, 0, 0, 1, 1, 1])
    KnotVector([0, 0, 0, 0, 1, 1, 1, 1])
    KnotVector([0, 0, 0, 0, 0.5, 1, 1, 1, 1])


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_Creation"])
def test_FailCreation():
    """
    Test some invalid creation cases, which should raise error
    """
    with pytest.raises(ValueError):
        KnotVector(-1)
    with pytest.raises(TypeError):
        KnotVector({1: 1})
    with pytest.raises(ValueError):
        KnotVector(["asd", {1.1: 1}])

    with pytest.raises(ValueError):
        KnotVector([0, 0, 0, 1, 1])
    with pytest.raises(ValueError):
        KnotVector([0, 0, 1, 1, 1])
    with pytest.raises(ValueError):
        KnotVector([0, 0, 0, 0, 1, 1, 1])
    with pytest.raises(ValueError):
        KnotVector([0, 0, 0, 1, 1, 1, 1])
    with pytest.raises(ValueError):
        KnotVector([0, 0, 0.7, 0.2, 1, 1])
    with pytest.raises(ValueError):
        KnotVector([[0, 0, 0.2, 0.7, 1, 1], [0, 0, 0.2, 0.7, 1, 1]])
    with pytest.raises(ValueError):
        KnotVector([[0, 0, 0.7, 0.2, 1, 1], [0, 0, 0.7, 0.2, 1, 1]])

    # Internal multiplicity error
    with pytest.raises(ValueError):
        KnotVector([0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1])
    with pytest.raises(ValueError):
        U = [0, 0, 0, 0.5, 0.5, 0.5, 0.5, 1, 1, 1]
        KnotVector(U)
    with pytest.raises(ValueError):
        U = [0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1]
        KnotVector(U)


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_Creation", "test_FailCreation"])
def test_ValuesDegree():
    V = KnotVector([0, 0, 1, 1])
    assert V.degree == 1
    V = KnotVector([0, 0, 0, 1, 1, 1])
    assert V.degree == 2
    V = KnotVector([0, 0, 0, 0, 1, 1, 1, 1])
    assert V.degree == 3

    V = KnotVector([0, 0, 0.5, 1, 1])
    assert V.degree == 1
    V = KnotVector([0, 0, 0.2, 0.6, 1, 1])
    assert V.degree == 1
    V = KnotVector([0, 0, 0, 0.5, 1, 1, 1])
    assert V.degree == 2
    V = KnotVector([0, 0, 0, 0.2, 0.6, 1, 1, 1])
    assert V.degree == 2
    V = KnotVector([0, 0, 0, 0, 0.5, 1, 1, 1, 1])
    assert V.degree == 3
    V = KnotVector([0, 0, 0, 0, 0.2, 0.6, 1, 1, 1, 1])
    assert V.degree == 3


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_Creation", "test_FailCreation"])
def test_ValuesNumberPoints():
    V = KnotVector([0, 0, 1, 1])
    assert V.npts == 2
    V = KnotVector([0, 0, 0, 1, 1, 1])
    assert V.npts == 3
    V = KnotVector([0, 0, 0, 0, 1, 1, 1, 1])
    assert V.npts == 4
    V = KnotVector([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    assert V.npts == 5

    V = KnotVector([0, 0, 0.5, 1, 1])
    assert V.npts == 3
    V = KnotVector([0, 0, 0.2, 0.6, 1, 1])
    assert V.npts == 4
    V = KnotVector([0, 0, 0, 0.5, 1, 1, 1])
    assert V.npts == 4
    V = KnotVector([0, 0, 0, 0.2, 0.6, 1, 1, 1])
    assert V.npts == 5
    V = KnotVector([0, 0, 0, 0, 0.5, 1, 1, 1, 1])
    assert V.npts == 5
    V = KnotVector([0, 0, 0, 0, 0.2, 0.6, 1, 1, 1, 1])
    assert V.npts == 6


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_ValuesDegree", "test_ValuesNumberPoints"])
def test_findspans_single():
    U = KnotVector([0, 0, 0.2, 0.4, 0.5, 0.6, 0.8, 1, 1])
    assert U.degree == 1
    assert U.npts == 7
    assert U.span(0) == 1
    assert U.span(0.1) == 1
    assert U.span(0.2) == 2
    assert U.span(0.3) == 2
    assert U.span(0.4) == 3
    assert U.span(0.5) == 4
    assert U.span(0.6) == 5
    assert U.span(0.7) == 5
    assert U.span(0.8) == 6
    assert U.span(0.9) == 6
    assert U.span(1.0) == 7

    with pytest.raises(ValueError):
        U.span(-0.1)
    with pytest.raises(ValueError):
        U.span(1.1)
    with pytest.raises(TypeError):
        U.span("asd")


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_ValuesDegree", "test_ValuesNumberPoints"])
def test_findmult_single():
    U = KnotVector([0, 0, 0.2, 0.4, 0.5, 0.6, 0.8, 1, 1])
    assert U.degree == 1
    assert U.npts == 7
    assert U.mult(0) == 2
    assert U.mult(0.1) == 0
    assert U.mult(0.2) == 1
    assert U.mult(0.3) == 0
    assert U.mult(0.4) == 1
    assert U.mult(0.5) == 1
    assert U.mult(0.6) == 1
    assert U.mult(0.7) == 0
    assert U.mult(0.8) == 1
    assert U.mult(0.9) == 0
    assert U.mult(1.0) == 2

    with pytest.raises(ValueError):
        U.mult(-0.1)
    with pytest.raises(ValueError):
        U.mult(1.1)
    with pytest.raises(TypeError):
        U.mult("asd")


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_findspans_single"])
def test_findspans_array():
    U = KnotVector([0, 0, 0.2, 0.4, 0.5, 0.6, 0.8, 1, 1])
    array = np.linspace(0, 1, 11)  # (0, 0.1, 0.2, ..., 0.9, 1.0)
    suposedspans = U.span(array)
    correctspans = [1, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7]
    assert U.degree == 1
    assert U.npts == 7
    np.testing.assert_equal(suposedspans, correctspans)


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_findmult_single"])
def test_findmult_array():
    U = KnotVector([0, 0, 0.2, 0.4, 0.5, 0.6, 0.8, 1, 1])
    array = np.linspace(0, 1, 11)  # (0, 0.1, 0.2, ..., 0.9, 1.0)
    suposedmults = U.mult(array)
    correctmults = [2, 0, 1, 0, 1, 1, 1, 0, 1, 0, 2]
    assert U.degree == 1
    assert U.npts == 7
    np.testing.assert_equal(suposedmults, correctmults)


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(depends=["test_ValuesDegree", "test_ValuesNumberPoints"])
def test_CompareKnotvector():
    U1 = KnotVector([0, 0, 1, 1])
    U2 = KnotVector([0, 0, 1, 1])
    assert U1 == U2
    assert U1 == [0, 0, 1, 1]

    U3 = KnotVector([0, 0, 0.5, 1, 1])
    assert U1 != U3

    assert U1 != 0
    assert U1 != "asad"


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_CompareKnotvector"])
def test_GeneratorBezier():
    Ugood = KnotVector([0, 0, 1, 1])
    assert Ugood.degree == 1
    assert Ugood.npts == 2
    Utest = GeneratorKnotVector.bezier(1)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood

    Ugood = KnotVector([0, 0, 0, 1, 1, 1])
    assert Ugood.degree == 2
    assert Ugood.npts == 3
    Utest = GeneratorKnotVector.bezier(2)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood

    Ugood = KnotVector([0, 0, 0, 0, 1, 1, 1, 1])
    assert Ugood.degree == 3
    assert Ugood.npts == 4
    Utest = GeneratorKnotVector.bezier(3)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(depends=["test_CompareKnotvector"])
def test_GeneratorUniform():
    Ugood = KnotVector([0, 0, 1, 1])
    assert Ugood.degree == 1
    assert Ugood.npts == 2
    Utest = GeneratorKnotVector.uniform(1, 2)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood

    Ugood = KnotVector([0, 0, 0.5, 1, 1])
    assert Ugood.degree == 1
    assert Ugood.npts == 3
    Utest = GeneratorKnotVector.uniform(1, 3)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood

    Ugood = KnotVector([0, 0, 0.25, 0.5, 0.75, 1, 1])
    assert Ugood.degree == 1
    assert Ugood.npts == 5
    Utest = GeneratorKnotVector.uniform(1, 5)
    assert isinstance(Utest, KnotVector)
    assert Utest == Ugood

    ntests = 100
    for i in range(ntests):
        degree = np.random.randint(1, 6)
        npts = np.random.randint(degree + 1, degree + 11)
        Utest = GeneratorKnotVector.uniform(degree, npts)
        assert isinstance(Utest, KnotVector)
        assert Utest.npts == npts
        assert Utest.degree == degree


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(depends=["test_CompareKnotvector"])
def test_GeneratorRandom():
    ntests = 1000
    for i in range(ntests):
        degree = np.random.randint(1, 6)
        npts = np.random.randint(degree + 1, degree + 11)
        knotvect = GeneratorKnotVector.random(degree, npts)
        assert isinstance(knotvect, KnotVector)
        assert knotvect.npts == npts
        assert knotvect.degree == degree


@pytest.mark.order(1)
@pytest.mark.timeout(2)
@pytest.mark.dependency(
    depends=[
        "test_GeneratorBezier",
        "test_GeneratorUniform",
        "test_GeneratorRandom",
        "test_CompareKnotvector",
    ]
)
def test_GeneratorKnotVectorFails():
    with pytest.raises(ValueError):
        GeneratorKnotVector.bezier(degree=-1)
    for degree in range(1, 6):
        with pytest.raises(ValueError):
            GeneratorKnotVector.uniform(degree, npts=degree)
        with pytest.raises(ValueError):
            GeneratorKnotVector.uniform(degree, npts=degree - 1)
        with pytest.raises(ValueError):
            GeneratorKnotVector.random(degree, npts=degree)
        with pytest.raises(ValueError):
            GeneratorKnotVector.random(degree, npts=degree - 1)

    with pytest.raises(TypeError):
        GeneratorKnotVector.bezier(degree="asd")
    with pytest.raises(TypeError):
        GeneratorKnotVector.bezier(degree={1: 1})
    with pytest.raises(TypeError):
        GeneratorKnotVector.uniform(degree=2, npts=3.0)
    with pytest.raises(TypeError):
        GeneratorKnotVector.uniform(degree=2.0, npts=3)
    with pytest.raises(TypeError):
        GeneratorKnotVector.uniform(degree=2, npts="3")
    with pytest.raises(TypeError):
        GeneratorKnotVector.uniform(degree="2", npts=3)
    with pytest.raises(TypeError):
        GeneratorKnotVector.random(degree=2, npts=3.0)
    with pytest.raises(TypeError):
        GeneratorKnotVector.random(degree=2.0, npts=3)


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(depends=["test_GeneratorUniform"])
def test_compare_knotvectors_fail():
    degree = np.random.randint(1, 6)
    npts = np.random.randint(degree + 3, degree + 11)
    U1 = GeneratorKnotVector.uniform(degree, npts)
    assert not (U1 == 1)
    assert U1 != 1
    assert U1 != "asd"
    assert U1 != [[0, 0, 0, 0.5, 1, 1, 1]]
    U2 = GeneratorKnotVector.uniform(degree + 1, npts + 1)
    U3 = GeneratorKnotVector.uniform(degree + 1, npts + 2)
    U4 = GeneratorKnotVector.uniform(degree, npts + 1)
    U5 = GeneratorKnotVector.random(degree, npts)
    assert U1 != U2
    assert U1 != U3
    assert U1 != U4
    assert U1 != U5
    assert U2 != U3
    assert U2 != U4
    assert U2 != U5
    assert U3 != U4
    assert U3 != U5
    assert U4 != U5


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(depends=["test_GeneratorUniform"])
def test_insert_knot_remove():
    Uinc0 = [0, 0, 0, 0, 1, 1, 1, 1]
    Uinc1 = [0, 0, 0, 0, 0.5, 1, 1, 1, 1]
    Uinc2 = [0, 0, 0, 0, 0.5, 0.5, 1, 1, 1, 1]
    Uinc3 = [0, 0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1, 1]
    Uinc4 = [0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1]
    Uinc5 = [0, 0, 0, 0, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1]

    U0 = KnotVector(Uinc0)
    U1 = KnotVector(Uinc1)
    U2 = KnotVector(Uinc2)
    U3 = KnotVector(Uinc3)
    with pytest.raises(ValueError):
        KnotVector(Uinc4)
    with pytest.raises(ValueError):
        KnotVector(Uinc5)

    Uo = KnotVector(Uinc0)
    assert Uo == U0
    Uo.knot_insert(0.5)
    assert Uo == U1
    Uo.knot_insert(0.5)
    assert Uo == U2
    Uo.knot_insert(0.5)
    assert Uo == U3

    Uo = KnotVector(Uinc0)
    Uo.knot_insert(0.5, 2)
    assert Uo == U2

    Uo = KnotVector(Uinc0)
    Uo.knot_insert(0.5, 3)
    assert Uo == U3

    Uo = KnotVector(Uinc3)
    Uo.knot_remove(0.5)
    assert Uo == U2
    Uo.knot_remove(0.5)
    assert Uo == U1
    Uo.knot_remove(0.5)
    assert Uo == U0
    with pytest.raises(ValueError):
        Uo.knot_remove(0.5)

    Uo = KnotVector(Uinc3)
    Uo.knot_remove(0.5, 2)
    assert Uo == U1

    Uo = KnotVector(Uinc3)
    Uo.knot_remove(0.5, 3)
    assert Uo == U0

    Uo = KnotVector(Uinc3)
    with pytest.raises(TypeError):
        U0.knot_remove("asd")
    with pytest.raises(TypeError):
        U0.knot_remove(0.5, "ads")
    with pytest.raises(ValueError):
        U0.knot_remove(0.5, 0)
    with pytest.raises(ValueError):
        U0.knot_remove(0.5, -1)
    with pytest.raises(ValueError):
        U0.knot_remove(-0.5)


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(
    depends=[
        "test_begin",
    ]
)
def test_others():
    knotvect = [0, 0.2, 0.4, 0.4, 0.8, 1]
    with pytest.raises(ValueError):
        KnotVector(knotvect)
    knotvect = [0, 0, 0.5, 1, 1]
    knotvect = KnotVector(knotvect)
    knotvect = KnotVector(knotvect)


@pytest.mark.order(1)
@pytest.mark.timeout(4)
@pytest.mark.dependency(
    depends=[
        "test_begin",
        "test_findspans_array",
        "test_findmult_array",
        "test_GeneratorBezier",
        "test_GeneratorUniform",
        "test_GeneratorRandom",
        "test_GeneratorKnotVectorFails",
        "test_compare_knotvectors_fail",
        "test_insert_knot_remove",
        "test_others",
    ]
)
def test_end():
    pass
