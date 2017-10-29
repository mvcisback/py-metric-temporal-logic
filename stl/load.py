from traces import Domain, TimeSeries


def from_pandas(df, compact=True):
    '''TODO'''
    domain = Domain(df.index[0], df.index[-1])
    data = {col: TimeSeries(df[col].T, domain=domain) for col in df.columns}
    if compact:
        for val in data.values():
            val.compact()
    return data
