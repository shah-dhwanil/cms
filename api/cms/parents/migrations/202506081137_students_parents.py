# List of dependencies (migration that must be applied before this one)
dependencies = ["parents.202506080839_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS students_parents(
        parent_id UUID NOT NULL,
        student_id UUID NOT NULL,
        CONSTRAINT pk_students_parents PRIMARY KEY (parent_id, student_id),
        CONSTRAINT uniq_students_parents_student_id UNIQUE (student_id),
        CONSTRAINT fk_students_parents_parents FOREIGN KEY (parent_id) REFERENCES parents(id),
        CONSTRAINT fk_students_parents_students FOREIGN KEY (student_id) REFERENCES students(id)
    );
    """
    """
    CREATE INDEX idx_students_parents_parent_id ON students_parents (parent_id);
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX idx_students_parents_parent_id;
    """
    """--sql
    DROP TABLE students_parents;
    """
]
