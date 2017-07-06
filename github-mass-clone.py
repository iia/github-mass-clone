#!/usr/bin/env python

import urlparse, json, requests
import npyscreen, curses

class GitHubMassClone(npyscreen.NPSAppManaged):
    def onStart(self):
        self.TYPE_USER = 0
        self.TYPE_ORGANIZATION = 1
        self.TYPE_TRANSOPORT_GIT = 0
        self.TYPE_TRANSOPORT_SSH = 1
        self.TYPE_TRANSOPORT_CLONE = 2

        self.repositories = []

        self.addForm("MAIN",
                     FormConfiguration,
                     name="Configuration",
                     color="IMPORTANT")

        self.addFormClass("Repository Selection",
                          FormRepositorySelection,
                          name="Repository Selection",
                          color="IMPORTANT")

    def onCleanExit(self):
        pass
        #npyscreen.notify_wait("Goodbye!")

    def change_form(self, name):
        # Switch forms.  NB. Do *not* call the .edit() method directly (which
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        self.switchForm(name)

        # By default the application keeps track of every form visited.
        # There's no harm in this, but we don't need it so:
        self.resetHistory()

class FormConfiguration(npyscreen.ActionForm):
    def create(self):
        self.type = self.add(npyscreen.TitleSelectOne,
                             value = [0,],
                             name = "Type:",
                             max_height = 2,
                             values = ["User", "Organization"],
                             scroll_exit = True)

        self.add(npyscreen.FixedText,
                 editable=False,
                 value = "")

        self.type_name = self.add(npyscreen.TitleText,
                                  name = "Name:",
                                  value = "")

        self.add(npyscreen.FixedText,
                 editable=False,
                 value = "")

        self.type_transport = self.add(npyscreen.TitleSelectOne,
                                       value = [0,],
                                       name = "Type:",
                                       max_height = 3,
                                       values = ["Git", "SSH", "Clone"],
                                       scroll_exit = True)

        self.add(npyscreen.FixedText,
                 editable=False,
                 value = "")

        self.path_store = self.add(npyscreen.TitleFilenameCombo,
                                   name = "Store:",
                                   select_dir = True)


        #self.add_handlers({"^T": self.change_forms})

    def on_ok(self):
        # Clear repositories list
        self.parentApp.repositories[:] = []

        # Exit the application if the OK button is pressed.
        if not self.type.value:
            npyscreen.notify_confirm("Type not defined", title= 'Error')
            return

        if self.type.value[0] < 0 or self.type.value[0] > 1:
            npyscreen.notify_confirm("Undefined type", title= 'Error')
            return

        if not self.type_name.value:
            npyscreen.notify_confirm("Type name not defined", title= 'Error')
            return

        if self.type_transport.value[0] < 0 or self.type_transport.value[0] > 2:
            npyscreen.notify_confirm("Undefined transport type", title= 'Error')
            return

        if not self.path_store.value:
            npyscreen.notify_confirm("Path to store undefined", title= 'Error')
            return

        url = ""

        if self.type.value[0] == self.parentApp.TYPE_USER:
            url = urlparse.urljoin("https://api.github.com/users/",
                                   "/".join([self.type_name.value, "repos"]))
        elif self.type.value[0] == self.parentApp.TYPE_ORGANIZATION:
            url = urlparse.urljoin("https://api.github.com/orgs/",
                                   "/".join([self.type_name.value, "repos"]))

        headers = {"content-type": "application/json"}
        payload = {}
        response = requests.get(url, data = json.dumps(payload), headers = headers)

        if response.status_code != 200:
            npyscreen.notify_confirm("Get request failed", title= 'Error')
            return

        response_json = response.json()

        response.close()

        #check type of response_json is list
        for r in response_json:
            rd = {}

            rd["name"] = r["name"]
            rd["url_git"] = r["git_url"]
            rd["url_ssh"] = r["ssh_url"]
            rd["url_clone"] = r["clone_url"]

            self.parentApp.repositories.append(rd)

        if len(self.parentApp.repositories) < 1:
            npyscreen.notify_confirm("No repositories found", title='Error')
            return

        self.parentApp.switchForm("Repository Selection")

    def on_cancel(self):
        self.parentApp.switchForm(None)

class FormRepositorySelection(npyscreen.ActionForm):
    def create(self):
        self.repo_titles = []

        for i in range(len(self.parentApp.repositories)):
            self.repo_titles.append(self.parentApp.repositories[i]["name"])

        self.repo_selection = self.add(npyscreen.TitleMultiSelect,
                                       max_height = 16,
                                       value = [],
                                       name = "Available Repositories:",
                                       values = self.repo_titles,
                                       scroll_exit = True)

    def on_ok(self):
        # Exit the application if the OK button is pressed.
        npyscreen.notify_confirm(str(self.repo_selection), title= 'Info')
        self.parentApp.switchForm(None)

    def on_cancel(self):
        # Clear repositories list.
        self.parentApp.repositories[:] = []

        # Go back to configuration form.
        self.parentApp.switchForm("MAIN")

if __name__ == '__main__':
    gmc = GitHubMassClone()
    gmc.run()
