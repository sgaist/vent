import npyscreen
import threading
import time

from vent.api.actions import Action
from vent.api.plugins import Plugin
from vent.menus.add_options import AddOptionsForm


class AddForm(npyscreen.ActionForm):
    """ For for adding a new repo """
    def create(self):
        """ Create widgets for AddForm """
        self.add_handlers({"^T": self.switch, "^Q": self.quit})
        self.add(npyscreen.Textfield,
                 value='Add a plugin from a Git repository or an image from a '
                       'Docker registry.',
                 editable=False,
                 color="STANDOUT")
        self.add(npyscreen.Textfield,
                 value='For Git repositories, you can optionally specify a '
                       'username and password',
                 editable=False,
                 color="STANDOUT")
        self.add(npyscreen.Textfield,
                 value='for private repositories.',
                 editable=False,
                 color="STANDOUT")
        self.add(npyscreen.Textfield,
                 value='For Docker images, specify a name for referencing the '
                       'image that is being',
                 editable=False,
                 color="STANDOUT")
        self.add(npyscreen.Textfield,
                 value='added and optionally override the tag and/or the '
                       'registry and specify',
                 editable=False,
                 color="STANDOUT")
        self.add(npyscreen.Textfield,
                 value='comma-separated groups this image should belong to.',
                 editable=False,
                 color="STANDOUT")
        self.nextrely += 1
        self.repo = self.add(npyscreen.TitleText,
                             name='Repository',
                             value='https://github.com/cyberreboot/vent-plugins')
        self.user = self.add(npyscreen.TitleText, name='Username')
        self.pw = self.add(npyscreen.TitlePassword, name='Password')
        self.nextrely += 1
        self.add(npyscreen.TitleText,
                 name='OR',
                 editable=False,
                 labelColor="STANDOUT")
        self.nextrely += 1
        self.image = self.add(npyscreen.TitleText, name='Image')
        self.link_name = self.add(npyscreen.TitleText,
                                  name='Name')
        self.tag = self.add(npyscreen.TitleText, name='Tag', value='latest')
        self.registry = self.add(npyscreen.TitleText,
                                 name='Registry',
                                 value='docker.io')
        self.groups = self.add(npyscreen.TitleText, name='Groups')
        self.repo.when_value_edited()

    def switch(self, *args, **kwargs):
        """ Wrapper that switches to HELP form """
        self.parentApp.change_form("HELP")

    def quit(self, *args, **kwargs):
        """ Overridden to switch back to MAIN form """
        self.parentApp.switchForm("MAIN")

    def on_ok(self):
        """ Add the repository """
        def popup(thr, add_type, title):
            """
            Start the thread and display a popup of the plugin being cloned
            until the thread is finished
            """
            thr.start()
            tool_str = 'Cloning repository...'
            if add_type == 'image':
                tool_str = 'Pulling image...'
            npyscreen.notify_wait(tool_str, title=title)
            while thr.is_alive():
                time.sleep(1)
            return

        if self.image.value and self.link_name.value:
            api_action = Action()
            thr = threading.Thread(target=api_action.add_image, args=(),
                                   kwargs={'image': self.image.value,
                                           'link_name': self.link_name.value,
                                           'tag': self.tag.value,
                                           'registry': self.registry.value,
                                           'groups': self.groups.value})
            popup(thr, 'image', 'Please wait, adding image...')
            npyscreen.notify_confirm('Done adding image.', title='Added image')
            self.quit()
        elif self.image.value:
            npyscreen.notify_confirm("A name needs to be supplied for "
                                     "the image being added!",
                                     title="Specify a name for the image",
                                     form_color='CAUTION')
        elif self.repo.value:
            self.parentApp.repo_value['repo'] = self.repo.value
            api_plugin = Plugin()
            thr = threading.Thread(target=api_plugin.clone, args=(),
                                   kwargs={'repo': self.repo.value,
                                           'user': self.user.value,
                                           'pw': self.pw.value})
            popup(thr, 'repository', 'Please wait, adding repository...')
            self.parentApp.addForm("ADDOPTIONS",
                                   AddOptionsForm,
                                   name="Set options for new plugin"
                                        "\t\t\t\t\t\tPress ^Q to quit",
                                   color="CONTROL")
            self.parentApp.change_form('ADDOPTIONS')
        else:
            npyscreen.notify_confirm("Either a repository or an image "
                                     "name must be specified!",
                                     title="Specify plugin to add",
                                     form_color='CAUTION')
        return

    def on_cancel(self):
        """ When user clicks cancel, will return to MAIN """
        self.quit()
