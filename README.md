# AI/ML Algorithmic Trading System for Short-Term Equities

this projects resides in a private repo

## Overview

This project implements a trading system that blends quantitative analysis with real-time Artificial Intelligence (AI) and Natural Language Processing (NLP) to identify and capitalize on short-term equity opportunities. It's designed as a hybrid system, potentially allowing for both automated execution and manual oversight.

## Core Components

### 1. Quantitative Analysis Pipeline

An end-to-end Python-based pipeline forms the backbone of the quantitative analysis. This component, primarily managed by `backend/quant_pipelineV2/orchestrate_analysis.py`, involves:

*   **Calculates Key Metrics:** Computes a range of technical indicators, quantitative statistics (Quant Stats), and support/resistance levels (e.g., 20-day and 50-day moving averages).
    *   Core logic resides in modules within `backend/quant_pipelineV2/` (e.g., `quant_stats_priceAction.py`, `reversal_rank.py`, `rank_momentum.py`, `bullish_divergence.py`).
*   **Data Storage & Retrieval:** Stores all calculated data efficiently in an SQLite database (`data/market_data.db`, with setup managed via `backend/research_agent/database_setup.py`) for rapid access and analysis.
    *   Data loading for the pipeline is handled by `backend/quant_pipelineV2/data_loader.py`.

### 2. AI-Powered News Analysis & Summarization

The system integrates cutting-edge Large Language Models (LLMs) like OpenAI's GPT and Google's Gemini Flash to process and understand financial news:

*   **Real-time News Processing:** Identifies and summarizes the five most relevant news stories for each targeted ticker within a 24-48 hour window.
    *   News sources are scraped by modules such as `backend/news_scraping/finnhub_scrape.py` and `backend/research_agent/yahoofin_scraper.py`.
*   **Sentiment & Summaries:** Generates sentiment scores (positive, negative, neutral) and concise summaries from the news articles in seconds.
    *   This processing is likely orchestrated within the `backend/research_agent/` (e.g., by `data_processor.py`).
    *   Outputs of this stage, like summaries and sentiment, may be cached or logged (e.g., `data/premarket_analysis_cache.json`, `data/decision_output.json`).

### 3. Open AI Gpt-4o & Google Gemini Flash 2.5  web-search Event Catalyst

To capture market-moving information that might be missed by standard news summaries, the system features an "event-catalyst" powered by LLM web-search capabilities:

*   **Proactive Information Gathering:** Conducts real-time sweeps of vetted news feeds and online sources to uncover fresh, price-moving events, looking ahead up to 30 days.
*   **Bridging Insight Gaps:** This proactive search complements the primary news summarization, aiming to capture a broader range of catalysts that traditional scraping methods might overlook. It ensures that crucial information beyond the top five summarized articles is considered.

## Conceptual Workflow & Orchestration

The overall process can be conceptualized as follows:

1.  **Data Ingestion & Quantitative Analysis:** Market data is loaded (`backend/research_agent/yahoofin_scrape,py`), and the quantitative pipeline (`backend/quant_pipelineV2/`) calculates technicals, stats, and levels, storing them in the SQLite DB.
2.  **News Aggregation & LLM Summarization:** News articles are scraped using Finnhub API (`backend/news_scraping/`). LLMs process these to summarize key stories and derive sentiment.
3.  **Event Catalyst Search:** LLMs perform broader web searches for additional event-driven catalysts, enhancing the news analysis.
4.  **Signal Fusion:** Quantitative signals are combined with NLP-derived insights (summaries, sentiment, event catalysts).
5.  **Opportunity Identification:** The fused data helps identify potential short-term trading opportunities, with outputs possibly logged in `data/decision_output.json`.

The overall orchestration of these components is orchestrated and managed by a central script, such as `backend/main.py`.

## Technologies used

*   **Programming Language:**
    *   Python
*   **Artificial Intelligence & Machine Learning:**
    *   Large Language Models (LLMs):
        *   Google Gemini Flash
        *   OpenAI GPT-4o
    *   Natural Language Processing (NLP) techniques
    *   PyTorch (FinBert sentiment analysis)
*   **Data Storage:**
    *   SQLite
*   **Data Formats:**
    *   JSON
*   **Key Python Libraries & Frameworks (Inferred):**
    *   `pandas` (for data manipulation and analysis)
    *   `numpy` (for numerical computations)
    *   `SciPy` (Quant Stata price action)
    *   `requests` (for HTTP requests - API interaction, web scraping)
    *   `SQLAlchemy` or Python's built-in `sqlite3` (for SQLite database interaction)
    *   API client libraries for OpenAI, Google Gemini, Finnhub, Yahoo Finance
    *   Technical analysis libraries (e.g., `TA-Lib`, `pandas_ta`, or custom implementations)
*   **Development Tools:**
    *   Git (for version control)
*   **External APIs & Data Sources:**
    *   Finnhub API
    *   Yahoo Finance API/Data