import streamlit as st


def render_header() -> None:
    st.title("Code Archaeologist")
    st.markdown("Analyze Python execution traces and visualize relationships between functions.")


def render_summary_card(title: str, value: str) -> None:
    st.metric(label=title, value=value)


def render_help() -> None:
    st.info("Upload a Python file or paste code, then click Analyze to build the trace graph.")
