#!/usr/bin/env python

import npyscreen, curses
import urlparse, json, requests

class GitHubMassClone(npyscreen.NPSAppManaged):
    def onStart(self):
        self.TYPE_USER = 0
        self.TYPE_ORGANIZATION = 1
        self.TYPE_TRANSOPORT_GIT = 0
        self.TYPE_TRANSOPORT_SSH = 1
        self.TYPE_TRANSOPORT_CLONE = 2

        self.repositories = []

        # The form name must be "MAIN" to define entry point form-
        self.addForm("MAIN",
                     FormMain,
                     name = "GitHub Mass Clone | Settings",
                     color = "IMPORTANT")

        self.addFormClass("REPOSITORY SELECTION",
                          FormRepositorySelection,
                          name = "GitHub Mass Clone | Repository Selection",
                          color = "IMPORTANT")

        '''
        self.addFormClass("CLONING,
                          FormCloning,
                          name = "GitHub Mass Clone | Cloning",
                          color = "IMPORTANT")
        '''

    def onCleanExit(self):
        pass

    '''
    def changeForm(self, name):
        self.switchForm(name)
        self.resetHistory()
    '''

class BoxName(npyscreen.BoxTitle):
    _contained_widget = npyscreen.Textfield

class BoxType(npyscreen.BoxTitle):
    _contained_widget = npyscreen.SelectOne

class BoxTransportType(npyscreen.BoxTitle):
    _contained_widget = npyscreen.SelectOne

class BoxPathStore(npyscreen.BoxTitle):
    _contained_widget = npyscreen.FilenameCombo

class BoxRepoSelection(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiSelect

class FormMain(npyscreen.ActionForm):
    def create(self):
        self.box_type = self.add(BoxType,
                                 name = "Select Type of Entity",
                                 values = ["User", "Organization"],
                                 value =  [0],
                                 max_height = 5,
                                 scroll_exit = True)

        self.add(npyscreen.FixedText,
                 editable=False,
                 value = "")

        self.box_name = self.add(BoxName,
                                 name = "Name of the Entity",
                                 value = "",
                                 max_height = 3)

        self.add(npyscreen.FixedText,
                 editable=False,
                 value = "")

        self.box_transport_type = self.add(BoxTransportType,
                                           name = "Type of Transport",
                                           values = ["Git", "SSH", "Clone"],
                                           value = [0],
                                           max_height = 6,
                                           scroll_exit = True)

        self.add(npyscreen.FixedText,
                 editable = False,
                 value = "")

        self.box_path_store = self.add(BoxPathStore,
                                       name = "Path to Store",
                                       select_dir = True,
                                       max_height = 3)

        #self.add_handlers({"^C": self.parentApp.switchForm(None)})
        #self.add_handlers({"^D": self.parentApp.switchForm(None)})
        #self.add_handlers({"^X": self.parentApp.switchForm(None)})

    def on_ok(self):
        # Clear repositories list
        self.parentApp.repositories[:] = []

        # Exit the application if the OK button is pressed.
        if not self.box_type.value:
            npyscreen.notify_confirm("Type not defined",
                                     title = "GitHub Mass Clone | Error")

            return

        if self.box_type.value[0] < 0 or self.box_type.value[0] > 1:
            npyscreen.notify_confirm("Undefined type",
                                     title = "GitHub Mass Clone | Error")

            return

        if not self.box_name.value:
            npyscreen.notify_confirm("Type name not defined",
                                     title = "GitHub Mass Clone | Error")
            return

        if self.box_transport_type.value[0] < 0 or self.box_transport_type.value[0] > 2:
            npyscreen.notify_confirm("Undefined transport type",
                                     title = "GitHub Mass Clone | Error")

            return

        if not self.box_path_store.value:
            npyscreen.notify_confirm("Path to store undefined",
                                     title= "GitHub Mass Clone | Error")

            return

        url = ""

        if self.box_type.value[0] == self.parentApp.TYPE_USER:
            url = urlparse.urljoin("https://api.github.com/users/",
                                   "/".join([self.box_name.value, "repos"]))
        elif self.box_type.value[0] == self.parentApp.TYPE_ORGANIZATION:
            url = urlparse.urljoin("https://api.github.com/orgs/",
                                   "/".join([self.box_name.value, "repos"]))

        payload = {}
        headers = {"content-type": "application/json"}
        response = requests.get(url,
                                data = json.dumps(payload),
                                headers = headers)

        if response.status_code != 200:
            npyscreen.notify_confirm("Get request failed",
                                     title = "GitHub Mass Clone | Error")

            return

        response_json = response.json()

        response.close()

        for r in response_json:
            rd = {}

            rd["name"] = r["name"]
            rd["url_git"] = r["git_url"]
            rd["url_ssh"] = r["ssh_url"]
            rd["url_clone"] = r["clone_url"]

            self.parentApp.repositories.append(rd)

        if len(self.parentApp.repositories) < 1:
            npyscreen.notify_confirm("No repositories found",
                                     title="GitHub Mass Clone | Error")

            return

        self.parentApp.switchForm("REPOSITORY SELECTION")

    def on_cancel(self):
        self.parentApp.switchForm(None)

class FormRepositorySelection(npyscreen.ActionForm):
    def create(self):
        self.repo_names = []

        for i in range(len(self.parentApp.repositories)):
            self.repo_names.append(self.parentApp.repositories[i]["name"])

        self.box_repo_selection = self.add(BoxRepoSelection,
                                           name = "Available Repositories",
                                           values = self.repo_names,
                                           value = [],
                                           scroll_exit = True)

    def on_ok(self):
        # Exit the application if the OK button is pressed.
        npyscreen.notify_confirm(str(self.box_repo_selection.value),
                                 title = 'Info')
        self.parentApp.switchForm(None)

    def on_cancel(self):
        # Clear repositories list.
        self.parentApp.repositories[:] = []

        # Go back to configuration form.
        self.parentApp.switchForm("MAIN")

if __name__ == '__main__':
    gmc = GitHubMassClone()
    gmc.run()
