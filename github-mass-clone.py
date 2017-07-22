#!/usr/bin/env python

import npyscreen, curses
import urlparse, json, requests, subprocess

class GitHubMassClone(npyscreen.NPSAppManaged):
    def onStart(self):
        self.TYPE_USER = 0
        self.TYPE_ORGANIZATION = 1
        self.TYPE_TRANSOPORT_GIT = 0
        self.TYPE_TRANSOPORT_SSH = 1
        self.TYPE_TRANSOPORT_CLONE = 2

        self.url_chosen = None
        self.repositories = []
        self.path_store = None

        # Set a theme.
        npyscreen.setTheme(npyscreen.Themes.ElegantTheme)

        # The form name must be "MAIN" to define entry point form.
        self.form_main = self.addForm("MAIN",
                                      FormMain,
                                      name = "GitHub Mass Clone | Settings")

        self.form_repository_selection = self.addForm("REPOSITORY SELECTION",
                                                      FormRepositorySelection,
                                                      name = "GitHub Mass Clone | Repository Selection")

    def changeForm(self, name):
        self.switchForm(name)
        self.resetHistory()

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

class FormMain(npyscreen.FormBaseNew):
    def create(self):
        self.repo_names = []

        self.box_type = self.add(BoxType,
                                 name = "Select Type of Entity",
                                 values = ["User", "Organization"],
                                 value =  [0],
                                 max_height = 5,
                                 scroll_exit = True)

        self.nextrely += 1

        self.box_name = self.add(BoxName,
                                 name = "Name of the Entity",
                                 value = "",
                                 max_height = 3)

        self.nextrely += 1

        self.box_transport_type = self.add(BoxTransportType,
                                           name = "Type of Transport",
                                           values = ["Git", "SSH", "Clone"],
                                           value = [0],
                                           max_height = 6,
                                           scroll_exit = True)

        self.nextrely += 1

        self.box_path_store = self.add(BoxPathStore,
                                       name = "Path to Store",
                                       select_dir = True,
                                       max_height = 3)

        self.nextrely += 1

        self.button_ok = self.add(npyscreen.ButtonPress,
                                  name = "OK",
                                  when_pressed_function = self.button_ok_pressed)

        self.nextrely -= 1
        self.nextrelx += 6

        self.button_exit = self.add(npyscreen.ButtonPress,
                                    name = "Exit",
                                    when_pressed_function = self.button_exit_pressed)

    def button_ok_pressed(self):
        # Clear repositories list.
        self.parentApp.repositories[:] = []

        # Some form input checks.
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
        self.parentApp.path_store = self.box_path_store.value
        self.parentApp.url_chosen = self.box_transport_type.value[0]

        if self.box_type.value[0] == self.parentApp.TYPE_USER:
            url = urlparse.urljoin("https://api.github.com/users/",
                                   "/".join([self.box_name.value, "repos"]))
        elif self.box_type.value[0] == self.parentApp.TYPE_ORGANIZATION:
            url = urlparse.urljoin("https://api.github.com/orgs/",
                                   "/".join([self.box_name.value, "repos"]))

        response = requests.get(url, headers = {"content-type": "application/json"})

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
            rd["status_message"] = "-"

            self.parentApp.repositories.append(rd)

        if len(self.parentApp.repositories) < 1:
            npyscreen.notify_confirm("No repositories found",
                                     title="GitHub Mass Clone | Error")

            return

        self.repo_names[:] = []

        for r in self.parentApp.repositories:
            self.repo_names.append(r["name"])

        self.parentApp.form_repository_selection.box_repo_selection.values = self.repo_names
        self.parentApp.form_repository_selection.box_repo_selection.value = None

        self.parentApp.changeForm("REPOSITORY SELECTION")

    def button_exit_pressed(self):
        self.parentApp.changeForm(None)

class FormRepositorySelection(npyscreen.FormBaseNew):
    def create(self):
        self.box_repo_selection = self.add(BoxRepoSelection,
                                           name = "Available Repositories",
                                           values = [],
                                           max_height = 24,
                                           scroll_exit = True)

        self.button_ok = self.add(npyscreen.ButtonPress,
                                  name = "OK",
                                  when_pressed_function = self.button_ok_pressed)

        self.nextrely -= 1
        self.nextrelx += 6

        self.button_back = self.add(npyscreen.ButtonPress,
                                    name = "Back",
                                    when_pressed_function = self.button_back_pressed)

        self.nextrely -= 1
        self.nextrelx += 8

        self.button_exit = self.add(npyscreen.ButtonPress,
                                    name = "Exit",
                                    when_pressed_function = self.button_exit_pressed)

    def button_ok_pressed(self):
        if len(self.box_repo_selection.value) < 1:
            npyscreen.notify_confirm("No repositories selected.",
                                     title = 'GitHub Mass Clone | Info')

            return

        self.repos_selected = self.box_repo_selection.value
        self.repos_selected.sort()

        # Do the actual cloning and keep updating ther progress form.
        for idx in self.repos_selected:
            ps = None
            stdout = None
            stderr = None
            repo_name = self.box_repo_selection.values[idx]

            self.box_repo_selection.values[idx] = repo_name + " >>> Processing... <<<"
            self.box_repo_selection.display()
            #import time
            #time.sleep(2)
            #continue

            if self.parentApp.url_chosen == self.parentApp.TYPE_TRANSOPORT_GIT:
                ps = subprocess.Popen("git clone --quiet " + self.parentApp.repositories[idx]["url_git"], cwd = self.parentApp.path_store, stdout = subprocess.PIPE, shell = True)
            elif self.parentApp.url_chosen == self.parentApp.TYPE_TRANSOPORT_SSH:
                ps = subprocess.Popen("git clone --quiet " + self.parentApp.repositories[idx]["url_ssh"], cwd = self.parentApp.path_store, stdout = subprocess.PIPE, shell = True)
            elif self.parentApp.url_chosen == self.parentApp.TYPE_TRANSOPORT_CLONE:
                ps = subprocess.Popen("git clone --quiet " + str(self.parentApp.repositories[idx]["url_clone"]) , cwd = self.parentApp.path_store, stdout = subprocess.PIPE, shell = True)

            stdout, stderr = ps.communicate()

            if ps.returncode != 0:
                if stderr:
                    self.parentApp.repositories[idx]["status_message"] = stderr

                if stdout:
                    self.parentApp.repositories[idx]["status_message"] = self.parentApp.repositories[idx]["status_message"] + " " + stdout
            else:
                self.parentApp.repositories[idx]["status_message"] = "OK"

            # TODO: Handle newline.
            self.box_repo_selection.values[idx] = repo_name + " >>> " + self.parentApp.repositories[idx]["status_message"] + " <<<"
            self.box_repo_selection.display()

    def button_back_pressed(self):
        # Clear repositories list.
        self.parentApp.repositories[:] = []

        # Go back to configuration form.
        self.parentApp.changeForm("MAIN")

    def button_exit_pressed(self):
        self.parentApp.changeForm(None)

if __name__ == '__main__':
    gmc = GitHubMassClone()
    gmc.run()
