# List of dependencies (migration that must be applied before this one)
dependencies = ["students.202506180903_initial", "parents.202506200708_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS student_parent (
        student_id UUID NOT NULL,
        parent_id UUID NOT NULL,
        CONSTRAINT pk_student_parent PRIMARY KEY (student_id, parent_id),
        CONSTRAINT fk_student_parent_students FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE ON update cascade,
        CONSTRAINT fk_student_parent_parents FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_student_parent_parent_id ON student_parent(parent_id);
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS idx_student_parent_parent_id;
    """,
    """--sql
    DROP TABLE IF EXISTS student_parent;
    """,
]
