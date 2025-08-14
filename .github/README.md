# GitHub Actions & Automation

This directory contains the automation configuration for the Vimeo Monitor project.

## Workflows

### CI Pipeline (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop, Pull Requests
- **Jobs**: Lint → Test → Build
- **Features**: UV package manager, Python 3.12, automated testing

### Documentation (`.github/workflows/docs.yml`)
- **Triggers**: Push to main, manual dispatch
- **Jobs**: Build → Deploy to GitHub Pages
- **Features**: MkDocs build, automated deployment

### Security Scan (`.github/workflows/security.yml`)
- **Triggers**: Weekly schedule, push to main, PRs
- **Jobs**: Security vulnerability scanning
- **Features**: Safety checks, dependency vulnerability scanning

### Deploy (`.github/workflows/deploy.yml`)
- **Triggers**: Release published, manual dispatch
- **Jobs**: Build and package for release
- **Features**: Release artifact creation

## Dependabot

- **Schedule**: Weekly updates on Mondays at 9:00 AM
- **Ecosystem**: pip (UV compatible)
- **Labels**: dependencies, automated
- **Reviewers**: dcapparelli

## Templates

- **Pull Request**: Standardized PR template
- **Issues**: Bug report and feature request templates
- **Automation**: Consistent project management

## Security

- **Dependencies**: Safety scanning for vulnerabilities
- **Schedule**: Weekly automated security checks
- **Integration**: CI/CD pipeline integration
