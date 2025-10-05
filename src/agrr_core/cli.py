"""CLI application entry point."""

import asyncio
import sys
from typing import Optional

from agrr_core.framework.agrr_core_container import WeatherCliContainer


def main() -> None:
    """Main entry point for CLI application."""
    try:
        # Create container with configuration
        config = {
            'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive'
        }
        container = WeatherCliContainer(config)
        
        # Get command line arguments (excluding script name)
        args = sys.argv[1:] if len(sys.argv) > 1 else None
        
        # Run CLI application
        asyncio.run(container.run_cli(args))
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        try:
            print(f"\n❌ Unexpected error: {e}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
