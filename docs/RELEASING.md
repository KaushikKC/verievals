# Releasing to PyPI (so `pip install verievals` works for everyone)

The project is already a proper Python package (`pyproject.toml` with a
`hatchling` build backend, metadata, and the `verievals` console script). It
builds a wheel today. To make `pip install verievals` work for the world, it
needs to be **published to PyPI** once. These are the exact steps.

> The name `verievals` is currently available on PyPI. The first upload claims it.

## 0. One-time: accounts and tokens

1. Create accounts at [pypi.org](https://pypi.org/account/register/) and
   [test.pypi.org](https://test.pypi.org/account/register/) (TestPyPI is a sandbox).
2. Create an **API token** for each (Account settings → API tokens). Store them;
   you'll paste them when `twine` prompts (username `__token__`, password = token).

## 1. Install the build tooling (already in the dev extras)

```bash
pip install -e ".[dev]"      # includes build + twine
```

## 2. Build the distributions

```bash
make build                   # or: python -m build
```

This produces `dist/verievals-0.1.0-py3-none-any.whl` and
`dist/verievals-0.1.0.tar.gz`.

## 3. Check the metadata renders correctly

```bash
twine check dist/*
```

Both files should report `PASSED` (this validates the long description / README).

## 4. Dry-run on TestPyPI first

```bash
twine upload --repository testpypi dist/*
# then verify it installs cleanly from the sandbox:
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ verievals
```

## 5. Publish to real PyPI

```bash
twine upload dist/*
```

Now anyone can:

```bash
pip install verievals
verievals --version
```

…and the `examples/custom_model.py` import (`from verievals... import ...`) works
from any Python environment — no clone, no `-e .`, no venv-in-this-repo required.

## 6. Cutting future versions

1. Bump `version` in `src/verievals/version.py` **and** `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. `make build` → `twine check dist/*` → `twine upload dist/*`.
4. Tag the release: `git tag v0.1.0 && git push --tags`.

## 7. Automated publishing on tag (recommended)

This repo ships `.github/workflows/publish.yml`, which builds and publishes to
PyPI automatically when you push a version tag — no token or manual `twine`:

```bash
# bump version in src/verievals/version.py and pyproject.toml, commit, then:
git tag v0.1.1 && git push --tags
```

**One-time PyPI setup (Trusted Publishing via OIDC, no secret to store):**

1. Go to the project on PyPI → **Manage → Publishing**.
2. Add a **GitHub Actions** trusted publisher:
   - Owner: `KaushikKC`  ·  Repository: `verievals`
   - Workflow filename: `publish.yml`  ·  Environment: `pypi`
3. Create a GitHub **Environment** named `pypi` (repo Settings → Environments).

After that, every `v*` tag push triggers a verified build + publish.

