#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, print_function

import argparse
import logging
import os
import sys
from collections import OrderedDict
from contextlib import contextmanager

from blessings import Terminal

import mondrian
from medikit.config import read_configuration, load_features
from medikit.events import LoggingDispatcher, ProjectEvent
from medikit.feature import ProjectInitializer
from medikit.pipeline import ConfiguredPipeline
from medikit.settings import DEFAULT_FEATURES, DEFAULT_FILES

# Globals

logger = mondrian.getLogger()
logger.setLevel(logging.INFO)

t = Terminal()

START = 'start'
CONTINUE = 'continue'
ABORT = 'abort'


def _read_configuration(dispatcher, config_filename):
    """
    Prepare the python context and delegate to the real configuration reader (see config.py)

    :param EventDispatcher dispatcher:
    :return tuple: (variables, features, files, config)
    """
    if not os.path.exists(config_filename):
        raise IOError('Could not find project description file (looked in {})'.format(config_filename))

    variables = OrderedDict()

    files = {filename: '' for filename in DEFAULT_FILES}
    features = set(DEFAULT_FEATURES)

    return read_configuration(dispatcher, config_filename, variables, features, files)


def main(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('--config', '-c', default='Projectfile')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    # todo aliases for update/init
    # warning: http://bugs.python.org/issue9234

    parser_init = subparsers.add_parser('init', help='Initialize a new project.')
    parser_init.set_defaults(handler=handle_init)
    parser_init.add_argument('target')
    parser_init.add_argument('--name')
    parser_init.add_argument('--description')
    parser_init.add_argument('--license')
    parser_init.add_argument('--feature', '-f', action='append', dest='features')

    parser_update = subparsers.add_parser('update', help='Update current project.')
    parser_update.set_defaults(handler=handle_update)

    parser_pipeline = subparsers.add_parser('pipeline', help='Execute multi-steps pipelines (release, etc.).')
    parser_pipeline.set_defaults(handler=handle_pipeline)
    parser_pipeline.add_argument('pipeline')
    parser_pipeline.add_argument(
        'action', choices=(
            START,
            CONTINUE,
            ABORT,
        )
    )
    parser_pipeline.add_argument('--force', '-f', action='store_true')

    options, more_args = parser.parse_known_args(args if args is not None else sys.argv[1:])
    if options.verbose:
        logger.setLevel(logging.DEBUG)

    options = vars(options)
    command, handler = options.pop('command'), options.pop('handler')

    config_filename = os.path.join(os.getcwd(), options.pop('target', '.'), options.pop('config'))

    if len(more_args):
        return handler(config_filename, more=more_args, **options)
    else:
        return handler(config_filename, **options)


@contextmanager
def _change_working_directory(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def handle_init(config_filename, **options):
    if os.path.exists(config_filename):
        raise IOError(
            'No config should be present in current directory to initialize (found {})'.format(config_filename)
        )

    config_dirname = os.path.dirname(config_filename)
    if not os.path.exists(config_dirname):
        os.makedirs(config_dirname)

    # Fast and dirty implementation
    # TODO
    # - input validation
    # - getting input from env/git conf (author...),
    # - dispatching something in selected features so maybe they can suggest deps
    # - deps selection
    # - ...
    with _change_working_directory(config_dirname):
        dispatcher = LoggingDispatcher()
        initializer = ProjectInitializer(dispatcher, options)
        initializer.execute()
        return handle_update(config_filename)


def handle_update(config_filename, **kwargs):
    dispatcher = LoggingDispatcher()

    variables, features, files, config = _read_configuration(dispatcher, config_filename)

    feature_instances = {}
    logger.info(
        'Updating {} with {} features'.format(
            t.bold(config['python'].get('name')),
            ', '.join(t.bold(t.green(feature_name)) for feature_name in sorted(features))
        )
    )

    all_features = load_features()

    sorted_features = sorted(features)  # sort to have a predictable display order
    for feature_name in sorted_features:
        logger.debug('Initializing feature {}...'.format(t.bold(t.green(feature_name))))
        try:
            feature = all_features[feature_name]
        except KeyError as exc:
            logger.exception('Feature "{}" not found.'.format(feature_name))

        if feature:
            feature_instances[feature_name] = feature(dispatcher)

            for req in feature_instances[feature_name].requires:
                if not req in sorted_features:
                    raise RuntimeError('Unmet dependency: {} requires {}.'.format(feature_name, req))

            for con in feature_instances[feature_name].conflicts:
                if con in sorted_features:
                    raise RuntimeError('Conflicting dependency: {} conflicts with {}.'.format(con, feature_name))
        else:
            raise RuntimeError('Required feature {} not found.'.format(feature_name))

    event = ProjectEvent(config=config)
    event.variables, event.files = variables, files

    # todo: add listener dump list in debug/verbose mode ?

    event = dispatcher.dispatch('medikit.on_start', event)

    dispatcher.dispatch('medikit.on_end', event)

    logger.info('Done.')


def _handle_pipeline_action(pipeline, action, *, filename, force=False):
    if action == START:
        if os.path.exists(filename):
            if force:
                os.unlink(filename)
            else:
                raise FileExistsError('Already started, use --force to force a restart, or use continue.')
        pipeline.init()
        with open(filename, 'w+') as f:
            f.write(pipeline.serialize())
        return CONTINUE
    elif action == CONTINUE:
        assert os.path.exists(filename)
        with open(filename) as f:
            pipeline.unserialize(f.read())

        try:
            step = pipeline.next()
            step.logger.info('Running {}.'.format(step))
            step.run(pipeline.meta)
            if step.complete:
                step.logger.info('{} is complete, moving forward.'.format(step))
            else:
                step.logger.warning('{} is NOT complete after run, exiting.'.format(step))
                return

        except StopIteration:
            return

        with open(filename, 'w+') as f:
            f.write(pipeline.serialize())

        return CONTINUE
    elif action == ABORT:
        assert os.path.exists(filename)
        try:
            with open(filename) as f:
                pipeline.unserialize(f.read())
            pipeline.abort()
        finally:
            os.unlink(filename)
    else:
        return


def handle_pipeline(config_filename, *, pipeline, action, force=False, verbose=False):
    dispatcher = LoggingDispatcher()
    variables, features, files, config = _read_configuration(dispatcher, config_filename)

    if not pipeline in config.pipelines:
        raise ValueError(
            'Undefined pipeline {!r}. Valid choices are: {}.'.format(
                pipeline, ', '.join(sorted(config.pipelines.keys()))
            )
        )
    pipeline = ConfiguredPipeline(pipeline, config.pipelines[pipeline])
    path = os.path.dirname(config_filename)
    pipeline_file = os.path.join(path, '.medikit-pipeline')

    while action:
        action = _handle_pipeline_action(pipeline, action, filename=pipeline_file, force=force)
        force = False


if __name__ == '__main__':
    main()
