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

def clean_status_for_pdf(status):
    """Remove Unicode characters that fpdf can't handle"""
    if not isinstance(status, str):
        return str(status)
    
    # Remove emojis and replace with text
    status = status.replace('✅', '').replace('⚠️', '').replace('❌', '').strip()
    
    # Simplify status names
    if 'Elite' in status:
        return 'Elite'
    elif 'Qualified' in status:
        return 'Qualified'
    elif 'Watchlist' in status:
        return 'Watchlist'
    elif 'Review' in status:
        return 'Review Required'
    else:
        return status

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
    # Clean category name of any special characters
    clean_category = category_name.replace('/', '-')
    pdf.cell(0, 10, f'Category: {clean_category}', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Quarter: {quarter}', 0, 1)
    pdf.cell(0, 10, f'Report Date: {datetime.now().strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(10)
    
    # Summary statistics section
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Summary Statistics', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    total = len(category_df)
    elite = 0
    qualified = 0
    
    # Count statuses (handle both with and without emojis)
    if 'Status' in category_df.columns:
        for status in category_df['Status']:
            clean = clean_status_for_pdf(str(status))
            if 'Elite' in clean:
                elite += 1
            elif 'Qualified' in clean:
                qualified += 1
    
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
        fund_name = str(row.get('Fund Name', row.get('Name', 'N/A')))[:35]
        percentile = row.get('FI ESG Quant Percentile Screen', 0)
        status = clean_status_for_pdf(str(row.get('Status', '')))
        
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
        'Reserves, and ESG quality indicators. Top quartile funds (percentile <=25) qualify '
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
    
    return bytes(pdf.output(dest='S'))