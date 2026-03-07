# Git Directory Extension

Jinja2 filter extension for detecting if a directory is an (empty) git repository and determining the default branch.

## Usage

### `gitdir`

Detects if the path being filtered by `gitdir` is the _top level_ git repository directory.

So, if my path is `/git/path/here` and there exists `/git/path/here/.git`, 
then `{{ '/git/path/here' | gitdir }}` will be true.

However, if my path is `/git/path/here` and there exists `/git/path/.git`, 
then `{{ '/git/path/here' | gitdir }}` will be false.

This is because the _top level_ directory is `/git/path`, not the tested path of `/git/path/here`.


Examples:

- Detect if `git_path` is a git directory  
    `{{ git_path | gitdir }}`
- Assert that `git_path` is a git directory  
    `{{ git_path | gitdir is true }}`
- Assert that `git_path` is **NOT** a git directory  
    `{{ git_path | gitdir is false }}`
- Using `gitdir` in a conditional  
    `{% if (git_path | gitdir) %}{{ git_path }} is a git directory{% else %}no git directory at {{ git_path }}{% endif %}`


### `emptygit`

Detects if the path being filtered by `emptygit` contains exactly 0 commits across all references. 
This will work for subdirectories within a git directory.

So, if my path is `/git/path/here` and there have been *no* commits, then `{{ '/git/path/here' | emptygit }}` will be true.

However, if my path is `/git/path/here` and there *have* been _any_ commits anywhere, then `{{ '/git/path/here' | emptygit }}` will be false.


Examples:

- Detect if `git_path` is an empty git directory  
    `{{ git_path | emptygit }}`
- Assert that `git_path` is an empty git directory  
    `{{ git_path | emptygit is true }}`
- Assert that `git_path` is **NOT** an empty git directory  
    `{{ git_path | emptygit is false }}`
- Using `emptygit` in a conditional  
    `{% if (git_path | emptygit) %}{{ git_path }} has commits{% else %}{{ git_path }} has NO commits{% endif %}`

### `gitdefaultbranch`

Returns the default branch name for the git repository at the given path. Uses a multi-layered
fallback cascade to determine the default branch:

1. `git symbolic-ref refs/remotes/upstream/HEAD` (local, fast)
2. `git symbolic-ref refs/remotes/origin/HEAD` (local, fast)
3. `git ls-remote --symref upstream HEAD` (network, read-only)
4. `git ls-remote --symref origin HEAD` (network, read-only)
5. `git config init.defaultBranch` (local config)
6. Hardcoded fallback: `main`

Returns an empty string if the path is not a git repository.


Examples:

- Get the default branch name
    `{{ git_path | gitdefaultbranch }}`
- Using `gitdefaultbranch` in a conditional
    `{% if (git_path | gitdefaultbranch) %}default branch: {{ git_path | gitdefaultbranch }}{% endif %}`


### Copier

This can be utilized within a Copier `copier.yaml` file for determining if the destination
path is already initialized as a git directory.

Example:  

This will configure a Copier `_task` to run `git init` but _only_ if the destination
path isn't already a git directory.

```yaml
_jinja_extensions:
    - jinja2_git_dir.GitDirectoryExtension
_tasks:
  - command: "git init"
    when: "{{ _copier_conf.dst_path | realpath | gitdir is false }}"
  # ORDERING: `emptygit is false` test must come first, otherwise both tasks trigger
  - command: "git commit -am 'template update applied'"
    when: "{{ _copier_conf.dst_path | realpath | emptygit is false }}"
  - command: "git commit -am 'initial commit'"
    when: "{{ _copier_conf.dst_path | realpath | emptygit is true }}"
```

## Development

- Use [`cog commit`](https://docs.cocogitto.io/guide/commit.html) for [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
-- `cog commit -a feat "new thing"`
- Use [`cog bump`](https://docs.cocogitto.io/guide/bump.html) for [SemVer versioning](https://semver.org)
-- `cog bump --auto`
- Use [`hatch build`](https://hatch.pypa.io/dev/cli/reference/#hatch-build) for building new package releases _after_ the repo version has been bumped
-- `uvx hatch build`
- Use [`hatch publish`](https://hatch.pypa.io/dev/cli/reference/#hatch-publish) to push the new package to PyPI
-- `uvx hatch publish`
- Bump the nixpkgs release to the new version
-- https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/python-modules/jinja2-git-dir/default.nix