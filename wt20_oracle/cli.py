"""
CLI Entry Point
===============

Usage:
  python -m wt20_oracle.cli prematch --opponent south_africa --venue lords
  python -m wt20_oracle.cli prematch --opponent australia --venue edgbaston --toss-winner india --toss-decision bowl_first
  python -m wt20_oracle.cli prematch --opponent pakistan --venue old_trafford --format json
"""

import json
import sys
import argparse

from wt20_oracle.pre_match_graph import run_pre_match_pipeline

DEFAULT_TEAM = "india"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wt20-oracle",
        description="Decision-support system for India Women T20 World Cup 2026",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pm = subparsers.add_parser("prematch", help="Pre-match analysis and recommendations")
    pm.add_argument("--opponent", required=True, help="Opponent team ID (e.g. australia)")
    pm.add_argument(
        "--venue",
        default=None,
        help="Venue ID (e.g. lords, edgbaston). Auto-fetch if omitted with future date.",
    )
    pm.add_argument("--team", default=DEFAULT_TEAM, help=f"Our team (default: {DEFAULT_TEAM})")
    pm.add_argument("--date", default="", help="Match date YYYY-MM-DD")
    pm.add_argument("--toss-winner", default=None, dest="toss_winner",
                    help="Team ID of toss winner. Omit if unknown.")
    pm.add_argument("--toss-decision", default=None, dest="toss_decision",
                    choices=["bat_first", "bowl_first"],
                    help="Toss decision: bat_first or bowl_first")
    pm.add_argument("--format", default="text", choices=["text", "json"])
    pm.add_argument("--verbose", action="store_true")
    pm.add_argument(
        "--fetch",
        action="store_true",
        help="Force internet search for match details (auto for future matches)",
    )
    pm.add_argument(
        "--no-confirm",
        action="store_true",
        help="Auto-confirm venue additions (skip interactive prompts)",
    )
    return parser


def run_prematch(args):
    print(f"\nPre-match: {args.team.upper()} vs {args.opponent.upper()}")
    if args.venue:
        print(f"Venue: {args.venue}")
    if args.toss_winner:
        print(f"Toss: {args.toss_winner} chose to {(args.toss_decision or '?').replace('_', ' ')}")
    else:
        print("Toss: not yet known")
    print()

    # ──────────────────────────────────────────────────────────────────────────
    # SMART DATA FETCHING: Auto-fetch for future matches, explicit --fetch otherwise
    # ──────────────────────────────────────────────────────────────────────────
    from wt20_oracle.data_fetcher import (
        should_auto_fetch,
        fetch_match_details,
        update_venues_json_with_confirmation,
    )

    venue_to_use = args.venue
    if not venue_to_use:
        should_fetch = should_auto_fetch(args.date, args.venue) or args.fetch

        if should_fetch:
            print("🔍 Searching for match details...")
            fetch_result = fetch_match_details(
                args.team, args.opponent, args.date, force_fetch=args.fetch
            )

            if fetch_result.get("cached"):
                print("  (using cached result)")

            if fetch_result["status"] in ["success", "partial"]:
                print(f"  ✓ Found: {fetch_result['venue_name']}")

                if fetch_result.get("requires_confirmation"):
                    if fetch_result.get("venue_to_add"):
                        if not args.no_confirm:
                            if not update_venues_json_with_confirmation(
                                fetch_result["venue_to_add"]
                            ):
                                print("  Proceeding without updating database...")
                        else:
                            # Auto-confirm
                            update_venues_json_with_confirmation(fetch_result["venue_to_add"])

                venue_to_use = fetch_result["venue_id"]
            else:
                print(f"  ✗ {fetch_result['message']}")
                print("  Please provide --venue manually")
                return 1
        else:
            print("❌ Venue required. Provide --venue or use --fetch for future matches")
            return 1

    # ──────────────────────────────────────────────────────────────────────────
    # RUN PIPELINE with validation & error handling
    # ──────────────────────────────────────────────────────────────────────────
    try:
        state = run_pre_match_pipeline(
            team_id=args.team,
            opponent_id=args.opponent,
            venue_id=venue_to_use,
            match_date=args.date,
            toss_winner=args.toss_winner,
            toss_decision=args.toss_decision,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Hard fail on validation errors
    if state.get("errors"):
        for err in state.get("errors", []):
            print(f"❌ ERROR: {err}", file=sys.stderr)
        return 1

    # Show warnings
    for warn in state.get("warnings", []):
        print(f"⚠️  WARNING: {warn}")

    if args.format == "json":
        _print_json(state)
    else:
        _print_text(state, verbose=args.verbose)

    return 0


def _print_text(state, verbose=False):
    print(state.get("strategy_brief", "(No strategy brief generated)"))

    if verbose:
        print("\n── DETAILED OUTPUT ──────────────────────────────────────────────────")
        selected = state.get("selected_xi", [])
        print(f"\nSELECTED XI ({len(selected)} players):")
        for pid in selected:
            print(f"  {pid}")

        order = state.get("batting_order", [])
        reasoning = state.get("batting_reasoning", {})
        if order:
            print("\nBATTING ORDER:")
            for pos, pid in enumerate(order, 1):
                print(f"  {pos:2}. {pid:<30} {reasoning.get(pid, '')}")

        plan = state.get("bowling_plan", [])
        if plan:
            print("\nBOWLING PLAN:")
            for entry in plan:
                econ = entry.get("economy")
                econ_str = f"econ {econ:.1f}" if econ else ""
                print(f"  {entry.get('player_name', entry.get('player_id')):<25} "
                      f"{entry.get('phase', '?'):<12} {econ_str}")

        sr = state.get("scenario_report", {})
        print(f"\nSCENARIO: {sr.get('message', state.get('scenario', '?'))}")
        adj = state.get("adjusted_runs_estimate")
        lo = state.get("runs_lower")
        hi = state.get("runs_upper")
        if adj:
            print(f"Runs estimate: {adj:.0f} ({lo:.0f}–{hi:.0f})")
        wp = state.get("win_probability")
        if wp is not None:
            print(f"Win probability: {wp:.0%}")


def _print_json(state):
    output = {
        "team": state.get("team_id"),
        "opponent": state.get("opponent_id"),
        "venue": state.get("venue_id"),
        "scenario": state.get("scenario"),
        "pitch_difficulty": state.get("pitch_difficulty"),
        "chase_penalty": state.get("chase_penalty"),
        "selected_xi": state.get("selected_xi", []),
        "batting_order": state.get("batting_order", []),
        "bowling_plan": state.get("bowling_plan", []),
        "runs_estimate": {
            "base": state.get("base_runs_estimate"),
            "adjusted": state.get("adjusted_runs_estimate"),
            "lower": state.get("runs_lower"),
            "upper": state.get("runs_upper"),
        },
        "win_probability": state.get("win_probability"),
        "strategy_brief": state.get("strategy_brief"),
        "key_matchups": state.get("key_matchups", []),
        "tactical_flags": state.get("tactical_flags", []),
        "scenario_report": state.get("scenario_report", {}),
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
    }
    print(json.dumps(output, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "prematch":
        return run_prematch(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
