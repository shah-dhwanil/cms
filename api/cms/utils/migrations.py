from asyncpg import connect
from pathlib import Path
from datetime import datetime
from textwrap import dedent
from importlib import import_module
from typing import Optional
from cms.utils.config import Config
import argparse
import asyncio

Config.load_config()
class MigrationManager:
    POSTGRES_DSN: str = Config.get_config().POSTGRES_DSN
    applied_migrations: Optional[list[str]] = None
    migration_table_present: bool = False

    async def ensure_migrations_table(self):
        """
        Ensure that the migrations table exists in the database.
        """
        if not self.migration_table_present:
            migrations_sql = """
            CREATE TABLE IF NOT EXISTS migrations(
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT unique_migration_name UNIQUE(name)
            );
            """
            conn = await connect(self.POSTGRES_DSN)
            await conn.execute(migrations_sql)
            self.migration_table_present = True

    async def load_applied_migrations(self):
        """
        Load the list of applied migrations from the database into memory for efficiency.
        """
        if self.applied_migrations is None:
            await self.ensure_migrations_table()
            conn = await connect(self.POSTGRES_DSN)
            applied_migrations = await conn.fetch(
                "SELECT name FROM migrations ORDER BY applied_at;"
            )
            self.applied_migrations = [row["name"] for row in applied_migrations]

    def get_all_migrations(self, path: Path):
        """
        Get a list of all migrations in the given path and it's sub directories.

        Args:
            path (Path): The path to search for migrations.

        Returns:
            List[str]: List of migrations in the given path and it's sub directories.
        """
        migrations = list(
            path.glob(
                "**/" + "[0123456789]" * 12 + "_*.py"
            )  # ** maps nested directorie and "[0123456789]" * 12 maps timestamp used in naming og migration files
        )
        migrations = [
            f"{migration.parents[1].stem}.{migration.stem}"
            for migration in migrations  # migration.parents give a list of parents in bottom to top order & migration.stem gives name of the just the file or folder
        ]
        migrations.sort(
            key=lambda x: x.split(".")[1][:12]
        )  # sorts all migration based on timestamp of it's creation
        return migrations

    def import_module(self, module_name: str, slug: str):
        """
        Dynamically imports the migration file of the given module

        Args:
            module_name (str): Name of the module where the file is located
            slug (str): Name of the migration file

        Returns:
            ModuleType: Module corresponding to given inputs
        """
        return import_module(f"iems.{module_name}.migrations.{slug}")

    def generate(self, module_name: str, slug: str):
        """
        Generates a new migration file for the given module and slug.

        Args:
            module_name (str): Name of the module where new migration file is to be created
            slug (str): Name of the migration
        """
        template = """
        # List of dependencies (migration that must be applied before this one)
        dependencies = ["{last_migration}"]

        # SQL to apply the migration
        apply = []

        # SQL to rollback the migration
        rollback = []
        """
        migrations_path = Path(
            import_module(f"cms.{module_name}").__path__[0] + "/migrations"
        )
        migrations_path.mkdir(exist_ok=True)
        # To get last migration if any for the module to add it is dependency for current migration
        generated_migrations = self.get_all_migrations(migrations_path)
        if len(generated_migrations) != 0:
            template = template.format(last_migration=generated_migrations[-1])
        else:
            template = template.replace('"{last_migration}"', "")
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        migration_file = migrations_path.joinpath(f"{timestamp}_{slug}.py")
        migration_file.touch()
        migration_file.write_text(dedent(template))

    async def migrate(self):
        """
        Applies all the unapplied migrations.
        """
        await self.load_applied_migrations()
        all_migrations = self.get_all_migrations(Path("./"))
        non_applied_migrations = []
        for migration in all_migrations:
            if migration not in self.applied_migrations:
                non_applied_migrations.append(migration)
        for migration in non_applied_migrations:
            module_name, slug = migration.split(".")
            await self.apply(module_name, slug)

    async def apply(self, module_name: str, slug: str):
        """
        Applies the given migration.

        Args:
            module_name (str): Name of the module where migration is located
            slug (str): Name of the migration

        Raises:
            e: If any error occurs while executing the migration
        """
        await self.load_applied_migrations()
        migration_name = f"{module_name}.{slug}"
        conn = await connect(self.POSTGRES_DSN)
        # Checks if migration is already applied or not
        if migration_name not in self.applied_migrations:
            module = self.import_module(module_name, slug)
            # Resolve the dependency and first applies them and then applies current migration
            for dependency in module.dependencies:
                if dependency not in self.applied_migrations:
                    dep_module, dep_slug = dependency.split(".")
                    await self.apply(dep_module, dep_slug)
            async with conn.transaction():
                print("Applying Migration:- ", migration_name)
                for sql in module.apply:
                    try:
                        await conn.execute(sql)
                    except Exception as e:
                        print("Error occured while executing sql:- ", sql)
                        raise e
                await conn.execute(
                    "INSERT INTO migrations(name) VALUES($1)",
                    migration_name,
                )
                self.applied_migrations.append(migration_name)

    async def rollback(self, module_name: str, slug: str):
        """
        Rollback the given migration

        Args:
            module_name (str): Name of the module where migration is located
            slug (str): Name of the migration

        Raises:
            e: If any error occurs while executing the migration
        """
        await self.load_applied_migrations()
        migration_name = f"{module_name}.{slug}"
        if migration_name in self.applied_migrations:
            # Generates list of migrations that are needed to be rollback before rollbacking the current one
            # Currently it rollbacks all the migration applied after the migration that is to be rollbacked
            dependencies = self.applied_migrations[
                self.applied_migrations.index(migration_name) :
            ]
            dependencies.reverse()
            conn = await connect(self.POSTGRES_DSN)
            for dependency in dependencies:
                dep_module, dep_slug = dependency.split(".")
                module = self.import_module(dep_module, dep_slug)
                print("Rollbacking Migration:- ", dependency)
                async with conn.transaction():
                    for sql in module.rollback:
                        try:
                            await conn.execute(sql)
                        except Exception as e:
                            print("Error occured while executing sql:- ", sql)
                            raise e
                    await conn.execute(
                        "DELETE FROM migrations WHERE name=$1", dependency
                    )
                    self.applied_migrations.remove(dependency)


async def main():
    parser = argparse.ArgumentParser(description="Manage database migrations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("migrate", help="Apply all pending migrations.")

    generate_parser = subparsers.add_parser(
        "generate", help="Generate a new migration file."
    )
    generate_parser.add_argument("module", help="The module name.")
    generate_parser.add_argument("slug", help="The migration slug.")

    rollback_parser = subparsers.add_parser("rollback", help="Rollback a migration.")
    rollback_parser.add_argument("module", help="The module name.")
    rollback_parser.add_argument("slug", help="The migration slug.")

    apply_parser = subparsers.add_parser("apply", help="Applies a migration.")
    apply_parser.add_argument("module", help="The module name.")
    apply_parser.add_argument("slug", help="The migration slug.")

    args = parser.parse_args()

    manager = MigrationManager()

    if args.command == "migrate":
        await manager.migrate()
    elif args.command == "generate":
        manager.generate(args.module, args.slug)
    elif args.command == "rollback":
        await manager.rollback(args.module, args.slug)
    elif args.command == "apply":
        await manager.apply(args.module, args.slug)

def run_cli():
    asyncio.run(main())