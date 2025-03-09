# Haystack

## Overview

This is a small tool that demonstrates how to pull the running configuration from all devices in an Arista CVaaS tenant and rebuild them in a full text search index with DuckDB to provide fabric-wide config search. 

## Usage

```bash
uv run haystack.py fetch-configs --apiserver <apiserver_url> --access-token <access_token>
```

```bash
uv run haystack.py search --query <query>
```

