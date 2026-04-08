# Hugo Custom Repo Preparer

This utility automates the process of creating customized versions of Hugo (or other repositories). It handles cloning, checking out specific tags, applying GitHub Pull Requests, applying local patches, and optionally building and archiving the resulting artifacts.

## Prerequisites

- Python 3.x
- Git
- PyYAML (`pip install -r requirements.txt`)

## Usage

Run the script using the following command:

```bash
python scripts/prepare-repo.py [options]
```

### Command Line Arguments

| Argument | Long Flag | Description |
| :--- | :--- | :--- |
| `-c` | `--config` | Path to the YAML configuration file (default: `config.yml`). |
| `-b` | `--build` | Executes the `build` command defined in the config for each entry. |
| `-a` | `--archive` | Name of the archive file to create (e.g., `output.zip`). Implies `-b`. |
| `-v` | `--verbose` | Enables debug-level logging for more detailed output. |
| | `--clean` | Automatically removes the checked-out repository directories upon exit. |

### Archiving Details
When using the `-a` / `--archive` flag, the script identifies "new" files (files untracked by Git, usually build artifacts) and packages them. Supported formats include:
- `.zip`
- `.tar`
- `.tar.gz` / `.tgz`

## Configuration Format

The script relies on a YAML file to define the build targets.

### Global Settings
| Key | Description |
| :--- | :--- |
| `default-repo` | The fallback Git URL used if a specific config doesn't provide one. |
| `prefix` | A string prepended to all target directory names (e.g., `hugo`). |
| `configs` | A list of repository configurations to process. |

### Repository Configuration (`configs` list items)
| Key | Description |
| :--- | :--- |
| `suffix` | Used to name the target directory: `{prefix}-{suffix}`. |
| `repo` | (Optional) Git URL to clone. Overrides `default-repo`. |
| `tag` | (Optional) Git tag to checkout (e.g., `v0.160.0`). |
| `prs` | (Optional) A list of Pull Request numbers to fetch and merge from `origin`. |
| `patches` | (Optional) A list of local file paths to `.patch` files to apply via `git apply`. |
| `build` | (Optional) A shell command to run inside the directory if `--build` is active. |

### Example `config.yaml`

```yaml
default-repo: https://github.com/gohugoio/hugo
prefix: hugo
configs:
  - suffix: esbuild
    tag: v0.160.0
    prs:
      - 14725
    patches:
      - ./patches/fix-build.patch
    build: CGO_ENABLED=1 go build -tags extended
```

## Example Commands

**Prepare and Build:**
`python scripts/prepare-repo.py -c config.yaml --build`

**Build, Archive, and Cleanup:**
`python scripts/prepare-repo.py -c config.yaml -a custom-hugo.tar.gz --clean`