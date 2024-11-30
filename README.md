# llm-llm-duckduckgo-chat

[![PyPI](https://img.shields.io/pypi/v/llm-llm-duckduckgo-chat.svg)](https://pypi.org/project/llm-llm-duckduckgo-chat/)
[![Changelog](https://img.shields.io/github/v/release/sukhbinder/llm-llm-duckduckgo-chat?include_prereleases&label=changelog)](https://github.com/sukhbinder/llm-llm-duckduckgo-chat/releases)
[![Tests](https://github.com/sukhbinder/llm-llm-duckduckgo-chat/actions/workflows/test.yml/badge.svg)](https://github.com/sukhbinder/llm-llm-duckduckgo-chat/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/sukhbinder/llm-llm-duckduckgo-chat/blob/main/LICENSE)

LLM plugin for Duckduckgo ai service

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).
```bash
llm install llm-llm-duckduckgo-chat
```
## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-llm-duckduckgo-chat
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
llm install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
