# Git Directory Extension

Jinja2 filter extension for detecting if a directory is a git repository.

## Usage

Examples:

- Detect if `git_path` is a git directory  
    `{{ git_path | gitdir }}`
- Assert that `git_path` is a git directory  
    `{{ git_path | gitdir is true }}`
- Assert that `git_path` is **NOT** a git directory  
    `{{ git_path | gitdir is false }}`
- Using `gitdir` in a conditional  
    `{% if (git_path | gitdir) %}{{ git_path }} is a git directory{% else %}no git directory at {{ git_path }}{% endif %}`

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
    when: "{{ _copier_conf.dst_path | realpath | gitdir }}"
```