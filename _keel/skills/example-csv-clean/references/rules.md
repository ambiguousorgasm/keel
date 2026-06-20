# CSV cleaning conventions

- Strip whitespace from headers; lowercase; replace spaces with underscores.
- Drop rows where every cell is empty.
- Treat columns as: int if all values parse as int; else float if all parse as
  float; else string. Never coerce a column with leading-zero values to numeric.
- Preserve original column order.
