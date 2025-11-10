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

# Create two tabs: Dashboard and Methodology
tab1, tab2 = st.tabs(["📊 Screening Dashboard", "📖 Methodology"])

# ============================================================================
# TAB 1: SCREENING DASHBOARD
# ============================================================================

with tab1:
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
                    """Calculate percentile rank within category"""
                    group['Category_Percentile'] = group['FI ESG Quant Screen Scoring System'].rank(ascending=False, pct=True) * 100
                    return group
                
                combined_df = combined_df.groupby('Morningstar Category', group_keys=False).apply(calculate_category_percentile)
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
                                             '⚠️ Review' if x <= config.PERCENTILE_THRESHOLDS['review'] else 
                                             '❌ Replace'
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
                                 '⚠️ Review' if x <= config.PERCENTILE_THRESHOLDS['review'] else 
                                 '❌ Replace'
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    total_count = len(category_df)
                    elite_count = len(category_df[category_df['Status'] == '✅ Elite'])
                    review_count = len(category_df[category_df['Status'] == '⚠️ Review'])
                    replace_count = len(category_df[category_df['Status'] == '❌ Replace'])
                    
                    col1.metric("Total Funds", total_count)
                    col2.metric("Elite (≤25%ile)", elite_count)
                    col3.metric("Review (26-50%ile)", review_count)
                    
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
        
        with st.expander("📖 Quick Start Guide"):
            st.markdown("""
            #### Step 1: Export from YCharts
            1. Open YCharts Fund Screener
            2. Add all ESG metrics + **Category Name** column
            3. Export entire universe (no category filter needed)
            
            #### Step 2: Upload
            1. Upload your comprehensive screening CSV
            2. Dashboard automatically calculates category-relative percentiles
            
            #### Step 3: Review by Category
            1. Use dropdown to select each category
            2. See top performers within that category
            3. Generate compliance PDFs
            """)

# ============================================================================
# TAB 2: METHODOLOGY
# ============================================================================

with tab2:
    st.title("ESG Quantitative Screening Methodology")
    
    st.markdown("---")
    
    # Philosophy section
    st.header("🎯 Our Philosophy: 'Elite or Replace'")
    
    st.markdown("""
    Our ESG screening adopts a strict **"Elite or Replace"** standard. In well-populated 
    categories (e.g., Large Blend, Foreign Large Value), there are typically 20-50 Elite 
    funds available. With sufficient options in the top quartile, holding anything below 
    the 25th percentile requires extraordinary justification.
    
    ### Why This Approach?
    
    **1. Defensible Standard**  
    "We only hold top quartile ESG funds" is a clear, binary statement for clients and regulators.
    
    **2. Abundant Options**  
    Most categories have 15+ Elite funds, providing sufficient diversification.
    
    **3. Avoids "Good Enough" Trap**  
    Without strict standards, portfolios drift toward mediocre ESG performance.
    
    **4. Simplifies IC Discussion**  
    Elite = automatic qualification. Anything else = justify or replace.
    """)
    
    st.markdown("---")
    
    # Qualification thresholds
    st.header("📏 Qualification Thresholds (Category-Relative)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Elite", "≤ 25th %ile")
        st.caption("**Top Quartile**")
        st.caption("Automatic qualification. Best-in-class ESG performance within category.")
    
    with col2:
        st.metric("⚠️ Review", "26-50th %ile")
        st.caption("**Second Quartile**")
        st.caption("Requires IC justification. Consider replacement with Elite alternative.")
    
    with col3:
        st.metric("❌ Replace", "> 50th %ile")
        st.caption("**Bottom Half**")
        st.caption("Replace at next rebalancing. Insufficient ESG quality.")
    
    st.markdown("---")
    
    # When we hold non-elite funds
    st.header("🤔 When We Hold Non-Elite Funds")
    
    st.markdown("""
    Rarely, we may hold a fund in the 26th-50th percentile if:
    
    - **Limited Elite Options**: Category has <10 Elite funds (e.g., Infrastructure)
    - **Unique Exposure**: Specific climate transition theme not available in Elite tier
    - **Transition Period**: Recent ESG deterioration, replacement planned next quarter
    - **Operational Constraints**: Cost/liquidity issues prevent immediate replacement
    
    **All exceptions require Investment Committee approval and quarterly re-evaluation.**
    """)
    
    st.markdown("---")
    
    # Metric framework
    st.header("📊 ESG Metric Framework")
    
    st.subheader("Environmental Metrics (70% Total Weight)")
    
    env_metrics = pd.DataFrame([
        {
            "Metric": "MSCI ESG Environmental Score",
            "Weight": "20%",
            "Rationale": "Composite environmental performance. Holistic view of environmental impact."
        },
        {
            "Metric": "ESG Score Environmental Weight",
            "Weight": "15%",
            "Rationale": "% of ESG score from environmental factors. Shows fund's environmental prioritization."
        },
        {
            "Metric": "Fund WACI (Carbon Intensity)",
            "Weight": "20%",
            "Rationale": "Emissions per revenue. Key metric for Scope 1&2 exposure and climate risk."
        },
        {
            "Metric": "Financed Carbon Emissions",
            "Weight": "10%",
            "Rationale": "Total emissions financed per $M. Absolute footprint metric for net-zero alignment."
        },
        {
            "Metric": "Fossil Fuel Reserves",
            "Weight": "15%",
            "Rationale": "% portfolio in companies with reserves. Stranded asset risk identifier."
        }
    ])
    
    st.dataframe(env_metrics, use_container_width=True, hide_index=True)
    
    st.markdown("""
    **Why 70% Environmental Weight?**  
    Climate transition is the dominant ESG factor for long-term returns. Funds positioned for a 
    low-carbon economy should outperform as regulatory pressure increases and carbon pricing expands.
    """)
    
    st.markdown("---")
    
    st.subheader("ESG Quality & Governance Metrics (30% Total Weight)")
    
    qual_metrics = pd.DataFrame([
        {
            "Metric": "MSCI ESG Score",
            "Weight": "5%",
            "Rationale": "Overall ESG rating. Independent third-party assessment."
        },
        {
            "Metric": "Fund ESG Leaders %",
            "Weight": "5%",
            "Rationale": "% in top-rated ESG companies. Concentration in best-in-class."
        },
        {
            "Metric": "MSCI ESG Trend Positive %",
            "Weight": "5%",
            "Rationale": "% holdings with improving scores. Captures positive ESG momentum."
        },
        {
            "Metric": "Fund ESG Laggards %",
            "Weight": "3%",
            "Rationale": "% in bottom-rated companies. Flags significant ESG risk."
        },
        {
            "Metric": "Controversial Weapons",
            "Weight": "1%",
            "Rationale": "Controversial weapons exposure. Zero tolerance approach."
        },
        {
            "Metric": "MSCI ESG Governance Score",
            "Weight": "1%",
            "Rationale": "Board quality and governance. Risk management indicator."
        }
    ])
    
    st.dataframe(qual_metrics, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Category-relative ranking
    st.header("🎯 Why Category-Relative Rankings?")
    
    st.markdown("""
    **Problem with Global Rankings:**
    
    Traditional ESG rankings compare all funds globally. This penalizes certain sectors:
    - Utilities rank low due to inherent emissions intensity
    - Technology ranks high due to low physical footprint
    - Result: False negatives and sector concentration bias
    
    **Our Solution: Category-Relative Percentiles**
    
    We rank funds **within** their Morningstar Category. This prevents sector bias and 
    identifies true best-in-class for each category.
    
    **Example:**
    | Fund Type | Global %ile | Category %ile | Our Classification |
    |-----------|-------------|---------------|--------------------|
    | Utility | 87th | 10th (utilities) | ✅ **Elite** |
    | Tech | 12th | 67th (tech) | ❌ **Replace** |
    
    The utility fund is Elite **for its sector**. Fair comparison!
    """)
    
    st.markdown("---")
    
    # Compliance documentation
    st.header("📝 Compliance & Documentation")
    
    st.markdown("""
    ### Quarterly Process
    
    1. **Export from YCharts**: All ESG metrics + Category
    2. **Calculate Percentiles**: Automated ranking within each category
    3. **Review Holdings**: Dashboard identifies Elite/Review/Replace funds
    4. **IC Decision**: Approve Elite, justify Review tier, replace bottom half
    5. **Document**: PDF compliance reports for each category
    6. **Archive**: Save quarterly CSVs for audit trail
    """)

st.markdown("---")
st.caption(f"ESG Screening Dashboard | Elite or Replace Philosophy | Category-Relative Rankings")