# OrderFlow CLI contract (stdout JSON + exit codes)

This document defines the externally-visible behaviour of the OrderFlow CLI.
It exists to make “CLI contract” tests precise and to support stable regression
tests.

Implementation reference: src/orderflow/cli.py (notably _print_json and _exit_code_for_response).

## 1) Stdout output format

Unless otherwise stated below, commands write JSON to stdout, followed by a single newline.
JSON keys are emitted in a deterministic order to support golden output tests.

### 1.1 Success schema

On success, commands return:

    { "ok": true, "command": "<command>", "data": { ... } }

- command is one of: place, list, fulfill, show, metrics, or batch_summary (for the batch final summary).
- data is command-specific.

### 1.2 Error schema

On failure, commands return:

    {
      "ok": false,
      "command": "<command>",
      "error": {
        "code": "<CODE>",
        "message": "<human message>",
        "details": { ... }
      }
    }

- error.code is a stable machine-readable identifier.
- error.details may include contextual fields (e.g., offending field, order_id, line_no).

## 2) Exit code mapping

Exit codes are stable and intended for scripting:

- 0: Success (ok=true).
- 1: Internal failure (e.g., INTERNAL_ERROR, DATABASE_ERROR, or any unexpected error).
- 2: Validation / input errors:
  INVALID_MOBILE, MESSAGE_TOO_LONG, PARSE_ERROR, TOO_MANY_ITEMS, UNKNOWN_ITEM, INVALID_QUANTITY.
- 3: UNAUTHORIZED (incorrect auth code).
- 4: ORDER_NOT_FOUND.
- 5: ORDER_ALREADY_FULFILLED.

## 3) Batch command special-case

orderflow batch --input <file> writes multiple JSON objects to stdout:

1) One JSON object per input line:

    { "line_no": 1, "mobile": "...", "message": "...", "response": { ... } }

2) A final summary object:

    {
      "ok": true,
      "command": "batch_summary",
      "data": { "lines_processed": 10, "lines_succeeded": 9, "lines_failed": 1 }
    }

Batch exit codes:
- 1 if any line produced an internal/database error,
- else 2 if any line produced a validation/input error,
- else 0.

## 4) List --format lines

orderflow list --format lines prints a human-readable line format on success and exits 0.
If list fails, it emits the standard JSON error schema and uses the exit code mapping above.

## 5) Non-stdout outputs

- Logs are written to stderr.
- Diagnostics (if enabled via --diagnostics or ORDERFLOW_DIAGNOSTICS_PATH) are written to a JSONL file and do not change stdout format.
