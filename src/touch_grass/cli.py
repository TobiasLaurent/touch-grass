from __future__ import annotations

import json
import random
import sys

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from touch_grass import conditions
from touch_grass.conditions import evaluate_current, find_next_safe_window, forecast_days
from touch_grass.config import has_user_thresholds, load_thresholds, run_first_time_setup
from touch_grass.location import get_location
from touch_grass.weather import get_air_quality, get_weather

console = Console()

NUDGES = [
    "The mass of grass is calling your name.",
    "Your IDE will still be here when you get back.",
    "Even Linus Torvalds goes outside sometimes.",
    "Fresh air is the best debugger.",
    "Touch grass. Commit later.",
]


def _status_dot(safe: bool) -> str:
    return "[green]●[/green]" if safe else "[red]●[/red]"


@click.command()
@click.option("--lat", type=float, default=None, help="Latitude (skips IP geolocation)")
@click.option("--lon", type=float, default=None, help="Longitude (skips IP geolocation)")
@click.option("--config", "config_path", default=None, help="Path to JSON config file with custom thresholds")
@click.option("--configure", is_flag=True, help="Run interactive threshold setup")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON")
@click.option("--plan", type=click.Choice(["next-24h"]), default=None, help="Planning mode")
@click.option("--forecast", type=click.IntRange(1, 7), default=None, help="Return a day-by-day forecast for the next N days")
def main(lat: float | None, lon: float | None, config_path: str | None, configure: bool, json_output: bool, plan: str | None, forecast: int | None):
    """Check if it's safe to go outside and touch grass."""
    try:
        # Load thresholds (first-run setup, config file and/or env vars)
        try:
            if configure:
                thresholds = run_first_time_setup()
            elif config_path is None and not has_user_thresholds() and sys.stdin.isatty():
                thresholds = run_first_time_setup()
            else:
                thresholds = load_thresholds(config_path)
            conditions.apply_thresholds(thresholds)
        except FileNotFoundError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            raise SystemExit(30)
        except ValueError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            raise SystemExit(30)
        except OSError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            raise SystemExit(30)

        # Location
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90):
                raise click.BadParameter(f"Latitude must be between -90 and 90, got {lat}")
            if not (-180 <= lon <= 180):
                raise click.BadParameter(f"Longitude must be between -180 and 180, got {lon}")
            location = {"city": "Custom", "region": "", "country": "", "latitude": lat, "longitude": lon}
        else:
            with console.status("[dim]Finding your location...[/dim]"):
                location = get_location()

        city_parts = [location["city"]]
        if location["region"]:
            city_parts.append(location["region"])
        if location["country"]:
            city_parts.append(location["country"])
        location_str = ", ".join(city_parts)

        forecast_days_requested = forecast if forecast is not None else 1

        # Fetch data
        with console.status("[dim]Checking conditions...[/dim]"):
            weather = get_weather(location["latitude"], location["longitude"], forecast_days=forecast_days_requested)
            air_quality = get_air_quality(location["latitude"], location["longitude"], forecast_days=forecast_days_requested)

        # Evaluate
        result = evaluate_current(weather, air_quality)
        next_window = find_next_safe_window(weather, air_quality)
        forecast_summary = forecast_days(weather, air_quality, forecast) if forecast else None

        if json_output:
            payload = {
                "safe": result["safe"],
                "location": {
                    "city": location.get("city"),
                    "region": location.get("region"),
                    "country": location.get("country"),
                    "latitude": location.get("latitude"),
                    "longitude": location.get("longitude"),
                },
                "checks": result["checks"],
                "next_safe_window": next_window,
                "thresholds": thresholds,
                "plan": plan,
            }
            if forecast_summary is not None:
                payload["forecast_days"] = forecast_summary
                payload["forecast_count"] = forecast
            click.echo(json.dumps(payload, ensure_ascii=False))
            raise SystemExit(0 if result["safe"] else 10)

        # Display
        console.print()
        console.print(f"[bold]📍 {location_str}[/bold]")
        console.print()

        # Conditions table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("status", width=2)
        table.add_column("condition")

        for check in result["checks"]:
            table.add_row(_status_dot(check["safe"]), check["reason"])

        console.print(table)
        console.print()

        if plan == "next-24h":
            if next_window:
                console.print(Panel(f"[bold cyan]Best next window[/bold cyan]\n\n[dim]{next_window}[/dim]", border_style="cyan"))
            else:
                console.print(Panel("[bold red]No safe window in next 24h.[/bold red]", border_style="red"))

        # Verdict
        if result["safe"]:
            nudge = random.choice(NUDGES)
            console.print(Panel(
                Text.from_markup(f"[bold green]Go touch grass![/bold green]\n\n[dim]{nudge}[/dim]"),
                border_style="green",
            ))
        else:
            if next_window:
                msg = f"[bold red]Keep coding...[/bold red]\n\n[dim]Try again at {next_window}[/dim]"
            else:
                msg = "[bold red]Keep coding...[/bold red]\n\n[dim]No safe window left today. Try tomorrow![/dim]"
            console.print(Panel(msg, border_style="red"))

    except click.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(30)
    except requests.RequestException as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise SystemExit(20)
    except KeyError as e:
        console.print(f"[red]Unexpected API response — missing field: {e}[/red]")
        raise SystemExit(20)
    except ValueError as e:
        console.print(f"[red]Could not parse API response: {e}[/red]")
        raise SystemExit(20)
