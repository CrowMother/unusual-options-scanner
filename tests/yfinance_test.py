import unittest
from unittest.mock import patch
import yfinance
from yahoo_fin import stock_info as si


from modules import yfinance


def test_get_batch_symbols(self, mock_yfinance_download):
        # Mock the yfinance download function to return a DataFrame
        import pandas as pd
        mock_df = pd.DataFrame({
            "AAPL": [150, 151],
            "MSFT": [300, 301]
        }, index=["2024-06-01 09:00:00", "2024-06-01 09:01:00"])
        
        # Mock return value
        mock_yfinance_download.return_value = mock_df

        # Call the function
        symbols = ["AAPL", "MSFT"]
        result = yfinance.get_batch_symbols(symbols)

        # Assertions
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue("AAPL" in result.columns)
        self.assertTrue("MSFT" in result.columns)
        self.assertEqual(result.iloc[0]["AAPL"], 150)
        self.assertEqual(result.iloc[1]["MSFT"], 301)

if __name__ == '__main__':
    unittest.main()