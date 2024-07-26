<h1 align=center> gists-gone </h2>

<p align="center">
     <a href="https://github.com/ben-n93/gists-gone/actions/workflows/tests.yml"><img src="https://github.com/ben-n93/gists-gone/actions/workflows/tests.yml/badge.svg" alt="Testing"></a>
    <a href="https://codecov.io/gh/ben-n93/gists-gone" ><img src="https://codecov.io/gh/ben-n93/gists-gone/graph/badge.svg?token=FO4QA8CUF5"/></a>
    <a href="https://pypi.org/project/gists-gone/"><img src="https://img.shields.io/pypi/pyversions/gists-gone" alt="versions"></a>
</p>

`gists-gone` is a command-line tool that gives you more granular control over bulk deletion of your Github gists.

For example, if you want to only delete your public Python gists:

```
gists-gone -l Python -v public
```

## Getting started

### Prerequisites

In order to use this tool you'll need a Github access token with the **"Gists" user permissions (write)**. 

Once you have this token you can pass it to the tool directly:

```
gists-gone --token ghp_abc123
```

... or you can create an environmental variable called `GITHUB_API_TOKEN`, the value of which is your access token.

### Installation

```
pip install gists-gone
```

## Usage

### Deleting everything 

To delete *all* your gists simply run the tool with no arguments:

```
gists-gone
```

You will get a warning message before proceeding (which can be overriden with the `--force` option, although I caution against this):

```
Are you sure you proceed with the deletion?
10 gists will be deleted.
[Y/n]
```

### Filtering

`gists-gone` have 3 different options, all of which can be combined for specifying the type of gists to included in the deletion.

#### Languages 

You can specify gists in particular languages you want deleted:

```
gists-gone --languages SQL Python
```

Note that the name of the languages is case-sensitive.

For gists you want deleted that that have no language (or Github doesn't recognise) you can specify Unknown:

```
gists-gone -l Unknown
```

#### Visbility

Using the `-visibility` option you can specify whether you want to delete public or private gists:

```
gists-gone -v private
gists-gone -v public
```

#### Date range

With the `--date_range` option you can specify to delete gists created on a particular date:

```
gists-gone -dr 2024-04-01
```

Or between two dates:

```
gists-gone -dr 2018-04-01 2024-01-01
```

Dates should be passed in YYYY-MM-DD format.

#### Examples

Deleting private gists created from 2020-01-01 onwards:

```
gists-gone -v private -dr 2020-01-01 2100-01-01
```

Deleting Rust gists created on a particular date:

```
gists-gone -l Rust -dr 2024-11-07
```

### Limitations

Note that a maximum of 3000 gists can be retrieved by the tool at any one time, due to a limitation imposed by the API.

However you can simply rerun the tool after you've deleted some gists or if you're feeling fancy you can invoke the command multiple times with a loop:

```sh
for i in {1..5}
do
  gists-gone --force # Be careful with this option!
done
```

The Github API also has a personal rate limit of 5,000 requests per hour so bear in mind you'll have to wait an hour if you want to delete more than 3000 gists.

## Roadmap

I would like to eventually add more options for specifying the types of gists to be deleted:

- [ ]  Filtering a gist's description using regex 
- [ ]  Starred or unstarred
- [ ]  Updated date

## Warning

I've done my best to unit test this tool as thoroughly as possible but as there is no way to retrieve a gist once it's deleted I caution you to not use this tool if you have any particularly important or sensitive gists that you do not want accidentally deleted.

I do not take responsibility for any unintended outcomes or damages.

That said, if you do notice anything wrong please raise an issue!

