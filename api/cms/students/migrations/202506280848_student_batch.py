
# List of dependencies (migration that must be applied before this one)
dependencies = ["students.202506180903_initial","batch.202506280405_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS student_batch(
        enrollment_no VARCHAR(36),
        student_id UUID NOT NULL,
        batch_id UUID NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_student_batch PRIMARY KEY (enrollment_no),
        CONSTRAINT fk_student_batch_student FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE NO ACTION ON UPDATE CASCADE,
        CONSTRAINT fk_student_batch_batch FOREIGN KEY (batch_id) REFERENCES batch (id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_student_student_id_batch_id ON student_batch (student_id, batch_id) WHERE is_active;
    """
    """--sql
    CREATE INDEX IF NOT EXISTS idx_student_batch_student_id ON student_batch (student_id);
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_student_batch_batch_id ON student_batch (batch_id);
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_student_student_id_batch_id;
    """
    """--sql
    DROP INDEX IF EXISTS idx_student_batch_student_id;
    """,
    """--sql
    DROP INDEX IF EXISTS idx_student_batch_batch_id;
    """,
    """--sql
    DROP TABLE IF EXISTS student_batch;
    """,
]
