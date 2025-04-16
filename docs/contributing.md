We'd love you to contribute to Otterdog!

## Issues

Questions, feature requests and bug reports are all welcome as
[discussions](https://github.com/eclipse-csi/otterdog/discussions) or
[issues](https://github.com/eclipse-csi/otterdog/issues).

## Pull Requests

It should be extremely simple to get started and create a Pull Request.

Unless your change is trivial (typo, docs tweak etc.), please create an issue to discuss the change before
creating a pull request.

If you're looking for something to get your teeth into, check out the
["help wanted"](https://github.com/eclipse-csi/otterdog/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22help%20wanted%22)
label on GitHub.

To make contributing as easy and fast as possible, you'll want to run tests and linting locally. Luckily,
Otterdog has few dependencies, doesn't require compiling and tests don't need access to databases, etc.
Because of this, setting up and running the tests should be very simple.

### Prerequisites

You'll need the following prerequisites:

- Any Python version **>= 3.11**
- **git**
- **make**
- [**poetry >= 2**](https://python-poetry.org/docs/#installation)


### Eclipse Contributor Agreement (ECA)

Log into the [Eclipse projects forge](https://www.eclipse.org/contribute/cla) (you will need to create
an account with the Eclipse Foundation if you have not already done so); click on "Eclipse Contributor
Agreement"; and Complete the form. Be sure to use the same email address when you register for the
account that you intend to use on Git commit records.

[More about ECA FAQ](https://www.eclipse.org/legal/eca/)

## Getting the source code

#### Fork the repository
[Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) the [repository](https://github.com/eclipse-csi/otterdog.git)
on GitHub and clone your fork locally.

```bash
# Clone your fork and cd into the repo directory
git clone https://github.com/<your username>/otterdog.git
cd otterdog

# Install poetry (preferred using pipx)
pipx install poetry
# or alternatively
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
make init
```

#### Add a git remote

Add a `remote
<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-for-a-fork>`_ and
regularly `sync <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork>`_ to make sure
you stay up-to-date with our repository:

Choose the component to get the instructions

```bash
git remote add upstream https://github.com/eclipse-csi/otterdog
git checkout main
git fetch upstream
git merge upstream/main
```


### Pre-commit hooks

The project extensively uses `pre-commit` hooks to ensure consistent source code formatting and type checking.
To enable `pre-commit` run the following:

```bash
poetry run pre-commit install
```

### Check out a new branch and make your changes

Create a new branch for your changes.

```bash
# Checkout a new branch and make your changes
git checkout -b my-new-feature-branch
# Make your changes...
```

### Run tests

Run tests locally to make sure everything is working as expected.

```bash
# Run tests
make test
```

Note: Code coverage HTML is also available in `htmlcov/`

### Commit and push your changes

Commit your changes, push your branch to GitHub, and create a pull request.

Please follow the pull request template and fill in as much information as possible. Link to any relevant issues and include a description of your changes.

When your pull request is ready for review, add a comment with the message "please review" and we'll take a look as soon as we can.

## Development Resources

### Creating an Organization for development
On your profile, [create one orgnaization](https://github.com/account/organizations/new?plan=free)

* **Organization name**: `otterdog-<github username>` (Ex: otterdog-foobar)
* **Contact email**: <your@email>
* **This organization belongs to**: My personal account

Accept the Terms of Service (if you agree)

#### Configure your otterdog (source code) to work with your development organization

https://otterdog.readthedocs.io/en/latest/setup/#otterdog-configuration

```json
{
    "defaults": {
        "jsonnet": {
        "base_template": "https://github.com/<Github Username>/otterdog#examples/template/otterdog-defaults.libsonnet@main",
        "config_dir": "orgs"
        }
    },
    "github": {
      "config_repo": ".otterdog",
    },
    "organizations": [
        {
        "name": "otterdog-<Github Username>",
        "github_id": "otterdog-<Github Username>",
        "credentials": {
            "provider": "plain",
            "api_token": "ghp_<TOKEN>",
            "username": "<Github Username>",
            "password": "<Password>",
            "twofa_seed": "<2FA TOTP seed>"
        }
        }
    ]
}
```

##### [Optional] Setup common Otterdog configuration repository

This will store and maintain the `otterdog.json` in the repository.


Go to your organization `https://github.com/otterdog-<github username>` > Repositories > New repository

- Repository name *: .otterdog

Click on Create repository


### [Optional] Otterdog WebApp development environment

#### Create a GitHub App

Create a GitHub app with the following permissions and events:

Repository Permissions:

- Actions: read and write
- Administration: read and write
- Commit statuses: read and write
- Contents: read and write
- Environments: read and write
- Metadata: read only
- Pages: read and write
- Pull requests: read and write
- Secrets: read and write
- Variables: read and write
- Webhooks: read and write
- Workflows: read and write

Organization Permissions:

- Administration: read and write
- Custom Organization Roles: read and write
- Members: read only
- Plan: read only
- Secrets: read and write
- Variables: read and write
- Webhooks: read and write

Events:

- Issue comment
- Pull request
- Pull request review
- Push
- Workflow job
- Workflow run

####


## Code style and requirements

TODO

## Documentation style

Documentation is written in Markdown and built using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

### Code documentation

When contributing to otterdog, please make sure that all code is well documented. The following should be documented using properly formatted docstrings:

- Modules
- Class definitions
- Function definitions
- Module-level variables

Otterdog uses [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) formatted according to [PEP 257](https://www.python.org/dev/peps/pep-0257/) guidelines. (See [Example Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for further examples.)

Where this is a conflict between Google-style docstrings and pydocstyle linting, follow the pydocstyle linting hints.

Class attributes and function arguments should be documented in the format "name: description." When applicable, a return type should be documented with just a description. Types are inferred from the signature.

```python
class Foo:
    """A class docstring.

    Attributes:
        bar: A description of bar. Defaults to "bar".
    """

    bar: str = 'bar'
```

```python
def bar(self, baz: int) -> str:
    """A function docstring.

    Args:
        baz: A description of `baz`.

    Returns:
        A description of the return value.
    """

    return 'bar'
```

You may include example code in docstrings. This code should be complete, self-contained, and runnable. Docstring examples are tested using [doctest](https://docs.python.org/3/library/doctest.html), so make sure they are correct and complete.

!!! note "Class and instance attributes"
    Class attributes should be documented in the class docstring.

    Instance attributes should be documented as "Args" in the `__init__` docstring.
