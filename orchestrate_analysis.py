import sys
import os
from pathlib import Path # <-- Add Path import
import logging
import json
import pandas as pd


# --- Path Setup ---
# Dynamically add the project root to sys.path if running directly
# This allows finding the 'backend' package for absolute imports.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# --- End Path Setup ---


# --- Import processing, ranking and display functions ---
from backend.quant_pipelineV2.rank_momentum import get_processed_momentum_results, display_ranking_results as display_momentum_results
# Import reversal processing, ranking and display functions
from backend.quant_pipelineV2.reversal_rank import get_processed_reversal_results, display_ranking_results as display_reversal_results
from backend.quant_pipelineV2.momentum_analysis.momentum_analysis import run_momentum_analysis
# --- Import Quant Stats Function ---
from backend.quant_pipelineV2.quant_stats_priceAction import generate_signal_report
# --- Indicator Constants no longer needed here ---


# --- Configuration ---
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data')
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'quant_pipelinev2.json')
# --- Database Path ---
DB_DIR = Path(PROJECT_ROOT) / "data"
DB_PATH = DB_DIR / "market_data.db"
# --- Quant Config (Only needed for generate_signal_report) ---
QUANT_HORIZONS = [3, 5, 10, 14] # Horizons for quant analysis
QUANT_SUCCESS_THRESHOLD = 0.04 # Success threshold (e.g., 4%)
# --- Top N Config ---
TOP_N_MOMENTUM = 10
TOP_N_REVERSAL = 5
# --- Thresholds and Weights are now handled within rank_*.py modules ---
# MOMENTUM_SCORE_THRESHOLD = 6.0
# MIN_MATCHES_THRESHOLD = 10
# MOMENTUM_COMPOSITE_WEIGHTS = { ... }
# REVERSAL_COMPOSITE_WEIGHTS = { ... }

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def orchestrate():
    """
    Orchestrates the quantitative analysis pipeline.
    1. Runs momentum analysis (fetches data, calculates indicators).
    2. Generates quant stats report.
    3. Processes momentum signals (ranks, merges, filters, scores, describes).
    4. Processes reversal signals (ranks, merges, filters, scores, describes).
    5. Displays the top processed results for both momentum and reversal.
    6. Saves the *initial* top ranking results (pre-processing) to a JSON file.
    """
    logger.info("Starting quantitative analysis orchestration...")

    all_indicator_data = None
    quant_report_df = None
    momentum_display_df = None # For final display data
    reversal_display_df = None # For final display data
    initial_momentum_ranked_data = None # Keep for JSON save
    initial_reversal_ranked_data = None # Keep for JSON save

    try:
        # 1. Run Momentum Analysis (includes indicators and divergences)
        logger.info("Running momentum analysis (fetch, indicators, divergences)...")
        # Assumes run_momentum_analysis returns all_indicator_data with MultiIndex [symbol, date]
        # and date level is datetime.date or compatible.
        _, all_indicator_data = run_momentum_analysis()

        if all_indicator_data is None or all_indicator_data.empty:
            logger.warning("Momentum analysis did not return indicator data. Stopping.")
            return
        # Basic index check (more robust checks happen inside processing functions)
        if not isinstance(all_indicator_data.index, pd.MultiIndex) or len(all_indicator_data.index.names) != 2:
            logger.error("all_indicator_data does not have the expected MultiIndex. Stopping.")
            return

        logger.info("Momentum analysis completed successfully.")

        # 2. Generate Quant Stats Report
        logger.info("Generating quant statistics report...")
        try:
            quant_report_df = generate_signal_report(
                db_path=DB_PATH,
                future_horizons=QUANT_HORIZONS,
                success_threshold=QUANT_SUCCESS_THRESHOLD
            )
            if quant_report_df is None or quant_report_df.empty:
                 logger.warning("Quant report generation returned empty or failed.")
                 quant_report_df = pd.DataFrame() # Ensure it's an empty DF
            else:
                 logger.info(f"Quant report generated with {len(quant_report_df)} entries.")
        except Exception as e:
            logger.error(f"Error during generate_signal_report: {e}", exc_info=True)
            quant_report_df = pd.DataFrame() # Ensure empty DF on error

        # --- Process Signals (using dedicated functions from rank_*.py) ---

        # 3. Process Momentum Signals
        logger.info(f"Processing top {TOP_N_MOMENTUM} momentum signals...")
        try:
            momentum_display_df = get_processed_momentum_results(
                all_indicator_data=all_indicator_data,
                quant_report_df=quant_report_df,
                top_n=TOP_N_MOMENTUM
                # Uses default thresholds defined in rank_momentum.py
            )
            if momentum_display_df.empty:
                 logger.warning("Momentum processing returned no displayable results.")
            else:
                 logger.info(f"Momentum processing complete. Found {len(momentum_display_df)} signals for display.")
        except Exception as e:
            logger.error(f"Error processing momentum signals: {e}", exc_info=True)
            momentum_display_df = pd.DataFrame() # Ensure empty on error

        # 4. Process Reversal Signals
        logger.info(f"Processing top {TOP_N_REVERSAL} reversal signals...")
        try:
            reversal_display_df = get_processed_reversal_results(
                all_indicator_data=all_indicator_data,
                quant_report_df=quant_report_df,
                top_n=TOP_N_REVERSAL
                # Uses default thresholds defined in reversal_rank.py
            )
            if reversal_display_df.empty:
                 logger.warning("Reversal processing returned no displayable results.")
            else:
                 logger.info(f"Reversal processing complete. Found {len(reversal_display_df)} signals for display.")
        except Exception as e:
            logger.error(f"Error processing reversal signals: {e}", exc_info=True)
            reversal_display_df = pd.DataFrame() # Ensure empty on error

        # 5. Display Results
        if not momentum_display_df.empty:
            logger.info("Displaying top momentum ranking results...")
            display_momentum_results(momentum_display_df)
        else:
            logger.info("No momentum results to display.")

        if not reversal_display_df.empty:
            logger.info("Displaying top reversal ranking results...")
            display_reversal_results(reversal_display_df)
        else:
            logger.info("No reversal results to display.")

        # 6. Save *initial* results to JSON (Requires re-running initial rank)
        # We need the initial ranks just for saving, as requested.
        logger.info("Re-running initial ranking for JSON save...")
        try:
            from backend.quant_pipelineV2.rank_momentum import rank_momentum_signals as initial_rank_momentum
            from backend.quant_pipelineV2.reversal_rank import rank_reversal_signals as initial_rank_reversal

            initial_momentum_ranked_data = initial_rank_momentum(all_indicator_data)
            initial_reversal_ranked_data = initial_rank_reversal(all_indicator_data)
        except Exception as rank_err:
            logger.error(f"Error re-running initial ranking for JSON save: {rank_err}")
            initial_momentum_ranked_data = None
            initial_reversal_ranked_data = None

        if (initial_momentum_ranked_data is not None and not initial_momentum_ranked_data.empty) or \
           (initial_reversal_ranked_data is not None and not initial_reversal_ranked_data.empty):

            logger.info(f"Attempting to save *initial* ranking results to {JSON_OUTPUT_PATH}...")
            try:
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                output_dict = {}

                if isinstance(initial_momentum_ranked_data, pd.DataFrame) and not initial_momentum_ranked_data.empty:
                    momentum_top = initial_momentum_ranked_data.head(TOP_N_MOMENTUM)
                    momentum_for_json = momentum_top.reset_index()
                    output_dict["rank_momentum_signals"] = momentum_for_json.to_dict(orient="records")
                    logger.info(f"Prepared top {TOP_N_MOMENTUM} *initial* momentum signals for JSON.")
                else:
                    logger.info("No initial momentum data to save to JSON.")

                if isinstance(initial_reversal_ranked_data, pd.DataFrame) and not initial_reversal_ranked_data.empty:
                    reversal_top = initial_reversal_ranked_data.head(TOP_N_REVERSAL)
                    reversal_for_json = reversal_top.reset_index()
                    output_dict["rank_reversal_signals"] = reversal_for_json.to_dict(orient="records")
                    logger.info(f"Prepared top {TOP_N_REVERSAL} *initial* reversal signals for JSON.")
                else:
                     logger.info("No initial reversal data to save to JSON.")

                if output_dict:
                    with open(JSON_OUTPUT_PATH, 'w') as f:
                        json.dump(output_dict, f, indent=4, default=str)
                    logger.info(f"Successfully saved *initial* ranking results to {JSON_OUTPUT_PATH}.")
                else:
                    logger.info("No initial ranking data was generated to save.")

            except Exception as json_e:
                logger.error(f"Failed to save initial results to JSON: {json_e}", exc_info=True)
        else:
             logger.info("No initial ranking data was generated. Skipping JSON save.")

        logger.info("Quantitative analysis orchestration finished.")

    except Exception as e:
        logger.error(f"An error occurred during orchestration: {e}", exc_info=True)


if __name__ == "__main__":
    orchestrate()
