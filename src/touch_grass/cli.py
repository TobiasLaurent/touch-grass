from __future__ import annotations

import random

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from touch_grass.conditions import evaluate_current, find_next_safe_window
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
def main(lat: float | None, lon: float | None):
    """Check if it's safe to go outside and touch grass."""
    try:
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

        # Fetch data
        with console.status("[dim]Checking conditions...[/dim]"):
            weather = get_weather(location["latitude"], location["longitude"])
            air_quality = get_air_quality(location["latitude"], location["longitude"])

        # Evaluate
        result = evaluate_current(weather, air_quality)

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

        # Verdict
        if result["safe"]:
            nudge = random.choice(NUDGES)
            console.print(Panel(
                Text.from_markup(f"[bold green]Go touch grass![/bold green]\n\n[dim]{nudge}[/dim]"),
                border_style="green",
            ))
        else:
            next_window = find_next_safe_window(weather, air_quality)
            if next_window:
                msg = f"[bold red]Keep coding...[/bold red]\n\n[dim]Try again at {next_window}[/dim]"
            else:
                msg = "[bold red]Keep coding...[/bold red]\n\n[dim]No safe window left today. Try tomorrow![/dim]"
            console.print(Panel(msg, border_style="red"))

    except click.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    except requests.RequestException as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise SystemExit(1)
    except (KeyError, ValueError) as e:
        console.print(f"[red]Error parsing data: {e}[/red]")
        raise SystemExit(1)
