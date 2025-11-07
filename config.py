# ESG Metric Weights Configuration
# These weights must sum to 1.0 for proper scoring

METRIC_WEIGHTS = {
    'MSCI_ESG_Environmental_Score': 0.20,
    'ESG_Score_Environmental_Weight_%': 0.15,
    'Fund_WACI': 0.20,
    'Financed_Carbon_Emissions': 0.10,
    'Fossil_Fuel_Reserves_%': 0.15,
    'MSCI_ESG_Score': 0.05,
    'Fund_ESG_Leaders_%': 0.05,
    'MSCI_Fund_ESG_Trend_Positive_%': 0.05,
    'Fund_ESG_Laggard_%': 0.03,
    'Controversial_Weapons_%': 0.01,
    'MSCI_ESG_Governance_Score': 0.01,
}

# Qualification Thresholds
# Funds ranked by percentile within Morningstar Category
PERCENTILE_THRESHOLDS = {
    'elite': 25,              # Top quartile - auto-qualify for core
    'qualified': 37,          # Extended top tier
    'watchlist': 74,          # Median - monitor closely
    'review': 110,            # Below median - replace if core holding
}

# YCharts Column Name Mapping (adjust based on your exports)
COLUMN_MAPPING = {
    'Symbol': 'Ticker',
    'Fund Name': 'Name',
    'Morningstar Category': 'Category',
}
