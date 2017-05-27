# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

from edgy.project.events import subscribe

from . import Feature, SUPPORT_PRIORITY


class YapfFeature(Feature):
    requires = {'python'}

    @subscribe('edgy.project.feature.python.on_generate')
    def on_python_generate(self, event):
        if not 'extras_require' in event.setup:
            event.setup['extras_require'] = {}

        if not 'dev' in event.setup['extras_require']:
            event.setup['extras_require']['dev'] = []

        event.setup['extras_require']['dev'].append('yapf')

    @subscribe('edgy.project.feature.make.on_generate', priority=SUPPORT_PRIORITY)
    def on_make_generate(self, event):
        makefile = event.makefile
        makefile['YAPF'] = '$(PYTHON_DIRNAME)/yapf'
        makefile['YAPF_OPTIONS'] = '-rip'
        makefile.add_target(
            'format', '''
            $(YAPF) $(YAPF_OPTIONS) .
        ''', deps=('install-dev',), phony=True
        )

    @subscribe('edgy.project.on_start', priority=SUPPORT_PRIORITY)
    def on_start(self, event):
        self.render_file('.style.yapf', 'yapf/style.yapf.j2')


__feature__ = YapfFeature
