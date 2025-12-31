"""Tests for TushareClient."""

from unittest.mock import MagicMock, patch

import pytest

from stock_data.tushare_api import TushareClient, TushareError


class TestTushareClientInit:
    """Tests for TushareClient initialization."""

    def test_missing_token_raises_error(self, monkeypatch):
        """Should raise TushareError when token is not provided."""
        monkeypatch.delenv("TUSHARE_TOKEN", raising=False)

        with pytest.raises(TushareError, match="未找到 Token"):
            with patch("stock_data.tushare_api.ts.pro_api"):
                TushareClient()

    def test_accepts_explicit_token(self, monkeypatch):
        """Should accept token passed as argument."""
        monkeypatch.delenv("TUSHARE_TOKEN", raising=False)

        with patch("stock_data.tushare_api.ts.pro_api") as mock_pro_api:
            client = TushareClient(token="explicit_token")

            mock_pro_api.assert_called_once_with(token="explicit_token", timeout=30)
            assert client._token == "explicit_token"

    def test_uses_env_token(self, monkeypatch):
        """Should use TUSHARE_TOKEN from environment."""
        monkeypatch.setenv("TUSHARE_TOKEN", "env_token")

        with patch("stock_data.tushare_api.ts.pro_api") as mock_pro_api:
            client = TushareClient()

            mock_pro_api.assert_called_once_with(token="env_token", timeout=30)
            assert client._token == "env_token"

    def test_custom_timeout(self, monkeypatch):
        """Should pass custom timeout to pro_api."""
        monkeypatch.setenv("TUSHARE_TOKEN", "test_token")

        with patch("stock_data.tushare_api.ts.pro_api") as mock_pro_api:
            TushareClient(timeout=60)

            mock_pro_api.assert_called_once_with(token="test_token", timeout=60)


class TestDaily:
    """Tests for TushareClient.daily method."""

    def test_returns_pydantic_model(self, monkeypatch):
        """Should return TushareDailyResult with items."""
        monkeypatch.setenv("TUSHARE_TOKEN", "test_token")

        mock_df = MagicMock()
        mock_df.to_dict.return_value = [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20241008",
                "open": 10.0,
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "pre_close": 10.0,
                "change": 0.5,
                "pct_chg": 5.0,
                "vol": 100000.0,
                "amount": 1050000.0,
            }
        ]

        mock_pro = MagicMock()
        mock_pro.daily.return_value = mock_df

        with patch("stock_data.tushare_api.ts.pro_api", return_value=mock_pro):
            client = TushareClient()
            result = client.daily(ts_code="000001.SZ", trade_date="20241008")

        assert result.trade_date == "20241008"
        assert result.ts_code == "000001.SZ"
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].ts_code == "000001.SZ"
        assert result.items[0].close == 10.5
        mock_pro.daily.assert_called_once_with(ts_code="000001.SZ", trade_date="20241008")

    def test_returns_empty_result_when_no_data(self, monkeypatch):
        """Should return empty TushareDailyResult when tushare returns None."""
        monkeypatch.setenv("TUSHARE_TOKEN", "test_token")

        mock_pro = MagicMock()
        mock_pro.daily.return_value = None

        with patch("stock_data.tushare_api.ts.pro_api", return_value=mock_pro):
            client = TushareClient()
            result = client.daily(trade_date="20241008")

        assert result.total == 0
        assert result.items == []

    def test_wraps_api_exception(self, monkeypatch):
        """Should wrap tushare exceptions in TushareError."""
        monkeypatch.setenv("TUSHARE_TOKEN", "test_token")

        mock_pro = MagicMock()
        mock_pro.daily.side_effect = Exception("API limit exceeded")

        with patch("stock_data.tushare_api.ts.pro_api", return_value=mock_pro):
            client = TushareClient()
            with pytest.raises(TushareError, match="获取日线失败"):
                client.daily(ts_code="000001.SZ")
