# List of dependencies (migration that must be applied before this one)
dependencies = ["staff.202506200509_initial", "departments.202506231626_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS staff_department (
        staff_id UUID NOT NULL,
        department_id UUID NOT NULL,
        CONSTRAINT pk_staff_department PRIMARY KEY (staff_id),
        CONSTRAINT fk_staff_department_staff FOREIGN KEY (staff_id) REFERENCES staff (id) ON DELETE CASCADE,
        CONSTRAINT fk_staff_department_department FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE CASCADE
    );
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_staff_department_department_id ON staff_department (department_id);
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS idx_staff_department_department_id;
    """,
    """--sql
    DROP TABLE IF EXISTS staff_department;
    """,
]
