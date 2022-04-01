import urwid
from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    BooleanField,
    ReadOnlyField,
)

class SecureBootForm(Form):
    cancel_label = 'Back'
    info_text = ReadOnlyField('', (
        'Alpaca Linux provides pre-bootloader "shim" with a built-in certificate, '
        'signed MOKManager utility, grub and kernel (automatically locked down if '
        'Secure Boot (SB) is enabled).\n\n'
        'The currently provided shim efi image is not yet signed by Microsoft, so '
        'it cannot be loaded with SB enabled using Microsoft certificates. For it '
        'to work, the shim must be signed with your own trusted SB key from UEFI '
        'Signature Database (db) or the shim hash added there.\n\n'
        'If the option is selected, sbsigntool, efitools and mokutil packages will '
        'also be installed.'
        ))
    install_shim = BooleanField('Install "shim" and signed "grub" bootloaders for SB')

class SecureBootView(BaseView):
    title = 'Secure Boot'

    def __init__(self, controller, install_shim):
        self._controller = controller
        self._form = SecureBootForm()
        self._form.install_shim.widget.value = install_shim

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)
        super().__init__(self._form.as_screen(focus_buttons=True))

    def done(self, sender):
        self._controller.done(self._form.install_shim.widget.value)

    def cancel(self, sender=None):
        self._controller.cancel()
