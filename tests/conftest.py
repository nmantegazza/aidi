import pandas as pd

# Monkey-patch Series.append which was removed in pandas 2.0+ but is used by recordlinkage
if not hasattr(pd.Series, "append"):
    def _append(self, to_append, ignore_index=False, verify_integrity=False):
        return pd.concat([self, to_append], ignore_index=ignore_index, verify_integrity=verify_integrity)
    pd.Series.append = _append
