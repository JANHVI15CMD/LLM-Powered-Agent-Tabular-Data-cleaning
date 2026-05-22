import streamlit as st
import pandas as pd

def render_preview(df_original, df_cleaned):
    """Enhanced preview with CORRECT visual comparisons."""

    if df_original is None or df_cleaned is None:
        st.info(" Upload a file and run a cleaning instruction to see the comparison")
        return

    # -------------------------
    # Correct Calculations
    # -------------------------
    rows_before = len(df_original)
    rows_after = len(df_cleaned)
    rows_removed = rows_before - rows_after

    cols_before = len(df_original.columns)
    cols_after = len(df_cleaned.columns)
    cols_removed = cols_before - cols_after

    nulls_before = df_original.isnull().sum().sum()
    nulls_after = df_cleaned.isnull().sum().sum()
    nulls_reduced = nulls_before - nulls_after

    memory_before = df_original.memory_usage(deep=True).sum() / 1024**2
    memory_after = df_cleaned.memory_usage(deep=True).sum() / 1024**2
    memory_reduced = memory_before - memory_after

    # -------------------------
    # Metrics Row
    # -------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Rows After", f"{rows_after:,}", delta=f"-{rows_removed:,}" if rows_removed > 0 else f"+{abs(rows_removed):,}")

    with col2:
        st.metric("Columns After", cols_after, delta=f"-{cols_removed}" if cols_removed > 0 else f"+{abs(cols_removed)}")

    with col3:
        st.metric("Null Values After", f"{nulls_after:,}", delta=f"-{nulls_reduced:,}")

    with col4:
        st.metric("Memory After (MB)", f"{memory_after:.2f}", delta=f"-{memory_reduced:.2f}")

    # -------------------------
    # Side-by-side preview
    # -------------------------
    left, right = st.columns(2)

    with left:
        st.markdown("####  Original Dataset")
        st.dataframe(df_original.head(15), use_container_width=True)
        st.caption(f"Showing 15 of {rows_before:,} rows")

    with right:
        st.markdown("####  Cleaned Dataset")
        st.dataframe(df_cleaned.head(15), use_container_width=True)
        st.caption(f"Showing 15 of {rows_after:,} rows")

    # -------------------------
    # Schema Comparison
    # -------------------------
    with st.expander(" Schema Changes"):
        original_cols = set(df_original.columns)
        cleaned_cols = set(df_cleaned.columns)

        removed_cols = original_cols - cleaned_cols
        added_cols = cleaned_cols - original_cols

        if removed_cols:
            st.error(f"**Removed columns:** {', '.join(removed_cols)}")
        if added_cols:
            st.success(f"**Added columns:** {', '.join(added_cols)}")
        if not removed_cols and not added_cols:
            st.info("✓ No schema changes")

        # Data type changes
        dtype_changes = []
        for col in original_cols & cleaned_cols:
            if df_original[col].dtype != df_cleaned[col].dtype:
                dtype_changes.append(f"**{col}**: {df_original[col].dtype} → {df_cleaned[col].dtype}")

        if dtype_changes:
            st.warning("**Data type changes:**")
            for change in dtype_changes:
                st.markdown(f"- {change}")
