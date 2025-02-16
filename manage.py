import click
from alembic.config import Config
from alembic import command
import os
import shutil

@click.group()
def cli():
    pass

@cli.command()
@click.option('--force', is_flag=True, help='Force initialization by removing existing migrations')
def init(force):
    """Initialize migrations"""
    migrations_dir = "migrations"
    if force and os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)
        click.echo(f"Removed existing {migrations_dir} directory")
    
    alembic_cfg = Config("alembic.ini")
    try:
        command.init(alembic_cfg, "migrations")
        click.echo("Successfully initialized migrations directory")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        click.echo("Use --force to reinitialize")

@cli.command()
@click.argument('message')
def migrate(message):
    """Create a new migration"""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=True)

@cli.command()
def upgrade():
    """Apply all migrations"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

@cli.command()
def downgrade():
    """Revert last migration"""
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "-1")

if __name__ == '__main__':
    cli()