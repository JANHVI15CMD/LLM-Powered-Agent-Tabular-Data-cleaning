# Autonomous LLM Agent for Data Cleaning

## Overview
This project implements an autonomous LLM-based agent for cleaning datasets using natural language instructions. It leverages Streamlit for the UI, Pandas for data manipulation, and OpenAI for code generation.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set `OPENAI_API_KEY` env var.
3. Run: `streamlit run app.py`

## Research Focus
- Autonomy: LLM generates and self-corrects Pandas code.
- Evaluation: Use `experiments/` for benchmarks (e.g., UCI datasets).
- Metrics: Cleaning accuracy, error correction rate, user satisfaction.

## Folder Structure
[As provided in the query]

## Usage
1. Upload CSV to `data/raw/`.
2. Enter NL instruction (e.g., "Remove duplicates based on email column").
3. View preview, logs, and download cleaned CSV.

