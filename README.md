# OrderFlow

OrderFlow is a small, modular, deterministic order intake + state + fulfillment
system with a CLI tool `orderflow`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Basic usage

Place an order:

```bash
orderflow place --mobile +447700900123 --message "ORDER COFFEE=2 TEA=1"
```

List outstanding orders:

```bash
orderflow list
orderflow list --format lines
```

Fulfill an order (default auth code is `123456`):

```bash
orderflow fulfill --order-id ORD-1A2B3C4D --auth-code 123456
```

Show a specific order:

```bash
orderflow show --order-id ORD-1A2B3C4D
```

Process a batch file (use `-` for stdin):

```bash
orderflow batch --input orders.txt
```

View metrics:

```bash
orderflow metrics
orderflow metrics --reset
```

## Authentication

The default auth code is `123456`. Override it using `--auth-code` or the
`ORDERFLOW_AUTH_CODE` environment variable.
