import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, r2_score, mean_squared_error

st.set_page_config(page_title="DataPulse | Analytics Studio", page_icon="⚡", layout="wide")

# Modern Styling
st.markdown("""
<style>
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        margin-bottom: 12px;
    }
    .metric-title { font-size: 13px; color: #888; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .metric-val { font-size: 28px; font-weight: 700; color: #f0f2f6; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & HELPERS -----------------
def sanitize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitizes columns to avoid PyArrow serialization errors."""
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    return df

st.title("⚡ DataPulse: Enterprise Data Engine")
st.caption("Automated Exploratory Data Analysis, Outlier Profiling & Multi-Model Competitions.")

uploaded_file = st.sidebar.file_uploader("📂 Load Source Dataset (CSV)", type=["csv"])

if uploaded_file is None:
    st.info("👈 Upload a dataset in the sidebar to launch analysis workspace.")
    st.stop()

# Initialize data in session state
if "df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
    raw_df = pd.read_csv(uploaded_file)
    st.session_state.df = sanitize_data(raw_df)
    st.session_state.file_name = uploaded_file.name

df = st.session_state.df

# Top Row KPI Banner
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
missing_cells = int(df.isna().sum().sum())
total_cells = df.shape[0] * df.shape[1]
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Observations</div><div class="metric-val">{df.shape[0]:,}</div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Dimensions</div><div class="metric-val">{df.shape[1]} cols</div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Data Completeness</div><div class="metric-val">{100 - (missing_cells / total_cells * 100):.1f}%</div></div>', unsafe_allow_html=True)
with kpi4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Numeric Features</div><div class="metric-val">{len(numeric_cols)}</div></div>', unsafe_allow_html=True)

# ----------------- MAIN WORKBENCH -----------------
tab_eda, tab_prep, tab_viz, tab_automl = st.tabs([
    "📈 Automated Diagnostics", 
    "🛠️ Feature Engineering", 
    "📊 Advanced Visualizer", 
    "🤖 Multi-Model Tournament"
])

# ----------------- TAB 1: ADVANCED DIAGNOSTICS -----------------
with tab_eda:
    st.subheader("Data Architecture & Integrity")
    st.dataframe(df.head(8), width='stretch')

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("**Column Schema Breakdown**")
        schema_summary = []
        for col in df.columns:
            null_cnt = df[col].isnull().sum()
            schema_summary.append({
                "Column": col,
                "Type": str(df[col].dtype),
                "Missing %": round((null_cnt / len(df)) * 100, 2),
                "Distinct Values": df[col].nunique()
            })
        st.dataframe(pd.DataFrame(schema_summary), height=280, width='stretch')

    with c2:
        st.markdown("**Outlier Intelligence (IQR Threshold: 1.5x)**")
        outlier_records = []
        for col in numeric_cols:
            q25, q75 = df[col].quantile(0.25), df[col].quantile(0.75)
            iqr = q75 - q25
            outliers = df[(df[col] < (q25 - 1.5 * iqr)) | (df[col] > (q75 + 1.5 * iqr))]
            outlier_records.append({"Feature": col, "Outlier Count": len(outliers), "Outlier %": round((len(outliers)/len(df))*100, 2)})
        st.dataframe(pd.DataFrame(outlier_records), height=280, width='stretch')

# ----------------- TAB 2: DATA PREP WORKSHOP -----------------
with tab_prep:
    st.subheader("Interactive Preprocessing")
    col_prep1, col_prep2 = st.columns(2)
    
    with col_prep1:
        st.markdown("**Column Pruning**")
        drop_cols = st.multiselect("Select irrelevant identifiers or high-cardinality columns to drop:", df.columns)
        if st.button("Apply Pruning") and drop_cols:
            st.session_state.df = st.session_state.df.drop(columns=drop_cols)
            st.success(f"Removed: {', '.join(drop_cols)}")
            st.rerun()

    with col_prep2:
        st.markdown("**Missing Value Imputation**")
        target_impute_col = st.selectbox("Select column to impute:", options=["None"] + list(df.columns))
        strategy = st.radio("Strategy:", ["Drop Rows", "Median (Numeric)", "Mode (Categorical)"], horizontal=True)
        
        if st.button("Apply Imputation") and target_impute_col != "None":
            if strategy == "Drop Rows":
                st.session_state.df = st.session_state.df.dropna(subset=[target_impute_col])
            elif strategy == "Median (Numeric)" and target_impute_col in numeric_cols:
                st.session_state.df[target_impute_col] = st.session_state.df[target_impute_col].fillna(st.session_state.df[target_impute_col].median())
            elif strategy == "Mode (Categorical)":
                st.session_state.df[target_impute_col] = st.session_state.df[target_impute_col].fillna(st.session_state.df[target_impute_col].mode()[0])
            st.success("Imputation complete.")
            st.rerun()

# ----------------- TAB 3: VISUALIZATION STUDIO -----------------
with tab_viz:
    st.subheader("Interactive Bi-Variate & Multivariate Explorer")
    vc1, vc2, vc3 = st.columns([1, 1, 1])
    with vc1:
        x_axis = st.selectbox("X-Axis Feature", df.columns, index=0)
    with vc2:
        y_axis = st.selectbox("Y-Axis Feature", ["None"] + list(df.columns), index=1 if len(df.columns) > 1 else 0)
    with vc3:
        color_by = st.selectbox("Segment / Color By", ["None"] + list(df.columns))

    plot_kind = st.selectbox("Visual Paradigm", ["Scatter / Correlation", "Box & Distribution", "Histogram", "Violin Plot"])
    
    color_param = None if color_by == "None" else color_by
    y_param = None if y_axis == "None" else y_axis

    if plot_kind == "Scatter / Correlation" and y_param:
        fig = px.scatter(df, x=x_axis, y=y_param, color=color_param, template="plotly_dark", trendline="ols" if not color_param and x_axis in numeric_cols and y_param in numeric_cols else None)
    elif plot_kind == "Box & Distribution":
        fig = px.box(df, x=x_axis, y=y_param, color=color_param, template="plotly_dark")
    elif plot_kind == "Histogram":
        fig = px.histogram(df, x=x_axis, color=color_param, template="plotly_dark", marginal="rug")
    elif plot_kind == "Violin Plot":
        fig = px.violin(df, x=x_axis, y=y_param, color=color_param, box=True, template="plotly_dark")
    else:
        fig = go.Figure()
        st.warning("Select valid pairings to render.")

    st.plotly_chart(fig, width='stretch')

    if len(numeric_cols) > 1:
        st.markdown("**Correlation Matrix Heatmap**")
        corr = df[numeric_cols].corr()
        corr_fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(corr_fig, width='stretch')

# ----------------- TAB 4: AUTOML MODEL ARENA -----------------
with tab_automl:
    st.subheader("Model Tournament Arena")
    st.caption("Benchmarking algorithms side-by-side with out-of-fold generalization.")

    target = st.selectbox("Target Variable (Prediction Objective):", options=df.columns)
    
    if st.button("🚀 Initiate Tournament"):
        with st.spinner("Preparing data and benchmarking models..."):
            work_df = df.dropna(subset=[target]).copy()
            y_raw = work_df[target]
            X_raw = work_df.drop(columns=[target])
            
            # Auto-encode inputs
            X = pd.get_dummies(X_raw, drop_first=True)
            X = X.fillna(X.median(numeric_only=True))

            is_classification = (y_raw.dtype == 'object') or (y_raw.nunique() <= 10)
            
            if is_classification:
                # Target encoding
                y = pd.factorize(y_raw)[0]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y if len(np.unique(y)) > 1 else None)
                
                models = {
                    "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
                    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
                    "Logistic Regression": LogisticRegression(max_iter=500)
                }

                results = []
                fitted_models = {}
                for name, mdl in models.items():
                    mdl.fit(X_train, y_train)
                    preds = mdl.predict(X_test)
                    acc = accuracy_score(y_test, preds)
                    f1 = f1_score(y_test, preds, average="weighted")
                    results.append({"Model": name, "Accuracy": round(acc, 4), "F1-Score": round(f1, 4)})
                    fitted_models[name] = mdl
                
                res_df = pd.DataFrame(results).sort_values("F1-Score", ascending=False)
                st.dataframe(res_df, width='stretch')
                best_model_name = res_df.iloc[0]["Model"]
                best_model = fitted_models[best_model_name]

            else:
                y = y_raw.astype(float)
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
                
                models = {
                    "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42),
                    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
                    "Ridge Regression": Ridge()
                }

                results = []
                fitted_models = {}
                for name, mdl in models.items():
                    mdl.fit(X_train, y_train)
                    preds = mdl.predict(X_test)
                    r2 = r2_score(y_test, preds)
                    rmse = np.sqrt(mean_squared_error(y_test, preds))
                    results.append({"Model": name, "R² Score": round(r2, 4), "RMSE": round(rmse, 4)})
                    fitted_models[name] = mdl
                
                res_df = pd.DataFrame(results).sort_values("R² Score", ascending=False)
                st.dataframe(res_df, width='stretch')
                best_model_name = res_df.iloc[0]["Model"]
                best_model = fitted_models[best_model_name]

            # Top Features Display
            if hasattr(best_model, "feature_importances_"):
                st.subheader(f"Top Predictors ({best_model_name})")
                importances = pd.Series(best_model.feature_importances_, index=X.columns).sort_values(ascending=True).tail(12)
                fig_imp = px.bar(importances, orientation='h', template="plotly_dark", title="Feature Relative Importance", labels={'value': 'Importance Coefficient', 'index': 'Feature'})
                st.plotly_chart(fig_imp, width='stretch')