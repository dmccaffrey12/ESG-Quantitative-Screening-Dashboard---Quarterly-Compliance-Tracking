import streamlit as st
import pandas as pd
import config

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="ESG Fund Screening Dashboard",
    page_icon="🌱",
    layout="wide"
)

# Title and description
st.title("🌱 ESG Quantitative Screening Dashboard")
st.markdown("*Quarterly ESG Fund Review & Due Diligence Tracker*")

# Sidebar - File uploads and configuration
with st.sidebar:
    st.header("📁 Upload YCharts Data")
    uploaded_files = st.file_uploader(
        "Upload YCharts CSV exports",
        type=['csv'],
        accept_multiple_files=True,
        help="Export from YCharts with all 11 ESG metrics"
    )
    
    quarter = st.text_input("Quarter (e.g., 2025Q4)", "2025Q4")
    
    st.markdown("---")
    st.header("📊 Current Portfolio")
    portfolio_file = st.file_uploader(
        "Upload current ESG model (Excel)",
        type=['xlsx'],
        help="Upload your esg_master_all_allocations file"
    )
    
    st.markdown("---")
    st.header("📈 Historical Comparison")
    previous_files = st.file_uploader(
        "Upload previous quarter CSVs (optional)",
        type=['csv'],
        accept_multiple_files=True,
        help="Compare vs. prior quarter"
    )

# Main content area
if uploaded_files:
    # Load and combine all uploaded CSVs
    dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        st.success(f"✅ Loaded {len(combined_df)} funds from {len(uploaded_files)} files")
        
        # SECTION 1: Portfolio Comparison (if portfolio uploaded)
        if portfolio_file:
            st.header("�� Portfolio vs. Screening Results")
            
            try:
                # Try to load portfolio Excel file
                portfolio_df = pd.read_excel(portfolio_file, sheet_name='ESG MAIN YCHARTS')
                
                st.subheader("Current Holdings Overview")
                
                # Display top 20 holdings
                display_cols = ['Holding', 'WeightedPercentage', 'Category']
                display_cols = [col for col in display_cols if col in portfolio_df.columns]
                
                if display_cols:
                    st.dataframe(
                        portfolio_df[display_cols].head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Check which holdings are in screening universe
                current_tickers = portfolio_df['Holding'].unique()
                screening_tickers = combined_df['Symbol'].unique() if 'Symbol' in combined_df.columns else []
                
                matches = set(current_tickers) & set(screening_tickers)
                
                col1, col2 = st.columns(2)
                col1.metric("Total Holdings", len(current_tickers))
                col2.metric("In Screening Universe", f"{len(matches)}/{len(current_tickers)}")
                
                # Show status of current holdings
                if len(matches) > 0 and 'Symbol' in combined_df.columns:
                    st.subheader("Current Holdings ESG Status")
                    
                    holdings_cols = ['Symbol', 'Fund Name', 'FI ESG Quant Percentile Screen', 'Morningstar Category']
                    holdings_cols = [col for col in holdings_cols if col in combined_df.columns]
                    
                    holdings_status = combined_df[combined_df['Symbol'].isin(current_tickers)][holdings_cols]
                    
                    st.dataframe(holdings_status, use_container_width=True, hide_index=True)
                    
            except Exception as e:
                st.error(f"Error loading portfolio file: {e}")
                st.info("Make sure your Excel file has a sheet named 'ESG MAIN YCHARTS'")
        
        # SECTION 2: Quarter-over-Quarter Comparison
        if previous_files:
            st.header("📈 Quarter-over-Quarter Changes")
            
            try:
                prev_dfs = [pd.read_csv(f) for f in previous_files]
                prev_combined = pd.concat(prev_dfs, ignore_index=True)
                
                if 'Symbol' in combined_df.columns and 'Symbol' in prev_combined.columns:
                    # Merge current and previous quarter data
                    comparison = combined_df.merge(
                        prev_combined[['Symbol', 'FI ESG Quant Percentile Screen']],
                        on='Symbol',
                        how='inner',
                        suffixes=('_current', '_previous')
                    )
                    
                    # Calculate percentile change
                    comparison['Percentile_Change'] = (
                        comparison['FI ESG Quant Percentile Screen_current'] - 
                        comparison['FI ESG Quant Percentile Screen_previous']
                    )
                    
                    # Flag significant changes
                    comparison['Alert'] = comparison['Percentile_Change'].apply(
                        lambda x: '🔴 Deteriorated' if x > 50 else 
                                 '🟠 Watchlist' if x > 25 else 
                                 '🟡 Minor Change' if x > 10 else 
                                 '✅ Stable/Improved'
                    )
                    
                    # Show alerts for deteriorated funds
                    alerts = comparison[comparison['Alert'].isin(['🔴 Deteriorated', '🟠 Watchlist'])]
                    
                    if len(alerts) > 0:
                        st.warning(f"⚠️ {len(alerts)} funds flagged for attention")
                        
                        alert_cols = ['Symbol', 'Fund Name', 'Alert', 'Percentile_Change', 
                                     'FI ESG Quant Percentile Screen_current']
                        alert_cols = [col for col in alert_cols if col in alerts.columns]
                        
                        st.dataframe(
                            alerts[alert_cols].sort_values('Percentile_Change', ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.success("✅ No funds require immediate attention")
                        
            except Exception as e:
                st.error(f"Error comparing quarters: {e}")
        
        # SECTION 3: Category Analysis (Main Screening Interface)
        if 'Morningstar Category' in combined_df.columns:
            categories = combined_df['Morningstar Category'].unique()
            
            st.header("🎯 Fund Universe by Category")
            selected_category = st.selectbox("Select Morningstar Category", sorted(categories))
            
            # Filter to selected category
            category_df = combined_df[combined_df['Morningstar Category'] == selected_category].copy()
            
            if 'FI ESG Quant Percentile Screen' in category_df.columns:
                # Sort by percentile (lower is better)
                category_df = category_df.sort_values('FI ESG Quant Percentile Screen')
                
                # Classify funds based on percentile thresholds
                category_df['Status'] = category_df['FI ESG Quant Percentile Screen'].apply(
                    lambda x: '✅ Elite' if x <= config.PERCENTILE_THRESHOLDS['elite'] else 
                             '✅ Qualified' if x <= config.PERCENTILE_THRESHOLDS['qualified'] else 
                             '⚠️ Watchlist' if x <= config.PERCENTILE_THRESHOLDS['watchlist'] else 
                             '❌ Review Required'
                )
                
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_count = len(category_df)
                elite_count = len(category_df[category_df['Status'] == '✅ Elite'])
                qualified_count = len(category_df[category_df['Status'] == '✅ Qualified'])
                watchlist_count = len(category_df[category_df['Status'] == '⚠️ Watchlist'])
                
                col1.metric("Total Funds", total_count)
                col2.metric("Elite (Top 25%)", elite_count)
                col3.metric("Qualified (Top 37%)", qualified_count)
                col4.metric("Watchlist", watchlist_count)
                
                # Show top performing funds
                st.subheader("Top Performing Funds")
                
                display_cols = ['Symbol', 'Fund Name', 'FI ESG Quant Percentile Screen', 'Status']
                display_cols = [col for col in display_cols if col in category_df.columns]
                
                st.dataframe(
                    category_df[display_cols].head(10),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Export functionality
                st.subheader("📥 Export Results")
                
                col1, col2 = st.columns(2)
                
                # CSV Export
                with col1:
                    csv = category_df.to_csv(index=False)
                    st.download_button(
                        label=f"Download {selected_category} Results (CSV)",
                        data=csv,
                        file_name=f"{selected_category.replace('/', '_')}_{quarter}.csv",
                        mime="text/csv"
                    )
                
                # PDF Export
                with col2:
                    try:
                        from report_generator import generate_compliance_report
                        
                        if st.button("Generate Compliance Report (PDF)"):
                            pdf_bytes = generate_compliance_report(category_df, selected_category, quarter)
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"ESG_Screening_{selected_category.replace('/', '_')}_{quarter}.pdf",
                                mime="application/pdf"
                            )
                    except ImportError:
                        st.info("Install fpdf2 to enable PDF reports: pip install fpdf2")
            else:
                st.warning("⚠️ Column 'FI ESG Quant Percentile Screen' not found in data")
        else:
            st.warning("⚠️ YCharts export missing 'Morningstar Category' column")
            st.info("Available columns: " + ", ".join(combined_df.columns.tolist()))

else:
    # Instructions when no files are uploaded
    st.info("👈 Upload YCharts CSV exports to begin")
    
    with st.expander("📖 How to Use This Dashboard"):
        st.markdown("""
        ### Quick Start Guide
        
        #### Step 1: Export from YCharts
        1. Open YCharts Fund Screener
        2. Filter by Morningstar Category
        3. Add all 11 ESG metrics to view
        4. Export to CSV
        5. Repeat for each category you want to screen
        
        #### Step 2: Upload CSVs
        1. Click Browse files in sidebar under Upload YCharts Data
        2. Select all category CSVs (can upload multiple at once)
        3. Dashboard will automatically combine and analyze
        
        #### Step 3: Review Results
        1. Select category from dropdown
        2. Review top performers (Elite and Qualified funds)
        3. Check watchlist funds for potential replacements
        4. Export results for documentation
        
        #### Step 4: Document for Compliance
        1. Download CSV for each category (for spreadsheet analysis)
        2. Generate PDF compliance report (for quarterly files)
        3. Save to compliance folder
        4. Note any fund changes for Investment Committee meeting
        
        #### Optional: Portfolio Comparison
        - Upload your current ESG model Excel file
        - See which holdings are in top quartile vs. need replacement
        
        #### Optional: Historical Tracking
        - Upload previous quarters CSVs
        - Identify funds that have deteriorated significantly
        - Prioritize replacements based on percentile changes
        """)
    
    with st.expander("⚙️ Configuration"):
        st.markdown("### ESG Metric Weights")
        
        weights_df = pd.DataFrame([
            {"Metric": k, "Weight": f"{v*100:.0f}%"} 
            for k, v in config.METRIC_WEIGHTS.items()
        ])
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Percentile Thresholds")
        thresholds_df = pd.DataFrame([
            {"Status": k.title(), "Percentile ≤": v} 
            for k, v in config.PERCENTILE_THRESHOLDS.items()
        ])
        st.dataframe(thresholds_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption(f"ESG Screening Dashboard | {quarter} | Last Updated: November 2025")
