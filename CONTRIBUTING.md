# Contributing

Thanks for your interest in contributing to the unified namespace! Please take a moment to review this document **before submitting a pull request**.

## Pull requests

**Please ask first before starting work on any significant new features.**

It's never a fun experience to have your pull request declined after investing a lot of time and effort into a new feature. To avoid this from happening, we request that contributors create [a discussion]([https://github.com/mkashwin/unifiednamespace/discussions/new?category=ideas) to first discuss any new ideas. Your ideas and suggestions are welcome!

Please ensure that the tests are passing when submitting a pull request. If you're adding new features to Unified Name Space, please include tests.

## Where do I go from here?

For any questions, support, or ideas, etc. [please create a GitHub discussion](https://github.com/mkashwin/unifiednamespace/discussions/new). If you've noticed a bug, [please submit an issue](https://github.com/mkashwin/unifiednamespace/issues/new?template=bug_report.md).

### Fork and create a branch

If this is something you think you can fix, then [fork unifiednamespace](https://github.com/mkashwin/unifiednamespace/fork) and create
a branch with a descriptive name.

### Get the test suite running

Make sure you have setup the dev environment as specified in the [README.md](./README.md#setting-up-the-development-environment)

### Implement your fix or feature

At this point, you're ready to make your changes. Feel free to ask for help.

### Create a Pull Request

At this point, if your changes look good and tests are passing, you are ready to create a pull request.

Github Actions will run our test suite. It's possible that your changes fail. In that case, you'll have to setup your development
environment and investigate what's going on.

## Merging a PR (maintainers only)

A PR can only be merged into master by a maintainer if: CI is passing, approved by another maintainer and is up to date with the default branch. Any maintainer is allowed to merge a PR if all of these conditions ae met.

## Shipping a release (maintainers only)

Use the appropriate github action to create a release 
