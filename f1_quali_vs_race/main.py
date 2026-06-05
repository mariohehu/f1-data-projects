"""
CLI: python main.py --season 2023
     python main.py --season 2022 2023
     python main.py --season 2023 --race "Monaco Grand Prix"
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import fastf1

from loader import load_session, get_best_quali_times, get_clean_race_pace, has_rain, get_race_list
from pace_analysis import calculate_hidden_pace, aggregate_by_team
from team_mapping import get_team
from visualizer import plot_scatter, plot_team_bar, plot_heatmap


def run_season(season: int, race_filter: str | None = None):
    print(f"\n{'='*50}")
    print(f"  Analysing season {season}")
    print(f"{'='*50}")

    races = get_race_list(season)
    if race_filter:
        races = [r for r in races if race_filter.lower() in r.lower()]

    all_results = []

    for race in races:
        print(f"\n  → {race}")

        try:
            q_session = load_session(season, race, "Q")
            r_session = load_session(season, race, "R")
        except Exception as e:
            print(f"     Failed to load: {e}")
            continue

        if has_rain(r_session):
            print("     Skipped (rain race)")
            continue

        try:
            quali_df = get_best_quali_times(q_session)
            race_df = get_clean_race_pace(r_session)
            result = calculate_hidden_pace(quali_df, race_df, race, season)
            if result.empty:
                print("     No matching drivers")
                continue
        except Exception as e:
            print(f"     Analysis failed: {e}")
            continue

        result["Team"] = result["Driver"].apply(lambda d: get_team(d, season))

        # per-race scatter plot
        try:
            plot_scatter(result, race, season)
            print(f"     Scatter saved")
        except Exception as e:
            print(f"     Scatter error: {e}")

        all_results.append(result)

    if not all_results:
        print("No data collected.")
        return

    df = pd.concat(all_results, ignore_index=True)

    print(f"\n  Total races analysed: {df['Race'].nunique()}")
    print(f"  Total driver-race rows: {len(df)}")

    team_summary = aggregate_by_team(df)
    print("\n  Team Hidden Pace Summary:")
    print(team_summary.to_string(index=False))

    # team bar chart
    try:
        plot_team_bar(team_summary, season)
        print(f"\n  Team bar chart saved")
    except Exception as e:
        print(f"  Team bar error: {e}")

    # heatmap
    try:
        plot_heatmap(df, season)
        print(f"  Heatmap saved")
    except Exception as e:
        print(f"  Heatmap error: {e}")

    output_csv = Path(__file__).parent / "output" / f"hidden_pace_{season}.csv"
    output_csv.parent.mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"\n  CSV saved to {output_csv}")

    return df


def main():
    parser = argparse.ArgumentParser(description="F1 Qualifying vs Race Pace Analysis")
    parser.add_argument("--season", type=int, nargs="+", default=[2023],
                        help="Season(s) to analyse (e.g. --season 2022 2023)")
    parser.add_argument("--race", type=str, default=None,
                        help="Filter by race name substring (e.g. --race Monaco)")
    args = parser.parse_args()

    all_data = []
    for season in args.season:
        df = run_season(season, race_filter=args.race)
        if df is not None:
            all_data.append(df)

    if len(args.season) > 1 and all_data:
        combined = pd.concat(all_data, ignore_index=True)
        multi_output = Path(__file__).parent / "output" / "hidden_pace_combined.csv"
        combined.to_csv(multi_output, index=False)
        print(f"\nCombined CSV saved to {multi_output}")


if __name__ == "__main__":
    main()
