from engine.scanner import run_scan

if __name__ == "__main__":
    result = run_scan()
    print(f"\nScanned {result['pairs_scanned']} pairs | {result['setups_found']} setups\n")

    for scored in result["setups"][:10]:
        s = scored.setup
        print(f"{s.pair:8} {s.direction.upper():5} {s.timeframe:3} | "
              f"score {scored.score}/10 | entry {s.entry:.5f} | "
              f"SL {s.stop_loss:.5f} | TP {s.take_profit:.5f} | RR 1:{s.rr_ratio}")