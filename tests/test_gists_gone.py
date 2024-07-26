"""
Unit tests for gists_gone.py
"""

from datetime import datetime
import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from requests import HTTPError

from gists_gone.gists_gone import (
    cli,
    parse_date_arguments,
    create_gists,
    filter_gists,
    delete_gists,
    Gist,
)


# Fixtures.
@pytest.fixture
def mock_gists():
    with open(
        Path("./tests/fixtures/fake_gists.json"), "r", encoding="utf-8"
    ) as json_input:
        gists = json.load(json_input)
    return gists


@pytest.fixture
def created_gists(mock_gists):
    gists = create_gists(mock_gists)
    return gists


# Test CLI.
@patch("gists_gone.gists_gone.get_parser_args")
@patch.dict("gists_gone.gists_gone.environ", {}, clear=True)
def test_no_api_key(cli_args):
    """Test a ValueError is raised when no API token is passed to the
    --token option AND no value is found with GITHUB_API_TOKEN environmental
    variable.
    """
    cli_args.return_value = Mock(token=None)
    with pytest.raises(ValueError):
        cli()


@patch("gists_gone.gists_gone.get_parser_args")
@patch.dict("gists_gone.gists_gone.environ", {"GITHUB_API_TOKEN": "123"})
def test_invalid_api_key(cli_args, requests_mock):
    """Test an exception is raised when an invalid API token is provided
    to the CLI.
    """
    cli_args.return_value = Mock(token=None)
    requests_mock.get("https://api.github.com/gists", status_code=403)

    with pytest.raises(HTTPError):
        cli()


@patch("gists_gone.gists_gone.create_gists")
@patch("gists_gone.gists_gone.filter_gists")
@patch("gists_gone.gists_gone.delete_gists")
@patch.dict("gists_gone.gists_gone.environ", {"GITHUB_API_TOKEN": "123"})
def test_no_filtering(mock_delete, mock_filter, gists, requests_mock):
    """Test that no filtering is applied when no arguments have been passed
    to the CLI and that delete_gists is called.

    Notes
    -----
    Unit testing this method requires swapping out the Mock object
    for a custom class, as calling vars() on a Mock returns attributes
    not present in the object I'm trying to mock.

    Note that this is also why I have used the patch decorator in the body of
    this unit test, as I needed to define swap out the mock for a custom class
    defined within this function.
    """

    class Arguments:
        def __init__(
            self,
            token=None,
            force=False,
            visibility=None,
            languages=None,
            date_range=None,
        ):
            self.token = token
            self.force = force
            self.visibility = visibility
            self.languages = languages
            self.date_range = date_range

    requests_mock.get("https://api.github.com/gists", status_code=200, json={})
    with patch("gists_gone.gists_gone.get_parser_args", Arguments):
        cli()
        mock_filter.assert_not_called()
        mock_delete.assert_called()


@patch("gists_gone.gists_gone.create_gists")
@patch("gists_gone.gists_gone.filter_gists")
@patch("gists_gone.gists_gone.delete_gists")
@patch.dict("gists_gone.gists_gone.environ", {"GITHUB_API_TOKEN": "123"})
def test_filtering_is_called(mock_delete, mock_filter, gists, requests_mock):
    """Test that the filter_gists is called onlt when a user passes an argument
    to the CLI.

    Notes
    -----
    See test_no_filtering() documentation for details on set up.
    """

    class Arguments:
        def __init__(
            self,
            token=None,
            force=None,
            visibility=False,
            languages=None,
            date_range=None,
        ):
            self.token = token
            self.force = force
            self.visibility = visibility
            if languages is None:
                self.languages = ["Python", "SQL"]
            else:
                self.languages = languages
            self.date_range = date_range

    requests_mock.get("https://api.github.com/gists", status_code=200, json={})
    with patch("gists_gone.gists_gone.get_parser_args", Arguments):
        cli()
        mock_filter.assert_called()
        mock_delete.assert_called()


# Test functions.
def test_parse_date_arguments():
    """Test that the test_parse_date_arguments works."""
    # Test that too many arguments raises an error.
    arguments = ["2024-01-01", "2024-02-01", "2024-03-01"]
    with pytest.raises(TypeError):
        parse_date_arguments(arguments)
    # Test that a list is returned.
    arguments = ["2024-01-01"]
    assert isinstance(parse_date_arguments(arguments), list)
    # Test that datetime objects are succesfully created.
    assert parse_date_arguments(arguments)[0] == datetime(2024, 1, 1).date()
    arguments = ["2024-01-01", "2024-02-01"]
    assert parse_date_arguments(arguments)[0] == datetime(2024, 1, 1).date()
    assert parse_date_arguments(arguments)[1] == datetime(2024, 2, 1).date()
    # Test that an exception is raised when a string in the wrong format is passed.
    arguments = ["2024-01"]
    with pytest.raises(ValueError):
        parse_date_arguments(arguments)
    arguments = ["2024-01-01", "2024"]
    with pytest.raises(ValueError):
        parse_date_arguments(arguments)


@patch("gists_gone.gists_gone.get_parser_args")
@patch.dict("gists_gone.gists_gone.environ", {"GITHUB_API_TOKEN": "123"})
def test_create_gists_works(cli_args, requests_mock, mock_gists):
    """Test that Gists named tuples are succesfully created from the JSON
    returned from the Github API."""
    requests_mock.get("https://api.github.com/gists", status_code=200)
    gists = create_gists(mock_gists)

    assert isinstance(gists, list)
    assert gists[0] == Gist(
        "7fea2e3837f324e5e3699917f687c862",
        "private",
        "Clojure",
        datetime(2024, 7, 12).date(),
    )
    assert gists[2] == Gist(
        "3a9f7f73665cf174f9466e3f28fcaf89",
        "public",
        "Unknown",
        datetime(2024, 7, 10).date(),
    )


def test_filter_gists_returns_list(created_gists):
    """Test that filter_gists() returns a list."""
    arguments = [None, ["Python"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert isinstance(gist_ids, list)


def test_filter_gists_works_with_visibility(created_gists):
    """Test that filter_gists() works when the visibility argument is passed."""

    arguments = ["private", None, None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "7fea2e3837f324e5e3699917f687c862" in gist_ids
    assert "5f6258f9caae6f2c6511e926f7f623af" in gist_ids
    assert len(gist_ids) == 2

    arguments = ["public", None, None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "7fea2e3837f324e5e3699917f687c862" not in gist_ids
    assert "5f6258f9caae6f2c6511e926f7f623af" not in gist_ids
    assert len(gist_ids) == 4


def test_filter_gists_works_with_languages(created_gists):
    """Test that filter_gists() works when a languages argument is passed."""

    # One language passed to --languages.
    arguments = [None, ["Python"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids
    assert len(gist_ids) == 1

    # Multiple language passed to --languages.
    arguments = [None, ["Python", "SQL"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids
    assert "bc22d164463296d99cbeb1a7038b6d6e" in gist_ids
    assert len(gist_ids) == 2

    # Multiple arguments passed to --languages, only one of which is valid.
    arguments = [None, ["Python", "Spam"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids
    assert len(gist_ids) == 1


def test_filter_works_with_dates(created_gists):
    """Test that filter_gists() works with arguments passed to -dr."""

    # Test Gist creation date equal to date passed to argument.
    arguments = [None, None, ["2024-06-16"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 3
    assert "8eaee095f4b3a822127cc4fa368b4165" in gist_ids
    assert "bc22d164463296d99cbeb1a7038b6d6e" in gist_ids
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids

    # Test Gist created within date ranges.
    arguments = [None, None, ["2024-07-11", "2024-08-01"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 2

    arguments = [None, None, ["2021-01-01", "2023-01-01"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 0

    arguments = [None, None, ["2025-01-01", "2030-01-01"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 0


def test_filter_works_with_multiple_arguments(created_gists):
    """Test that filter_gists works when different arguments are passed."""

    arguments = ["private", ["Python"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 0

    arguments = ["public", ["Python"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids
    assert len(gist_ids) == 1

    arguments = ["public", ["Python", "Ruby"], None]
    gist_ids = filter_gists(arguments, created_gists)
    assert "68ae668e6b5e7364f44b62dd7062231f" in gist_ids
    assert "8eaee095f4b3a822127cc4fa368b4165" in gist_ids
    assert len(gist_ids) == 2

    arguments = ["private", None, ["2024-07-12"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 2

    arguments = ["public", ["Rust", "Clojure"], ["2024-07-12"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 0

    arguments = ["private", ["Rust", "Clojure"], ["2024-07-12"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 2

    arguments = ["public", None, ["2024-04-01", "2024-06-28"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 3

    arguments = ["public", ["Ruby"], ["2024-04-01", "2024-06-28"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 1
    assert "8eaee095f4b3a822127cc4fa368b4165" in gist_ids

    arguments = ["public", ["SQL"], ["2024-01-01", "2024-06-15"]]
    arguments[2] = parse_date_arguments(arguments[2])
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 0

    # Technically filter_gists() should not be called if all arguments are None.
    arguments = [None, None, None]
    gist_ids = filter_gists(arguments, created_gists)
    assert len(gist_ids) == 6


@patch("builtins.input")
@patch("requests.delete")
def test_force_argument_works(mock_api_call, mock_input, created_gists):
    """
    Test that the --force option works with delete_gists.
    """
    delete_gists(Mock(force=True), created_gists)
    mock_input.assert_not_called()


@patch("builtins.input")
@patch("gists_gone.gists_gone.sleep")
@patch("requests.delete")
def test_delete_returns_if_users_says_no(mock_api_call, sleep, answer, created_gists):
    """Test that if a user does not respond with Yes, Y or yes the delete_gists()
    function will exit without doing anything.
    """
    answer.return_value = "No"
    delete_gists(Mock(force=False), created_gists)
    sleep.assert_not_called()


@patch("builtins.input")
@patch("gists_gone.gists_gone.sleep")
@patch("requests.delete")
def test_delete_does_not_run_with_no_gists(mock_api_call, sleep, mock_input):
    """
    Test that if no gists have been passed to delete_gists() nothing happens.
    """
    mock_input.assert_not_called()
    sleep.assert_not_called()
    delete_gists(Mock(force=False), {})
