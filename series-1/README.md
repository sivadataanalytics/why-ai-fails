# Series 1 — Context Pruning (Engineering Lab 2.1)

Demo: send only the log evidence the model needs — not all 2,000 HDFS lines.

## Layout

```
series-1/
  app.py    # main demo
  prune.py  # filter → dedupe → summarize pipeline
```

Shared helpers live in `common/`. Dataset: `datasets/HDFS_2k.log`.

## Run

```bash
# From repo root
python demo.py --dry-run
python demo.py --clarify-demo
python demo.py
```

Or directly:

```bash
python series-1/app.py --dry-run
```
