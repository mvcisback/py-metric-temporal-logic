import typing

import stl.ast as ast

ML = typing.Union[ast.AtomicPred, ast.NaryOpSTL, ast.Neg]
SL = typing.Union[ast.LinEq, ML]

STL = typing.Union[SL, ast.ModalOp]
MTL = typing.Union[ML, ast.ModalOp]

PSTL = typing.NewType("PSTL", STL)
STL_Generator = typing.Generator[STL, None, STL]
