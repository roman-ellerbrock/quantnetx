# Data Sources and Attribution

This document lists all data sources used in QuantNetX and provides proper attribution as required by data providers.

## Market Data Sources

### Palladium Historical Prices

**Source:** www.macrotrends.net
**File:** `data/palladium-prices-historical-chart-data.csv`
**Date Range:** 1977-01-05 to 2025-10-13
**Data Points:** 12,258

**Attribution Requirements:**
- Data source must be indicated as "www.macrotrends.net"
- If displayed on a web page, a "dofollow" backlink to the originating page is required

**Disclaimer:**
Historical data is provided "AS IS" and solely for informational purposes - not for trading purposes or advice. Neither Macrotrends LLC nor any of our information providers will be liable for any damages relating to your use of the data provided.

**Processing:**
Raw data from Macrotrends is processed using `process_palladium_macrotrends.py` and merged with existing palladium data using `merge_palladium_data.py`. The merged dataset contains 12,365 data points from 1977-01-05 to 2025-10-17.

---

## Other Data Sources

- Bitcoin, S&P 500, NASDAQ, and other market data: [To be documented]
- CPI Data: Federal Reserve Economic Data (FRED)

---

*Last Updated: 2025-10-19*
