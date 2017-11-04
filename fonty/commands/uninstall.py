'''fonty.commands.uninstall.py: Command-line interface to uninstall fonts.'''
import time
import sys

import click
from termcolor import colored
from fonty.lib.task import Task, TaskStatus
from fonty.lib.variants import FontAttribute
from fonty.lib.constants import COLOR_INPUT
from fonty.lib.uninstall import uninstall_fonts
from fonty.models.manifest import Manifest

@click.command('uninstall', short_help='Uninstall a font')
@click.argument(
    'name',
    nargs=-1,
    type=click.STRING)
@click.option(
    '--variants', '-v',
    multiple=True,
    default=None,
    help='Specify which font variants to uninstall.')
@click.pass_context
def cli_uninstall(ctx, name, variants):
    '''Uninstall a font from this computer.

    \b
    Example usage:
    ==============

    \b
      Uninstall Open Sans from your computer:
      >>> fonty uninstall "Open Sans"

    \b
      Uninstall only the bold and bold italic variants of Open Sans:
      >>> fonty uninstall "Open Sans" -v 700,700i

    '''

    # Process arguments and options
    name = ' '.join(str(x) for x in name)
    if variants:
        variants = (','.join(str(x) for x in variants)).split(',')
        variants = [FontAttribute.parse(variant) for variant in variants]

    if not name:
        click.echo(ctx.get_help())
        sys.exit(1)

    # Get manifest list
    try:
        manifest = Manifest.load()
    except FileNotFoundError:
        task = Task("Generating font manifest...")
        manifest = Manifest.generate()
        manifest.save()
        task = task.stop(message='Generated font manifest file')

    # Get typeface from system
    task = Task("Searching for {}".format(colored(name, COLOR_INPUT)))
    typeface = manifest.get(name)
    if typeface is None:
        task.stop(status=TaskStatus.ERROR,
                  message="No typeface found with the name '{}'".format(
                      colored(name, COLOR_INPUT)
                  ))
        sys.exit(1)

    # Check if variants exists
    if variants:
        invalid_variants = [x for x in variants if x not in typeface.variants]
        if invalid_variants:
            task.stop(status=TaskStatus.ERROR,
                      message="Variant(s) [{}] not available".format(
                          colored(', '.join([str(v) for v in invalid_variants]), COLOR_INPUT)
                     ))
            sys.exit(1)

    if not variants:
        variants = typeface.variants

    # Uninstall this typeface
    local_fonts = typeface.get_fonts(variants)
    task.message = "Uninstalling {name} ({variants})".format(
        name=colored(typeface.name, COLOR_INPUT),
        variants=colored(', '.join([str(v) for v in variants]), 'green')
    )
    result = uninstall_fonts(local_fonts)

    # Update the font manifest
    manifest = Manifest.load()
    for font in local_fonts:
        manifest.remove(font)
    manifest.save()

    if result:
        task.stop(
            status=TaskStatus.SUCCESS,
            message="Uninstalled {name}({variants})".format(
                name=colored(typeface.name, COLOR_INPUT),
                variants=colored(', '.join([str(v) for v in variants]), 'green')
            )
        )
    else:
        task.stop(
            status=TaskStatus.ERROR,
            message="Failed to uninstall {name}({variants})".format(
                name=colored(typeface.name, COLOR_INPUT),
                variants=colored(', '.join([str(v) for v in variants]), 'green')
            )
        )
