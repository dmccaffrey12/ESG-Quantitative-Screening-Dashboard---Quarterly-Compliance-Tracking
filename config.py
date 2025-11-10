"""
ESG Quantitative Screening Configuration
Defines metric weights and qualification thresholds
"""

# ESG Metric Weights (must sum to 1.0)
METRIC_WEIGHTS = {
    # Environmental Metrics (70% total weight)
    'MSCI ESG Environmental Score': 0.20,
    'ESG Score Environmental Weight (%)': 0.15,
    'Fund Weighted Average Carbon Intensity': 0.20,
    'Financed Carbon Emissions (Carbon Emissions / USD Million Invested)': 0.10,
    'Fossil Fuels Reserve (%)': 0.15,
    
    # ESG Quality & Governance Metrics (30% total weight)
    'MSCI ESG Score': 0.05,
    'Fund ESG Leaders (%)': 0.05,
    'MSCI Fund ESG Trend Positive (%)': 0.05,
    'Fund ESG Laggards (%)': 0.03,
    'Controversial Weapons Involvement (%)': 0.01,
    'MSCI ESG Governance Score': 0.01,
}

# Percentile Thresholds (Category-Relative)
# Philosophy: "Elite or Replace" - Only hold top quartile ESG funds
PERCENTILE_THRESHOLDS = {
    'elite': 25,        # <= 25th percentile: Automatic qualification (Top Quartile)
    'review': 50,       # 26-50th percentile: Needs justification, consider replacement
    'replace': 100,     # > 50th percentile: Bottom half, replace at next rebalance
}

# Threshold Descriptions (for documentation)
THRESHOLD_DESCRIPTIONS = {
    'elite': 'Top Quartile - Automatic qualification. Best-in-class ESG performance.',
    'review': 'Second Quartile - Requires IC justification. Consider replacement with Elite alternative.',
    'replace': 'Bottom Half - Replace at next rebalancing. Insufficient ESG quality.',
}