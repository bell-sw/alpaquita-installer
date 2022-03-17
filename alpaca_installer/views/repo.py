import urwid

from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    URLField,
    ReadOnlyField,
    NO_HELP
)

class RepoForm(Form):
    cancel_label = 'Back'
    repo_base_url = URLField('Base URL:')
    repo_field0 = ReadOnlyField('Repositories:', help=NO_HELP)
    repo_field1 = ReadOnlyField('', help=NO_HELP)

    def __init__(self):
        super().__init__()
        self.repo_fields = [self.repo_field0, self.repo_field1]

class RepoView(BaseView):
    title = 'Installation Source'
    excerpt = ('Specify the URL of the repository server that will be used to install the packages')

    def __init__(self, controller, repo_base_url: str):
        self._controller = controller

        self._form = RepoForm()
        self._form.repo_base_url.widget.value = repo_base_url
        self.set_repos_text(repo_base_url)

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)
        urwid.connect_signal(self._form.repo_base_url.widget, 'change', self.update_repos_text)

        super().__init__(self._form.as_screen(excerpt=self.excerpt,
                                              focus_buttons=True))

    def done(self, sender):
        self._controller.done(self._form.repo_base_url.widget.value)

    def cancel(self, sender=None):
        self._controller.cancel()

    def set_repos_text(self, url):
        for r, w in zip(self._controller.get_repos(url), self._form.repo_fields):
            w.widget.value = r

    def update_repos_text(self, sender, url):
        self.set_repos_text(url)