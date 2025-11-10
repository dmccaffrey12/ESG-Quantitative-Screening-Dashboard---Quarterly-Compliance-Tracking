import streamlit as st
import pandas as pd
import numpy as np
import config

# Page configuration
st.set_page_config(
    page_title="ESG Fund Screening Dashboard",
    page_icon="🌱",
    layout="wide"
)

# Title
st.title("🌱 ESG Quantitative Screening Dashboard")
st.markdown("*Quarterly ESG Fund Review & Due Diligence Tracker*")

# Sidebar
with st.sidebar:
    st.header("📁 Upload YCharts Data")
    uploaded_files = st.file_uploader(
        "Upload YCharts CSV exports",
        type=['csv'],
        accept_multiple_files=True,
        help="Export from YCharts with all ESG metrics"
    )
    
    quarter = st.text_input("Quarter (e.g., 2025Q4)", "2025Q4")
    
    st.markdown("---")
    st.header("📊 Current Portfolio")
    portfolio_file = st.file_uploader(
        "Upload current ESG model (CSV)",
        type=['csv'],
        help="Upload your model template CSV"
    )
    
    st.markdown("---")
    st.header("📈 Historical Comparison")
    previous_files = st.file_uploader(
        "Upload previous quarter CSVs (optional)",
        type=['csv'],
        accept_multiple_files=True,
        help="Compare vs. prior quarter"
    )

# Main content
if uploaded_files:
    dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            
            # Standardize column names
            if 'Category Name' in df.columns:
                df.rename(columns={'Category Name': 'Morningstar Category'}, inplace=True)
            
            dfs.append(df)
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # CRITICAL: Calculate category-relative percentiles
        if 'FI ESG Quant Screen Scoring System' in combined_df.columns and 'Morningstar Category' in combined_df.columns:
            st.info("🔄 Calculating category-relative percentiles...")
            
            def calculate_category_percentile(group):
                """Calculate percentile rank within category (lower score = better)"""
                # Rank by composite score (higher score = better ESG)
                # Convert to percentile (1-100, where lower is better)
                group['Category_Percentile'] = group['FI ESG Quant Screen Scoring System'].rank(ascending=False, pct=True) * 100
                return group
            
            combined_df = combined_df.groupby('Morningstar Category', group_keys=False).apply(calculate_category_percentile)
            
            # Replace the global percentile with category-relative
            combined_df['FI ESG Quant Percentile Screen'] = combined_df['Category_Percentile']
            
            st.success(f"✅ Loaded {len(combined_df)} funds and calculated category-relative percentiles")
        else:
            st.warning("⚠️ Could not calculate category percentiles - missing required columns")
            st.success(f"✅ Loaded {len(combined_df)} funds")
        
        # Portfolio Comparison
        if portfolio_file:
            st.header("📊 Portfolio vs. Screening Results")
            
            try:
                portfolio_df = pd.read_csv(portfolio_file)
                
                st.subheader("Current Holdings Overview")
                
                # Find column names
                holding_col = None
                weight_col = None
                category_col = None
                
                for col in portfolio_df.columns:
                    col_lower = str(col).lower()
                    if 'holding' in col_lower:
                        holding_col = col
                    if 'weight' in col_lower:
                        weight_col = col
                    if 'category' in col_lower and 'global' not in col_lower:
                        category_col = col
                
                if holding_col:
                    display_cols = [col for col in [holding_col, weight_col, category_col] if col]
                    portfolio_clean = portfolio_df[display_cols].dropna(subset=[holding_col])
                    
                    st.dataframe(
                        portfolio_clean.head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    current_tickers = portfolio_clean[holding_col].dropna().unique()
                    screening_tickers = combined_df['Symbol'].unique() if 'Symbol' in combined_df.columns else []
                    
                    matches = set(current_tickers) & set(screening_tickers)
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Total Holdings", len(current_tickers))
                    col2.metric("In Screening Universe", f"{len(matches)}/{len(current_tickers)}")
                    
                    if len(matches) > 0 and 'Symbol' in combined_df.columns:
                        st.subheader("Current Holdings ESG Status")
                        
                        holdings_cols = ['Symbol', 'Name', 'Morningstar Category', 'FI ESG Quant Percentile Screen']
                        holdings_cols = [col for col in holdings_cols if col in combined_df.columns]
                        
                        holdings_status = combined_df[combined_df['Symbol'].isin(current_tickers)][holdings_cols].copy()
                        
                        if 'FI ESG Quant Percentile Screen' in holdings_status.columns:
                            holdings_status['Status'] = holdings_status['FI ESG Quant Percentile Screen'].apply(
                                lambda x: '✅ Elite' if x <= config.PERCENTILE_THRESHOLDS['elite'] else 
                                         '✅ Qualified' if x <= config.PERCENTILE_THRESHOLDS['qualified'] else 
                                         '⚠️ Watchlist' if x <= config.PERCENTILE_THRESHOLDS['watchlist'] else 
                                         '❌ Review Required'
                            )
                            holdings_status = holdings_status.sort_values('FI ESG Quant Percentile Screen')
                        
                        st.dataframe(holdings_status, use_container_width=True, hide_index=True)
                else:
                    st.warning("Could not identify holding column in portfolio")
                    
            except Exception as e:
                st.error(f"Error loading portfolio: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        # Quarter-over-Quarter Comparison
        if previous_files:
            st.header("📈 Quarter-over-Quarter Changes")
            
            try:
                prev_dfs = [pd.read_csv(f) for f in previous_files]
                prev_combined = pd.concat(prev_dfs, ignore_index=True)
                
                # Standardize previous quarter columns
                if 'Category Name' in prev_combined.columns:
                    prev_combined.rename(columns={'Category Name': 'Morningstar Category'}, inplace=True)
                
                # Calculate category percentiles for previous quarter
                if 'FI ESG Quant Screen Scoring System' in prev_combined.columns and 'Morningstar Category' in prev_combined.columns:
                    def calc_prev_percentile(group):
                        group['Category_Percentile'] = group['FI ESG Quant Screen Scoring System'].rank(ascending=False, pct=True) * 100
                        return group
                    
                    prev_combined = prev_combined.groupby('Morningstar Category', group_keys=False).apply(calc_prev_percentile)
                    prev_combined['FI ESG Quant Percentile Screen'] = prev_combined['Category_Percentile']
                
                if 'Symbol' in combined_df.columns and 'Symbol' in prev_combined.columns:
                    comparison = combined_df.merge(
                        prev_combined[['Symbol', 'FI ESG Quant Percentile Screen']],
                        on='Symbol',
                        how='inner',
                        suffixes=('_current', '_previous')
                    )
                    
                    comparison['Percentile_Change'] = (
                        comparison['FI ESG Quant Percentile Screen_current'] - 
                        comparison['FI ESG Quant Percentile Screen_previous']
                    )
                    
                    comparison['Alert'] = comparison['Percentile_Change'].apply(
                        lambda x: '🔴 Deteriorated' if x > 25 else 
                                 '🟠 Watchlist' if x > 15 else 
                                 '🟡 Minor Change' if x > 5 else 
                                 '✅ Stable/Improved'
                    )
                    
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
        
        # Category Analysis
        if 'Morningstar Category' in combined_df.columns:
            categories = combined_df['Morningstar Category'].dropna().unique()
            
            st.header("🎯 Fund Universe by Category")
            selected_category = st.selectbox("Select Morningstar Category", sorted(categories))
            
            category_df = combined_df[combined_df['Morningstar Category'] == selected_category].copy()
            
            if 'FI ESG Quant Percentile Screen' in category_df.columns:
                category_df = category_df.sort_values('FI ESG Quant Percentile Screen')
                
                category_df['Status'] = category_df['FI ESG Quant Percentile Screen'].apply(
                    lambda x: '✅ Elite' if x <= config.PERCENTILE_THRESHOLDS['elite'] else 
                             '✅ Qualified' if x <= config.PERCENTILE_THRESHOLDS['qualified'] else 
                             '⚠️ Watchlist' if x <= config.PERCENTILE_THRESHOLDS['watchlist'] else 
                             '❌ Review Required'
                )
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_count = len(category_df)
                elite_count = len(category_df[category_df['Status'] == '✅ Elite'])
                qualified_count = len(category_df[category_df['Status'] == '✅ Qualified'])
                watchlist_count = len(category_df[category_df['Status'] == '⚠️ Watchlist'])
                
                col1.metric("Total Funds", total_count)
                col2.metric("Elite (Top 25%)", elite_count)
                col3.metric("Qualified (Top 37%)", qualified_count)
                col4.metric("Watchlist", watchlist_count)
                
                st.subheader("Top Performing Funds")
                
                display_cols = ['Symbol', 'Name', 'FI ESG Quant Percentile Screen', 'FI ESG Quant Screen Scoring System', 'Status']
                display_cols = [col for col in display_cols if col in category_df.columns]
                
                st.dataframe(
                    category_df[display_cols].head(20),
                    use_container_width=True,
                    hide_index=True
                )
                
                st.subheader("📥 Export Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = category_df.to_csv(index=False)
                    st.download_button(
                        label=f"Download {selected_category} Results (CSV)",
                        data=csv,
                        file_name=f"{selected_category.replace('/', '_')}_{quarter}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    try:
                        from report_generator import generate_compliance_report
                        
                        if st.button("📄 Generate Compliance Report (PDF)"):
                            # Pass portfolio_df to report generator if available
                            portfolio_data = None
                            if portfolio_file:
                                try:
                                    portfolio_data = pd.read_csv(portfolio_file)
                                except:
                                    pass
                            
                            pdf_bytes = generate_compliance_report(
                                category_df, 
                                selected_category, 
                                quarter,
                                portfolio_df=portfolio_data
                            )
                            
                            st.download_button(
                                label="Download Enhanced PDF Report",
                                data=pdf_bytes,
                                file_name=f"ESG_Screening_{selected_category.replace('/', '_')}_{quarter}.pdf",
                                mime="application/pdf"
                            )
                            st.success("✅ PDF generated with portfolio holdings analysis!")
                    except ImportError:
                        st.info("Install fpdf2 for PDF reports: pip install fpdf2")
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
            else:
                st.warning("Missing required columns for analysis")
        else:
            st.warning("Missing 'Category Name' column in YCharts export")

else:
    st.info("👈 Upload YCharts CSV exports to begin")
    
    with st.expander("📖 How to Use This Dashboard"):
        st.markdown("""
        ### Quick Start Guide
        
        #### Step 1: Export from YCharts
        1. Open YCharts Fund Screener
        2. Add all ESG metrics + **Category Name** column
        3. Export entire universe (no category filter needed)
        4. Save as: ESG_Screening_2025Q4.csv
        
        #### Step 2: Upload
        1. Upload your comprehensive screening CSV
        2. Dashboard automatically calculates category-relative percentiles
        3. No need to specify category manually
        
        #### Step 3: Review by Category
        1. Use dropdown to select each category
        2. See top performers within that category
        3. Generate compliance PDFs
        
        #### Step 4: Portfolio Analysis
        1. Upload your model template CSV
        2. Dashboard shows current holdings' ESG status
        3. Identifies which holdings need replacement
        """)
    
    with st.expander("⚙️ Configuration"):
        st.markdown("### ESG Metric Weights")
        weights_df = pd.DataFrame([
            {"Metric": k, "Weight": f"{v*100:.0f}%"} 
            for k, v in config.METRIC_WEIGHTS.items()
        ])
        st.dataframe(weights_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Percentile Thresholds (Category-Relative)")
        thresholds_df = pd.DataFrame([
            {"Status": k.title(), "Percentile <=": v} 
            for k, v in config.PERCENTILE_THRESHOLDS.items()
        ])
        st.dataframe(thresholds_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(f"ESG Screening Dashboard | {quarter} | Category-Relative Rankings")