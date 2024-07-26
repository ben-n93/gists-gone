"""
gists-gone is a CLI that gives you more granular control over bulk deletion of
your Github gists.
"""

import argparse
from collections import namedtuple
from datetime import datetime
from os import environ
from time import sleep

from alive_progress import alive_bar
import requests
import rich

Gist = namedtuple(
    "Gist",
    ["id", "visibility", "language", "created_date"],
)


def get_parser_args():
    """Create the command-line parser and get arguments."""
    parser = argparse.ArgumentParser(
        description="Bulk delete Github Gists from the command-line."
    )
    parser.add_argument(
        "-t", "--token", type=str, help="Your Github API access token.", required=False
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Don't ask for confirmation before deletion of gists. Use with caution.",
        required=False,
    )

    parser.add_argument(
        "-v",
        "--visibility",
        type=str,
        help="Specify whether you want to delete public or secret gists.",
        required=False,
        choices=["public", "secret"],
    )

    parser.add_argument(
        "-l",
        "--languages",
        type=str,
        help="Specify gists in which which programming languages to delete. Default is all.",
        nargs="+",
        required=False,
    )

    parser.add_argument(
        "-dr",
        "--date_range",
        type=str,
        help="Specify the date or date range gists were created.",
        nargs="+",
        required=False,
    )

    args = parser.parse_args()
    return args


def cli():
    # Check for access token.
    args = get_parser_args()
    if not args.token:
        try:
            args.token = environ["GITHUB_API_TOKEN"]
        except KeyError:
            raise ValueError(
                "Please pass your Github API token to the --token option or create an environmental variable."
            )

    relevant_args = [
        value for key, value in vars(args).items() if key not in ("token", "force")
    ]
    # Process date arguments.
    if relevant_args[2] is not None:
        relevant_args[2] = parse_date_arguments(relevant_args[2])

    # Verify token is valid and get all gists.
    gists = []
    for page in range(1, 31):
        response = requests.get(
            "https://api.github.com/gists",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {args.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"per_page": "100", "page": f"{page}"},
        )
        response.raise_for_status()
        page_gists = create_gists(response.json())
        gists.extend(page_gists)
        if len(page_gists) < 30:  # No gists on further pages.
            break
        sleep(1)  # To avoid secondary rate limits.

    # Filter and delete gists.
    if all(value is None for value in relevant_args):
        gist_ids = [gist.id for gist in gists]
        delete_gists(args, gist_ids)
    else:
        gist_ids = filter_gists(relevant_args, gists)
        delete_gists(args, gist_ids)


def parse_date_arguments(date_arguments):
    """Create a list of datetime objects from the arguments passed to the
    CLI's -dr option."""
    if len(date_arguments) == 3:
        raise TypeError(
            "Too many arguments passed to the -dr flag. Only pass max 2 dates."
        )
    dates = []
    for argument in date_arguments:
        try:
            date = datetime.strptime(argument, "%Y-%m-%d").date()
            dates.append(date)
        except ValueError as error:
            raise ValueError(
                "Please pass a date in YYYY-MM-DD format to the -dr argument."
            ) from error
    return dates


def create_gists(json):
    """Create Gists."""
    gists = []
    for raw_gist in json:
        if (
            languages := raw_gist["files"][next(iter(raw_gist["files"]))]["language"]
        ) is None:
            languages = "Unknown"
        visibility = raw_gist.get("public")
        date_created = datetime.strptime(
            raw_gist["created_at"], "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601 format.
        ).date()
        if visibility:
            visibility = "public"
        else:
            visibility = "secret"

        gist = Gist(raw_gist.get("id"), visibility, languages, date_created)
        gists.append(gist)
    return gists


def filter_gists(relevant_args, gists):
    """Filter the gists to those that match the CLI arguments."""
    gist_ids = []
    for index, argument in enumerate(relevant_args):
        matched_ids = []
        for gist in gists:
            if (
                argument is None
            ):  # All Gists eligible if there is no argument for this option.
                matched_ids.append(gist.id)
                continue
            # Visiblity.
            if index == 0 and argument == gist.visibility:
                matched_ids.append(gist.id)
            # Languages.
            if index == 1 and isinstance(argument, list):
                if gist.language in argument:
                    matched_ids.append(gist.id)
            # Date range
            if index == 2 and isinstance(argument, list):
                if len(argument) == 1:
                    if gist.created_date == argument[0]:
                        matched_ids.append(gist.id)
                else:
                    if (
                        gist.created_date >= argument[0]
                        and gist.created_date <= argument[1]
                    ):
                        matched_ids.append(gist.id)
        gist_ids.append(matched_ids)

    gist_ids = set(gist_ids[0]).intersection(*gist_ids[1:])
    return list(gist_ids)


def delete_gists(args, gists):
    """Delete Github gists."""
    if len(gists) == 0:
        print("No gists are eligible for deletion.")
        return
    if not args.force:
        rich.print(
            """[bold red]Are you [underline]sure[/underline] you proceed with the deletion?[/bold red]"""
        )
        rich.print(
            f"""[bold yellow]{len(gists)}[/bold yellow] [bold red]gists will be deleted.[/bold red]"""
        )
        answer = input("[Y/n] ")
        if answer not in ("Yes", "Y", "y"):
            return
    with alive_bar(len(gists)) as progress_bar:
        progress_bar.title("Deleting gists...")
        for gist in gists:
            sleep(1)
            response = requests.delete(
                f"https://api.github.com/gists/{gist}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {args.token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        response.raise_for_status()
        progress_bar()
    rich.print("[bold red]Gists have been deleted![/bold red]")
