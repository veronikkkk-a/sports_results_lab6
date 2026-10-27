"""Command-line entry point."""
import argparse
import logging
import sys
from itertools import islice
from pathlib import Path
from sports_streaming.config import load_config
from sports_streaming.exceptions import ApplicationError, RecordValidationError
from sports_streaming.exporters import export_errors, export_json
from sports_streaming.logging_config import configure_logging
from sports_streaming.services import ImportStatistics, import_results, logged_operation

def main() -> None:
    parser = argparse.ArgumentParser(description="Stream and validate sports CSV results")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--limit", type=int, help="Process at most N CSV records")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        configure_logging(config.log_level, config.log_path)
        stats = ImportStatistics()
        errors: list[dict[str, object]] = []
        records = import_results(config, stats, errors)
        if args.limit is not None:
            if args.limit < 0:
                raise ApplicationError("--limit must be non-negative")
            records = islice(records, args.limit)
        with logged_operation("Sports results import/export"):
            exported = export_json(records, config.output_path)
            export_errors(errors, config.error_path)
        logger = logging.getLogger(__name__)
        logger.info("Total=%d valid=%d invalid=%d exported=%d", stats.total, stats.valid, stats.invalid, exported)
        for sport, total in sorted(stats.result_sums.items()):
            best = stats.best_by_sport[sport]
            average = total / stats.result_counts[sport]
            logger.info("%s: count=%d average=%.4f best numeric record=%s (%.4f)",
                        sport, stats.result_counts[sport], average, best.athlete, best.result)
    except RecordValidationError as error:
        export_errors(errors, config.error_path)
        logging.getLogger(__name__).error("Strict validation stopped import: %s", error)
        raise SystemExit(1) from error
    except ApplicationError as error:
        logging.getLogger(__name__).error("Application error: %s", error)
        raise SystemExit(1) from error
    except OSError:
        logging.getLogger(__name__).exception("Unexpected file I/O failure")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
