#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import urwid
from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    SubForm,
    SubFormField,
    BooleanField,
    NO_HELP
)


class KernelForm(SubForm):
    extramods = BooleanField('Install firmware and extra modules',
                             help=('info_minor', (
                                 'This option installs components which may be required for '
                                 'operating Alpaquita Linux on bare-metal machines.')))


class JavaForm(SubForm):
    jdk_8 = BooleanField('Liberica Standard JDK 8', help=NO_HELP)
    jdk_11 = BooleanField('Liberica Standard JDK 11', help=NO_HELP)
    jdk_17 = BooleanField('Liberica Standard JDK 17', help=NO_HELP)
    nik_22_11 = BooleanField('Liberica Native Image Kit 22 (Java 11)', help=NO_HELP)
    nik_22_17 = BooleanField('Liberica Native Image Kit 22 (Java 17)', help=NO_HELP)


class LibcForm(SubForm):
    perf = BooleanField('Install musl-perf with CPU features detection and optimized asm functions',
                        help=NO_HELP)


class OtherForm(SubForm):
    ssh_server = BooleanField('Enable SSH access', help=NO_HELP)
    coreutils = BooleanField('Install GNU Core Utilities',
                             help=('info_minor', (
                                 'This option installs basic file, shell and text manipulation utilities '
                                 'from the GNU coreutils project on top of busybox (which is always '
                                 'installed by default).')))


class PackagesForm(Form):
    ok_label = 'Next'
    cancel_label = 'Back'
    kernel = SubFormField(KernelForm, 'Linux kernel')
    jdk = SubFormField(JavaForm, 'Java')
    libc = SubFormField(LibcForm, 'libc')
    other = SubFormField(OtherForm, 'Other components', help=NO_HELP)


class PackagesView(BaseView):
    title = 'Packages'
    excerpt = ('info_minor', 'Select additional packages to install.')

    def __init__(self, controller, data, is_musl):
        self._controller = controller
        self._form = PackagesForm()
        self._form.kernel.widget.value = data.get('kernel')

        for k, f in [('kernel', self._form.kernel),
                     ('jdk', self._form.jdk),
                     ('libc', self._form.libc),
                     ('other', self._form.other)]:
            if k in data:
                f.widget.value = data.get(k)

        if not is_musl:
            self._form.libc.enabled = False

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)
        super().__init__(self._form.as_screen(excerpt=self.excerpt,
                                              focus_buttons=True))

    def done(self, sender):
        self._controller.done({
            'kernel': self._form.kernel.widget.value,
            'jdk': self._form.jdk.widget.value,
            'libc': self._form.libc.widget.value,
            'other': self._form.other.widget.value,
            })

    def cancel(self, sender=None):
        self._controller.cancel()
