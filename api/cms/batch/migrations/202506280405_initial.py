
# List of dependencies (migration that must be applied before this one)
dependencies = ["programs.202506260323_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS batch(
        id UUID,
        code VARCHAR(32) NOT NULL,
        program_id UUID NOT NULL,
        name VARCHAR(32) NOT NULL,
        year INTEGER NOT NULL,
        extra_info JSONB,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_batch PRIMARY KEY (id),
        CONSTRAINT fk_batch_program FOREIGN KEY (program_id) REFERENCES programs (id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_batch_code ON batch (code, is_active);
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_batch_name ON batch (program_id, name, year, is_active);
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_batch_program_id ON batch (program_id);
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_batch_code;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_batch_name;
    """,
    """--sql
    DROP INDEX IF EXISTS idx_batch_program_id;
    """,
    """--sql
    DROP TABLE IF EXISTS batch;
    """,
]
