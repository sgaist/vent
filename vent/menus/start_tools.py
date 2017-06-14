import npyscreen
import threading
import time

from vent.api.actions import Action
from vent.api.plugins import Plugin
from vent.helpers.logs import Logger
from vent.helpers.meta import Containers
from vent.helpers.meta import Images
from vent.helpers.meta import Tools

class StartToolsForm(npyscreen.ActionForm):
    """ For picking which tools to start """
    api_action = Action()
    tools_tc = {}
    logger = Logger(__name__)

    def create(self):
        """ Update with current tools that are not cores """
        self.add_handlers({"^T": self.change_forms, "^Q": self.quit})
        self.add(npyscreen.FixedText, name='Select which tools to start (only enabled, built, non-running plugin tools are shown):', editable=False)

        i = 4
        response = self.api_action.inventory(choices=['repos', 'tools', 'built', 'enabled', 'running', 'core'])
        if response[0]:
            inventory = response[1]
            for repo in inventory['repos']:
                if repo != 'https://github.com/cyberreboot/vent':
                    repo_name = repo.rsplit("/", 2)[1:]
                    self.tools_tc[repo] = {}
                    title_text = self.add(npyscreen.TitleText, name='Plugin: '+repo, editable=False, rely=i, relx=5)
                    i += 1
                    for tool in inventory['tools']:
                        r_name = tool[0].split(":")
                        if repo_name[0] == r_name[0] and repo_name[1] == r_name[1]:
                            core = False
                            running = False
                            built = False
                            enabled = False
                            for item in inventory['core']:
                                if tool[0] == item[0]:
                                    core = True
                            for item in inventory['running']:
                                if tool[0] == item[0] and item[2] == 'running':
                                    running = True
                            for item in inventory['built']:
                                if tool[0] == item[0] and item[2] == 'yes':
                                    built = True
                            for item in inventory['enabled']:
                                if tool[0] == item[0] and item[2] == 'yes':
                                    enabled = True
                            t = tool[1]
                            if t == "":
                                t = "/"
                            if not core and not running and built and enabled:
                                t += ":" + ":".join(tool[0].split(":")[-2:])
                                self.tools_tc[repo][t] = self.add(npyscreen.CheckBox, name=t, value=True, relx=10)
                                i += 1
                    i += 2
        return

    def quit(self, *args, **kwargs):
        self.parentApp.switchForm("MAIN")

    def on_ok(self):
        """
        Take the tool selections and start them
        """
        def diff(first, second):
            """
            Get the elements that exist in the first list and not in the second
            """
            second = set(second)
            return [item for item in first if item not in second]

        def popup(original, orig_type, thr, title):
            """
            Start the thread and display a popup of info
            until the thread is finished
            """
            thr.start()
            info_str = ""
            while thr.is_alive():
                if orig_type == 'containers':
                    info = diff(Containers(), original)
                elif orig_type == 'images':
                    info = diff(Images(), original)
                if info:
                    info_str = ""
                for entry in info:
                    # TODO limit length of info_str to fit box
                    info_str += entry[0]+": "+entry[1]+"\n"
                npyscreen.notify_wait(info_str, title=title)
                time.sleep(1)
            return

        original_containers = Containers()

        tool_dict = {}
        for repo in self.tools_tc:
            for tool in self.tools_tc[repo]:
                self.logger.info(tool)
                if self.tools_tc[repo][tool].value:
                    t = tool
                    if t.startswith('/:'):
                        t = " "+t[1:]
                    t = t.split(":")
                    status = self.api_action.prep_start(name=t[0], branch=t[1], version=t[2])
                    if status[0]:
                        tool_dict.update(status[1])
        thr = threading.Thread(target=self.api_action.start, args=(), kwargs={'tool_dict':tool_dict})
        popup(original_containers, "containers", thr,
              'Please wait, starting containers...')
        npyscreen.notify_confirm("Done starting containers.",
                                 title='Started containers')
        self.quit()

    def on_cancel(self):
        self.quit()

    def change_forms(self, *args, **keywords):
        """ Toggles to main """
        change_to = "MAIN"

        # Tell the VentApp object to change forms.
        self.parentApp.change_form(change_to)