import pytest

from daxlab.data.fingerprint_contract import (
    V1_OHLC_CSV_SHA256,
    assert_known_fingerprint_method,
)


def test_v1_fingerprint_method_is_frozen() -> None:
    method = V1_OHLC_CSV_SHA256
    assert method.method_id == "DAXLAB_OHLC_CSV_SHA256_V1"
    assert method.columns == ("open", "high", "low", "close")
    assert method.index_encoding == "pandas_datetime_index_int64_nanoseconds"
    assert method.serialization == "pandas.to_csv(index=True,header=True)"
    assert method.float_format == "%.10f"
    assert method.text_encoding == "utf-8"
    assert method.digest == "sha256"


def test_unknown_fingerprint_method_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown fingerprint method"):
        assert_known_fingerprint_method("DAXLAB_OHLC_CSV_SHA256_V2")
