from fpdf import FPDF
import pandas as pd
from datetime import datetime

class ESGComplianceReport(FPDF):
    """Custom PDF class for ESG screening reports"""
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ESG Quantitative Screening Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_compliance_report(category_df, category_name, quarter):
    """
    Generate PDF compliance report for quarterly due diligence
    
    Args:
        category_df: DataFrame with fund data for the category
        category_name: String name of Morningstar category
        quarter: String like '2025Q4'
    
    Returns:
        PDF bytes for download
    """
    
    pdf = ESGComplianceReport()
    pdf.add_page()
    
    # Report header section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Category: {category_name}', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Quarter: {quarter}', 0, 1)
    pdf.cell(0, 10, f'Report Date: {datetime.now().strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(10)
    
    # Summary statistics section
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Summary Statistics', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    total = len(category_df)
    elite = len(category_df[category_df['Status'] == '✅ Elite']) if 'Status' in category_df.columns else 0
    qualified = len(category_df[category_df['Status'] == '✅ Qualified']) if 'Status' in category_df.columns else 0
    
    pdf.cell(0, 8, f'Total Funds Analyzed: {total}', 0, 1)
    if total > 0:
        pdf.cell(0, 8, f'Elite Funds (Top 25%): {elite} ({elite/total*100:.1f}%)', 0, 1)
        pdf.cell(0, 8, f'Qualified Funds (Top 37%): {qualified} ({qualified/total*100:.1f}%)', 0, 1)
    pdf.ln(10)
    
    # Top 10 funds table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Top 10 Qualifying Funds', 0, 1)
    pdf.set_font('Arial', '', 9)
    
    # Table header
    pdf.cell(30, 8, 'Ticker', 1)
    pdf.cell(80, 8, 'Fund Name', 1)
    pdf.cell(30, 8, 'Percentile', 1)
    pdf.cell(30, 8, 'Status', 1)
    pdf.ln()
    
    # Table rows (top 10 funds)
    for _, row in category_df.head(10).iterrows():
        ticker = str(row.get('Symbol', 'N/A'))[:10]
        fund_name = str(row.get('Fund Name', 'N/A'))[:35]
        percentile = row.get('FI ESG Quant Percentile Screen', 0)
        status = row.get('Status', '').replace('✅', '').replace('⚠️', '').replace('❌', '').strip()
        
        pdf.cell(30, 8, ticker, 1)
        pdf.cell(80, 8, fund_name, 1)
        pdf.cell(30, 8, f"{percentile:.1f}", 1)
        pdf.cell(30, 8, status[:12], 1)
        pdf.ln()
    
    # Methodology section
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Screening Methodology', 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 6, 
        'This report documents the quarterly ESG screening process using an 11-metric '
        'quantitative framework. Funds are ranked within their Morningstar Category using '
        'percentile ranking on ESG metrics including Environmental Score, WACI, Fossil Fuel '
        'Reserves, and ESG quality indicators. Top quartile funds (percentile ≤25) qualify '
        'for core portfolio inclusion. This screening process ensures systematic, repeatable, '
        'and auditable fund selection for compliance documentation.'
    )
    
    # Compliance note
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 5,
        'This report is generated for internal compliance and due diligence purposes. '
        'Fund selection is based on quantitative ESG metrics and does not constitute '
        'investment advice. Past performance does not guarantee future results.'
    )
    
    return pdf.output(dest='S').encode('latin-1')
