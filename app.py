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
    
    # Add category input for files without Morningstar Category
    category_override = st.text_input(
        "Category for uploaded CSVs (optional)",
        placeholder="e.g., Foreign Large Value",
        help="If your CSV doesn't have Morningstar Category column, specify it here"
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
            
            # If no Morningstar Category column and user provided one, add it
            if 'Morningstar Category' not in df.columns and category_override:
                df['Morningstar Category'] = category_override
                st.info(f"✅ Added category '{category_override}' to {file.name}")
            
            dfs.append(df)
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        st.success(f"✅ Loaded {len(combined_df)} funds from {len(uploaded_files)} files")
        
        # SECTION 1: Portfolio Comparison (if portfolio uploaded)
        if portfolio_file:
            st.header("📊 Portfolio vs. Screening Results")
            
            try:
                # Try multiple sheet names
                excel_file = pd.ExcelFile(portfolio_file)
                sheet_names = excel_file.sheet_names
                
                # Look for main portfolio sheet
                possible_sheets = ['ESG MAIN', 'ESG MAIN YCHARTS', 'ESG_MAIN', 'Main']
                portfolio_sheet = None
                
                for sheet in possible_sheets:
                    if sheet in sheet_names:
                        portfolio_sheet = sheet
                        break
                
                if portfolio_sheet:
                    st.info(f"📋 Loading portfolio from sheet: '{portfolio_sheet}'")
                    portfolio_df = pd.read_excel(portfolio_file, sheet_name=portfolio_sheet)
                    
                    # Check if first row contains 'Holding' or 'Model_Name' (indicates header row in data)
                    first_row_str = ' '.join(portfolio_df.iloc.astype(str).tolist())
                    
                    if 'Holding' in first_row_str or 'Model_Name' in first_row_str:
                        # Use first row as column names
                        new_columns = portfolio_df.iloc.tolist()
                        portfolio_df.columns = new_columns
                        portfolio_df = portfolio_df[1:].reset_index(drop=True)
                        st.success("✅ Detected and applied header row from data")
                    
                    st.subheader("Current Holdings Overview")
                    
                    # Try different column name variations
                    holding_col = None
                    weight_col = None
                    category_col = None
                    
                    for col in portfolio_df.columns:
                        col_str = str(col).lower()
                        if 'holding' in col_str:
                            holding_col = col
                        elif 'symbol' in col_str:
                            holding_col = col
                        
                        if 'weight' in col_str and 'percent' in col_str:
                            weight_col = col
                        
                        if 'category' in col_str:
                            category_col = col
                    
                    # Display holdings if found
                    if holding_col:
                        display_cols = [holding_col]
                        if weight_col:
                            display_cols.append(weight_col)
                        if category_col:
                            display_cols.append(category_col)
                        
                        # Clean the data (remove NaN rows)
                        portfolio_clean = portfolio_df[display_cols].dropna(subset=[holding_col])
                        
                        st.dataframe(
                            portfolio_clean.head(20),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Check which holdings are in screening universe
                        current_tickers = portfolio_clean[holding_col].dropna().unique()
                        screening_tickers = combined_df['Symbol'].unique() if 'Symbol' in combined_df.columns else []
                        
                        matches = set(current_tickers) & set(screening_tickers)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total Holdings", len(current_tickers))
                        col2.metric("In Screening Universe", f"{len(matches)}/{len(current_tickers)}")
                        
                        # Show status of current holdings
                        if len(matches) > 0 and 'Symbol' in combined_df.columns:
                            st.subheader("Current Holdings ESG Status")
                            
                            holdings_cols = ['Symbol', 'Name', 'FI ESG Quant Percentile Screen']
                            if 'Morningstar Category' in combined_df.columns:
                                holdings_cols.append('Morningstar Category')
                            
                            holdings_cols = [col for col in holdings_cols if col in combined_df.columns]
                            
                            holdings_status = combined_df[combined_df['Symbol'].isin(current_tickers)][holdings_cols]
                            
                            # Add status classification
                            if 'FI ESG Quant Percentile Screen' in holdings_status.columns:
                                holdings_status = holdings_status.copy()
                                holdings_status['Status'] = holdings_status['FI ESG Quant Percentile Screen'].apply(
                                    lambda x: '✅ Elite' if x <= config.PERCENTILE_THRESHOLDS['elite'] else 
                                             '✅ Qualified' if x <= config.PERCENTILE_THRESHOLDS['qualified'] else 
                                             '⚠️ Watchlist' if x <= config.PERCENTILE_THRESHOLDS['watchlist'] else 
                                             '❌ Review Required'
                                )
                            
                            st.dataframe(holdings_status.sort_values('FI ESG Quant Percentile Screen') if 'FI ESG Quant Percentile Screen' in holdings_status.columns else holdings_status, 
                                       use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ Could not identify holding/symbol column in portfolio")
                        st.info(f"Available columns: {', '.join([str(c) for c in portfolio_df.columns])}")
                else:
                    st.error("❌ Could not find portfolio sheet")
                    st.info(f"Available sheets: {', '.join(sheet_names)}")
                    
            except Exception as e:
                st.error(f"❌ Error loading portfolio file: {e}")
                import traceback
                st.code(traceback.format_exc())
        
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
                        
                        alert_cols = ['Symbol', 'Name', 'Alert', 'Percentile_Change', 
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
            categories = combined_df['Morningstar Category'].dropna().unique()
            
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
                
                display_cols = ['Symbol', 'Name', 'FI ESG Quant Percentile Screen', 'Status']
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
                        
                        if st.button("📄 Generate Compliance Report (PDF)"):
                            pdf_bytes = generate_compliance_report(category_df, selected_category, quarter)
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"ESG_Screening_{selected_category.replace('/', '_')}_{quarter}.pdf",
                                mime="application/pdf"
                            )
                    except ImportError:
                        st.info("💡 Install fpdf2 to enable PDF reports: pip install fpdf2")
            else:
                st.warning("⚠️ Column 'FI ESG Quant Percentile Screen' not found in data")
        else:
            st.warning("⚠️ YCharts export missing 'Morningstar Category' column")
            st.info("💡 Use the 'Category for uploaded CSVs' field in the sidebar to specify the category")
            st.info(f"Available columns: {', '.join(combined_df.columns.tolist())}")
            
            # Still allow viewing data without category
            if 'FI ESG Quant Percentile Screen' in combined_df.columns:
                st.subheader("All Funds (No Category Grouping)")
                
                combined_df_sorted = combined_df.sort_values('FI ESG Quant Percentile Screen').copy()
                
                combined_df_sorted['Status'] = combined_df_sorted['FI ESG Quant Percentile Screen'].apply(
                    lambda x: '✅ Elite' if x <= config.PERCENTILE_THRESHOLDS['elite'] else 
                             '✅ Qualified' if x <= config.PERCENTILE_THRESHOLDS['qualified'] else 
                             '⚠️ Watchlist' if x <= config.PERCENTILE_THRESHOLDS['watchlist'] else 
                             '❌ Review Required'
                )
                
                display_cols = ['Symbol', 'Name', 'FI ESG Quant Percentile Screen', 'Status']
                display_cols = [col for col in display_cols if col in combined_df_sorted.columns]
                
                st.dataframe(
                    combined_df_sorted[display_cols].head(20),
                    use_container_width=True,
                    hide_index=True
                )

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
        1. Click Browse files in sidebar
        2. Select all category CSVs (can upload multiple)
        3. **If CSV doesn't have 'Morningstar Category' column:** Enter the category name in the text field
        4. Dashboard combines and analyzes automatically
        
        #### Step 3: Review Results
        1. Select category from dropdown (or view all funds)
        2. Review top performers (Elite/Qualified funds)
        3. Check watchlist funds for replacements
        4. Export results for documentation
        
        #### Step 4: Document for Compliance
        1. Download CSV for each category
        2. Generate PDF compliance report
        3. Save to compliance folder
        4. Note fund changes for IC meeting
        
        #### Portfolio Upload Tips
        - Excel file should have sheet named 'ESG MAIN' or 'ESG MAIN YCHARTS'
        - Columns should include holdings/symbols and weights
        - Dashboard will auto-detect header rows
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
