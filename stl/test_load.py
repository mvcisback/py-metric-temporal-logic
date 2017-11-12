import pandas as pd

from stl.load import from_pandas

DATA = pd.DataFrame(
    data={
        'AP1': [True, False, True],
        'x': [0, 0, 0.1],
        'y': [-1, -1, 0],
        'z': [2, 3, 1],
    },
    index=[0, 1, 2],
)


def test_from_pandas():
    x = from_pandas(DATA)
    assert x['x'][0] == 0
    assert x['x'][0.2] == 0
    assert not x['AP1'][1.4]
