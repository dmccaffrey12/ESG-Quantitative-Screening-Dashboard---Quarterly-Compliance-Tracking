from fpdf import FPDF
import pandas as pd
from datetime import datetime

class ESGComplianceReport(FPDF):
    """Enhanced PDF class for ESG screening reports"""
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ESG Quantitative Screening Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        """Add a chapter title with formatting"""
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
    
    def section_title(self, title):
        """Add a section title"""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

def clean_status_for_pdf(status):
    """Remove Unicode characters that fpdf can't handle"""
    if not isinstance(status, str):
        return str(status)
    
    status = status.replace('✅', '').replace('⚠️', '').replace('❌', '').strip()
    
    if 'Elite' in status:
        return 'Elite'
    elif 'Review' in status:
        return 'Review'
    elif 'Replace' in status:
        return 'Replace'
    else:
        return status

def generate_compliance_report(category_df, category_name, quarter, portfolio_df=None):
    """
    Generate enhanced PDF compliance report with portfolio holdings analysis
    
    Args:
        category_df: DataFrame with fund data for the category
        category_name: String name of Morningstar category
        quarter: String like '2025Q4'
        portfolio_df: Optional DataFrame with current portfolio holdings
    
    Returns:
        PDF bytes for download
    """
    
    pdf = ESGComplianceReport()
    pdf.add_page()
    
    # ========== PAGE 1: Executive Summary ==========
    pdf.set_font('Arial', 'B', 14)
    clean_category = category_name.replace('/', '-')
    pdf.cell(0, 10, f'Category: {clean_category}', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Quarter: {quarter}', 0, 1)
    pdf.cell(0, 10, f'Report Date: {datetime.now().strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(10)
    
    # Summary statistics
    pdf.section_title('Summary Statistics')
    pdf.set_font('Arial', '', 10)
    
    total = len(category_df)
    elite = 0
    review = 0
    replace = 0
    
    if 'Status' in category_df.columns:
        for status in category_df['Status']:
            clean = clean_status_for_pdf(str(status))
            if 'Elite' in clean:
                elite += 1
            elif 'Review' in clean:
                review += 1
            elif 'Replace' in clean:
                replace += 1
    
    pdf.cell(0, 8, f'Total Funds Analyzed: {total}', 0, 1)
    if total > 0:
        pdf.cell(0, 8, f'Elite Funds (<=25th %ile): {elite} ({elite/total*100:.1f}%)', 0, 1)
        pdf.cell(0, 8, f'Review Funds (26-50th %ile): {review} ({review/total*100:.1f}%)', 0, 1)
        pdf.cell(0, 8, f'Replace Funds (>50th %ile): {replace} ({replace/total*100:.1f}%)', 0, 1)
    pdf.ln(10)
    
    # ========== Current Holdings in This Category ==========
    if portfolio_df is not None:
        pdf.section_title('Current Portfolio Holdings in This Category')
        pdf.set_font('Arial', '', 9)
        
        # Find holding column
        holding_col = None
        for col in portfolio_df.columns:
            if 'holding' in str(col).lower():
                holding_col = col
                break
        
        if holding_col:
            current_tickers = portfolio_df[holding_col].dropna().unique()
            holdings_in_category = category_df[category_df['Symbol'].isin(current_tickers)]
            
            if len(holdings_in_category) > 0:
                pdf.cell(0, 6, f'You currently hold {len(holdings_in_category)} funds in this category:', 0, 1)
                pdf.ln(3)
                
                # Table header
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(25, 8, 'Ticker', 1)
                pdf.cell(70, 8, 'Fund Name', 1)
                pdf.cell(25, 8, 'Percentile', 1)
                pdf.cell(30, 8, 'Status', 1)
                pdf.cell(30, 8, 'Action', 1)
                pdf.ln()
                
                # Holdings data
                pdf.set_font('Arial', '', 8)
                for _, row in holdings_in_category.iterrows():
                    ticker = str(row.get('Symbol', 'N/A'))[:10]
                    fund_name = str(row.get('Name', 'N/A'))[:30]
                    percentile = row.get('FI ESG Quant Percentile Screen', 0)
                    status = clean_status_for_pdf(str(row.get('Status', '')))
                    
                    # Determine action based on new Elite or Replace philosophy
                    if percentile <= 25:
                        action = 'Keep (Elite)'
                    elif percentile <= 50:
                        action = 'Justify or Replace'
                    else:
                        action = 'Replace'
                    
                    pdf.cell(25, 8, ticker, 1)
                    pdf.cell(70, 8, fund_name, 1)
                    pdf.cell(25, 8, f"{percentile:.1f}", 1)
                    pdf.cell(30, 8, status[:15], 1)
                    pdf.cell(30, 8, action[:20], 1)
                    pdf.ln()
                
                pdf.ln(5)
            else:
                pdf.cell(0, 6, 'No current holdings identified in this category.', 0, 1)
                pdf.ln(5)
    
    # ========== Top 10 Universe Funds ==========
    pdf.section_title('Top 10 Available Funds in Universe')
    pdf.set_font('Arial', '', 9)
    
    # Mark which are current holdings
    if portfolio_df is not None and holding_col:
        current_tickers = portfolio_df[holding_col].dropna().unique()
    else:
        current_tickers = []
    
    # Table header
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(8, 8, '#', 1)
    pdf.cell(25, 8, 'Ticker', 1)
    pdf.cell(65, 8, 'Fund Name', 1)
    pdf.cell(25, 8, 'Percentile', 1)
    pdf.cell(30, 8, 'Status', 1)
    pdf.cell(27, 8, 'In Portfolio?', 1)
    pdf.ln()
    
    # Top 10 funds
    pdf.set_font('Arial', '', 8)
    for idx, (_, row) in enumerate(category_df.head(10).iterrows(), 1):
        ticker = str(row.get('Symbol', 'N/A'))[:10]
        fund_name = str(row.get('Name', 'N/A'))[:28]
        percentile = row.get('FI ESG Quant Percentile Screen', 0)
        status = clean_status_for_pdf(str(row.get('Status', '')))
        in_portfolio = 'YES' if ticker in current_tickers else 'No'
        
        pdf.cell(8, 8, str(idx), 1)
        pdf.cell(25, 8, ticker, 1)
        pdf.cell(65, 8, fund_name, 1)
        pdf.cell(25, 8, f"{percentile:.1f}", 1)
        pdf.cell(30, 8, status[:15], 1)
        pdf.cell(27, 8, in_portfolio, 1)
        pdf.ln()
    
    # ========== PAGE 2: Methodology ==========
    pdf.add_page()
    pdf.chapter_title('Screening Methodology')
    
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 6, 
        'This report documents our quarterly ESG screening using an 11-metric quantitative framework. '
        'Funds are ranked within their Morningstar Category using category-relative percentile ranking. '
        'This ensures fair comparison within peer groups (utilities vs. utilities, not utilities vs. tech).'
    )
    pdf.ln(5)
    
    pdf.section_title('Elite or Replace Philosophy')
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 6,
        'Our ESG screening adopts a strict "Elite or Replace" standard. In well-populated categories, '
        'there are typically 20-50 Elite funds available. With sufficient options in the top quartile, '
        'holding anything below the 25th percentile requires extraordinary justification.'
    )
    pdf.ln(5)
    
    pdf.section_title('Qualification Thresholds')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 6, 'Elite: <= 25th percentile (Top Quartile - Automatic qualification)', 0, 1)
    pdf.cell(0, 6, 'Review: 26-50th percentile (Requires IC justification)', 0, 1)
    pdf.cell(0, 6, 'Replace: > 50th percentile (Replace at next rebalancing)', 0, 1)
    pdf.ln(8)
    
    # ========== PAGE 3: ESG Metrics Detail ==========
    pdf.add_page()
    pdf.chapter_title('ESG Metrics Framework')
    
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 6,
        'Our screening framework evaluates 11 ESG metrics across environmental, social, and governance factors. '
        'Metrics are weighted based on their materiality to long-term sustainability and climate transition. '
        '70% weight is given to environmental metrics reflecting their dominant role in financial outcomes.'
    )
    pdf.ln(5)
    
    # Environmental Metrics (70% of total weight)
    pdf.section_title('Environmental Metrics (70% Total Weight)')
    pdf.set_font('Arial', '', 8)
    
    metrics = [
        ('MSCI ESG Environmental Score - 20%', 
         'Composite environmental score covering carbon, resources, pollution, and opportunities.'),
        
        ('ESG Score Environmental Weight - 15%', 
         'Percentage of ESG score from environmental factors. Shows prioritization in fund construction.'),
        
        ('Fund WACI (Carbon Intensity) - 20%', 
         'Emissions per million USD revenue. Key metric for Scope 1&2 and climate transition risk.'),
        
        ('Financed Carbon Emissions - 10%', 
         'Total carbon emissions financed per million USD invested. Absolute footprint metric.'),
        
        ('Fossil Fuel Reserves - 15%', 
         'Percentage in companies with fossil reserves. Identifies stranded asset risk.'),
    ]
    
    for metric, description in metrics:
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 6, metric, 0, 1)
        pdf.set_font('Arial', '', 8)
        pdf.multi_cell(0, 5, description)
        pdf.ln(2)
    
    # ESG Quality Metrics
    pdf.section_title('ESG Quality & Governance Metrics (30% Total Weight)')
    pdf.set_font('Arial', '', 8)
    
    quality_metrics = [
        ('MSCI ESG Score - 5%', 
         'Overall ESG rating. Independent third-party assessment.'),
        
        ('Fund ESG Leaders % - 5%', 
         'Percentage in top-rated ESG companies. Concentration in best-in-class.'),
        
        ('MSCI ESG Trend Positive % - 5%', 
         'Percentage with improving ESG scores. Captures positive momentum.'),
        
        ('Fund ESG Laggards % - 3%', 
         'Percentage in bottom-rated companies. Lower is better.'),
        
        ('Controversial Weapons - 1%', 
         'Exposure to controversial weapons. Zero tolerance approach.'),
        
        ('MSCI ESG Governance Score - 1%', 
         'Board quality, compensation, ownership. Governance risk indicator.'),
    ]
    
    for metric, description in quality_metrics:
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 6, metric, 0, 1)
        pdf.set_font('Arial', '', 8)
        pdf.multi_cell(0, 5, description)
        pdf.ln(2)
    
    # ========== Compliance footer ==========
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 5,
        'This report is generated for internal compliance and due diligence purposes. '
        'Fund selection is based on quantitative ESG metrics and does not constitute investment advice. '
        'Category-relative percentiles ensure fair comparison within peer groups.'
    )
    
    return bytes(pdf.output(dest='S'))