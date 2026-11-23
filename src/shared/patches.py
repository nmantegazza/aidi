"""
Runtime monkeypatches for 3rd-party dependency compatibility fixes.
"""

def apply_jellyfish_patch() -> None:
    """
    Patch jellyfish.jaro_winkler to delegate directly to jaro_winkler_similarity,
    preventing recordlinkage string comparisons from triggering thousands of DeprecationWarnings.
    """
    try:
        import jellyfish
        if hasattr(jellyfish, "jaro_winkler_similarity"):
            jellyfish.jaro_winkler = jellyfish.jaro_winkler_similarity
    except ImportError:
        pass


apply_jellyfish_patch()


def apply_recordlinkage_date_patch() -> None:
    """
    Patch recordlinkage.compare.Date._compute_vectorized to initialize float64 arrays,
    preventing Pandas 2.1+ FutureWarning when setting float swap values into int64 arrays.
    """
    try:
        import numpy as np
        import pandas as pd
        import recordlinkage.compare as rlc

        def patched_compute_vectorized(self, s_left, s_right):
            if str(s_left.dtype) != 'datetime64[ns]':
                raise ValueError('Left column is not of type datetime64[ns]')
            if str(s_right.dtype) != 'datetime64[ns]':
                raise ValueError('Right column is not of type datetime64[ns]')

            c = (s_left == s_right).astype(np.float64)

            if self.swap_month_day and self.swap_month_day != 0:
                c[(s_left.dt.year == s_right.dt.year) &
                  (s_left.dt.month == s_right.dt.day) &
                  (s_left.dt.day == s_right.dt.month) &
                  (c != 1)] = self.swap_month_day

            if self.swap_months and self.swap_months != 0:
                if self.swap_months == 'default':
                    self.swap_months = [(6, 7, 0.5), (7, 6, 0.5),
                                        (9, 10, 0.5), (10, 9, 0.5)]
                else:
                    try:
                        if not all(len(x) == 3 for x in self.swap_months):
                            raise Exception
                    except Exception:
                        raise ValueError(
                            'swap_months must be a list of (first month, '
                            'second month, value) tuples or lists.'
                        )

                for month1, month2, value in self.swap_months:
                    c[(s_left.dt.year == s_right.dt.year) &
                      (s_left.dt.month == month1) &
                      (s_right.dt.month == month2) &
                      (s_left.dt.day == s_right.dt.day) &
                      (c != 1)] = value

            c = pd.Series(c)
            c[s_left.isnull() | s_right.isnull()] = self.missing_value
            return c

        rlc.Date._compute_vectorized = patched_compute_vectorized
    except ImportError:
        pass


apply_jellyfish_patch()
apply_recordlinkage_date_patch()

