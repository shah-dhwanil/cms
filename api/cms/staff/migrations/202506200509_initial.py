# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial"]

# SQL to apply the migration
apply = [
    """--sql    
    CREATE TABLE IF NOT EXISTS staff (
        id UUID,
        first_name VARCHAR(32) NOT NULL,
        last_name VARCHAR(32) NOT NULL,
        position VARCHAR(64) NOT NULL,
        education JSON NOT NULL,
        experience JSON NOT NULL,
        activity JSON NOT NULL,
        other_details JSON,
        is_public BOOL DEFAULT TRUE,
        is_active BOOL DEFAULT TRUE,
        CONSTRAINT pk_staff PRIMARY KEY (id),
        CONSTRAINT fk_staff_users FOREIGN KEY (id,is_active) REFERENCES users(id,is_active) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS staff;
    """
]
