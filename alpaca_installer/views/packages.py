#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import urwid
from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    SubForm,
    SubFormField,
    BooleanField,
    ChoiceField,
    NO_HELP
)

class KernelForm(SubForm):
    extramods = BooleanField('Install firmware and extra modules')

class JDKForm(SubForm):
    jdk_8  = BooleanField('JDK 8', help=NO_HELP)
    jdk_11 = BooleanField('JDK 11', help=NO_HELP)
    jdk_17 = BooleanField('JDK 17')

class NIKForm(SubForm):
    nik_21_11 = BooleanField('NIK 21-11', help=NO_HELP)
    nik_21_17 = BooleanField('NIK 21-17', help=NO_HELP)
    nik_22_11 = BooleanField('NIK 22-11', help=NO_HELP)
    nik_22_17 = BooleanField('NIK 22-17')

class LibcForm(SubForm):
    perf = BooleanField('Install musl-perf with CPU features detection and optimized asm functions')


class OtherForm(SubForm):
    ssh_server = BooleanField('OpenSSH server', help=NO_HELP)


class PackagesForm(Form):
    cancel_label = 'Back'
    kernel = SubFormField(KernelForm, 'Linux kernel')
    jdk = SubFormField(JDKForm, 'Liberica JDK')
    nik = SubFormField(NIKForm, 'Liberica Native Image Kit')
    libc = SubFormField(LibcForm, 'libc')
    other = SubFormField(OtherForm, 'Other components')


class PackagesView(BaseView):
    title = 'Packages'
    excerpt = 'Select additional packages to install.'

    def __init__(self, controller, data, is_musl):
        self._controller = controller
        self._form = PackagesForm()
        self._form.kernel.widget.value = data.get('kernel')

        for k, f  in [('kernel', self._form.kernel),
                      ('jdk', self._form.jdk),
                      ('nik', self._form.nik),
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
            'nik': self._form.nik.widget.value,
            'libc': self._form.libc.widget.value,
            'other': self._form.other.widget.value,
            })

    def cancel(self, sender=None):
        self._controller.cancel()
