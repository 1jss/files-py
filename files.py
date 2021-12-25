#!/usr/bin/python3
# version: 21-12-25

import os, subprocess, sys, shutil, time

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, Gio
from gi.repository.GdkPixbuf import Pixbuf


COL_PATH = 0
COL_PIXBUF = 1
COL_IS_DIRECTORY = 2
SELECTION_SINGLE = 1

class Files():

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        Gtk.main_quit()

    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_icon_from_file('/usr/share/icons/hicolor/64x64/apps/files.svg')

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.connect("key-press-event", self.on_key_press)
        self.window.set_default_size(810, 600)

        self.home_directory = os.path.realpath(os.path.expanduser('~')) # get home directory
        self.current_directory = "" # Path to current directory
        # Check if there is a valid path as argument
        if len(sys.argv) > 1 and os.path.isdir(str(sys.argv[1])):
            self.current_directory = str(sys.argv[1]) # get startup argument
        else:
            self.current_directory = self.home_directory
        self.full_path = self.current_directory # Path to chosen file or folder
        self.show_hidden = False

        self.container = Gtk.VBox(homogeneous=False, spacing=0)

        self.toolbar = Gtk.Toolbar()
        self.container.pack_start(self.toolbar, False, False, 0)

        self.upButton = Gtk.ToolButton.new()
        self.upButton.set_icon_name('go-up')
        self.toolbar.insert(self.upButton, -1)

        self.pathBar = Gtk.Entry()
        self.pathBarToolItem = Gtk.ToolItem.new()
        self.pathBarToolItem.set_expand(True)
        self.pathBarToolItem.add(self.pathBar)
        self.toolbar.insert(self.pathBarToolItem, -1)

        self.homeButton = Gtk.ToolButton.new()
        self.homeButton.set_icon_name('go-home')
        self.toolbar.insert(self.homeButton, -1)

        self.genericFileIcon = self.get_icon("gtk-file")
        self.dirIcon = self.get_icon("folder")

        self.view = Gtk.ScrolledWindow()
        self.container.pack_start(self.view, True, True, 0)

        self.set_window_title()
        self.set_path()

        self.iconView = Gtk.IconView.new()
        self.iconView.set_selection_mode(Gtk.SelectionMode(SELECTION_SINGLE))
        self.iconView.set_margin(16)
        self.iconView.set_item_width(64)
        self.iconView.set_activate_on_single_click(True)

        self.pathBar.connect("activate", self.load_path)
        self.upButton.connect("clicked", self.on_up_clicked)
        self.homeButton.connect("clicked", self.on_home_clicked)

        self.fill_store()

        self.iconView.set_text_column(COL_PATH) # Constant: 0
        self.iconView.set_pixbuf_column(COL_PIXBUF) # Constant: 1

        self.iconView.connect("button-press-event", self.on_button_pressed)
        self.iconView.connect("item-activated", self.on_item_activated)

        self.view.add(self.iconView)
        self.iconView.grab_focus()

        self.window.add(self.container)
        self.window.show_all()

    def get_icon(self, name):
        theme = Gtk.IconTheme.get_default()
        return theme.load_icon(name, 64, 0)

    def fill_store(self):
        store = Gtk.ListStore(str, Pixbuf, bool)
        if self.current_directory == None:
            return

        #before = time.perf_counter()
        self.theme = Gtk.IconTheme.get_default() # get default theme
        folder_content = sorted(os.listdir(self.current_directory),key=str.lower)
        if len(folder_content) < 200:
            for fl in folder_content:
                if self.show_hidden or not fl[0] == '.': # filter hidden files
                    # Check if directory or not and append to store
                    if os.path.isdir(os.path.join(self.current_directory, fl)):
                        store.append([fl, self.dirIcon, True])
                    else:
                        self.currentFileIcon = self.genericFileIcon # fallback icon
                        path = os.path.join(self.current_directory, fl) # current file
                        self.mimeType = Gio.content_type_guess(filename=path)[0] # guess mime type
                        if self.mimeType is not None:
                            # get icon name from mime type
                            self.iconName = Gio.content_type_get_icon(self.mimeType)
                            # check if theme has mime type icon 
                            if self.theme.has_icon(self.iconName.get_names()[0]):
                                # set icon
                                self.currentFileIcon = self.get_icon(self.iconName.get_names()[0])
                            else:
                                # get generic icon name
                                self.iconName = Gio.content_type_get_generic_icon_name(self.mimeType)
                                 # check if theme has generic icon
                                if self.theme.has_icon(self.iconName):
                                    # set generic icon
                                    self.currentFileIcon = self.get_icon(self.iconName)
                        # fill store
                        store.append([fl, self.currentFileIcon, False])
        else:
            for fl in folder_content:
                if os.path.isdir(self.current_directory + "/" + fl):
                    store.append([fl, self.dirIcon , True])
                else:
                    store.append([fl, self.genericFileIcon , False])
                
        #print("Time: " + str(time.perf_counter()-before))
        self.iconView.set_model(store)


    def set_window_title(self):
        self.window.set_title(self.current_directory)

    # Take text in pathBar and load it as current directory
    def load_path(self, widget):
        newPath = self.pathBar.get_text()
        if os.path.exists(newPath):
            self.current_directory = newPath
            self.fill_store()
            sensitive = True
            if self.current_directory == "/": sensitive = False
            self.upButton.set_sensitive(sensitive)
            self.set_window_title()
        else:
            self.set_path()

    # Take the current directory path and set ut as text in the pathBar
    def set_path(self):
        self.pathBar.set_text(self.current_directory)

    def on_home_clicked(self, widget):
        self.current_directory = self.home_directory
        self.full_path = self.current_directory
        self.fill_store()
        self.upButton.set_sensitive(True)
        self.set_window_title()
        self.set_path()

    # When right-clicking in the icon view
    def on_button_pressed(self, widget, event):
        if event.button == 3: # 3 = right mouse button
            targetIcon = widget.get_path_at_pos(int(event.x),int(event.y)) # get which icon that was clicked
            if targetIcon: # if the user clicked an icon (and not just in the window)
                model = widget.get_model()
                path = model[targetIcon][COL_PATH]
                isDir = model[targetIcon][COL_IS_DIRECTORY]
                self.full_path = os.path.join(self.current_directory, path)

                contextMenu = Gtk.Menu()

                if not isDir:
                    openAsTextMenuItem = Gtk.MenuItem()
                    openAsTextMenuItem.set_label("Open as text")
                    openAsTextMenuItem.connect("activate", self.open_as_text)
                    contextMenu.add(openAsTextMenuItem)

                renameMenuItem = Gtk.MenuItem()
                renameMenuItem.set_label("Rename...")
                renameMenuItem.connect("activate", self.rename_action)
                contextMenu.add(renameMenuItem)
                                
                moveMenuItem = Gtk.MenuItem()
                moveMenuItem.set_label("Move to...")
                moveMenuItem.connect("activate", self.move_to)
                contextMenu.add(moveMenuItem)

                copyMenuItem = Gtk.MenuItem()
                copyMenuItem.set_label("Copy to...")
                copyMenuItem.connect("activate", self.copy_to)
                contextMenu.add(copyMenuItem)

                deleteMenuItem = Gtk.MenuItem()
                deleteMenuItem.set_label("Delete")
                deleteMenuItem.connect("activate", self.delete_action)
                contextMenu.add(deleteMenuItem)

                contextMenu.show_all()
                Gtk.Menu.popup_at_pointer(contextMenu)

            else: # if the user clicked in the window, but not on an icon
                print("Clicked on the window")
                contextMenu = Gtk.Menu()
                self.full_path = self.current_directory
                
                newFileMenuItem = Gtk.MenuItem()
                newFileMenuItem.set_label("New file...")
                newFileMenuItem.connect("activate", self.new_file)
                contextMenu.add(newFileMenuItem)
                
                newFolderMenuItem = Gtk.MenuItem()
                newFolderMenuItem.set_label("New folder...")
                newFolderMenuItem.connect("activate", self.new_folder)
                contextMenu.add(newFolderMenuItem)

                terminalMenuItem = Gtk.MenuItem()
                terminalMenuItem.set_label("Open folder in terminal")
                terminalMenuItem.connect("activate", self.open_in_terminal)
                contextMenu.add(terminalMenuItem)

                contextMenu.show_all()
                Gtk.Menu.popup_at_pointer(contextMenu)

    # When activating (left-click, enter or space) on an icon
    def on_item_activated(self, widget, item):
        model = widget.get_model()
        path = model[item][COL_PATH]
        isDir = model[item][COL_IS_DIRECTORY]
        self.full_path = os.path.normpath(os.path.join(self.current_directory, path))
        if not isDir:
            subprocess.call(["xdg-open", self.full_path])
            return

        self.current_directory = self.full_path
        self.fill_store()
        self.upButton.set_sensitive(True)
        self.set_window_title()
        self.set_path()

    def open_as_text(self, widget):
        print("Open as text:")
        print(self.full_path)
        import re        
        subprocess.Popen("lxterminal --command='micro " + re.escape(self.full_path) + "'", shell=True)

    def rename_action(self, widget):
        print("Rename file or folder:")
        rename_to_path = self.show_input_dialog(widget, 'Rename', 'What do you want to call  \'' + self.full_path + '\'?')
        if rename_to_path:
            self.make_parent_path(rename_to_path)
            os.rename(self.full_path, rename_to_path)
            self.fill_store()
            print(rename_to_path)
        else:
            print("Canceled")
        
    def delete_action(self, widget):
        print("Delete file or folder:")
        delete_path = self.show_question_dialog(widget, 'Delete Item', 'Do you really want to delete \'' + self.full_path + '\'?')
        if delete_path:
            if(os.path.isfile(delete_path)):
            	os.remove(delete_path)
            elif(os.path.isdir(delete_path)):
                shutil.rmtree(delete_path)
            self.fill_store()
            print(delete_path)
        else:
            print("Canceled")

    def new_folder(self, widget):
        print("Create new folder here:")
        new_folder_path = self.show_input_dialog(widget, 'Create New Folder', 'Where do you want to create a new folder?')
        if new_folder_path:
            os.makedirs(new_folder_path)
            self.fill_store()
            print(new_folder_path)
        else:
            print("Canceled")

    def new_file(self, widget):
        print("Create new file here:")
        new_file_path = self.show_input_dialog(widget, 'Create New File', 'What do you want to call your new file?')
        if new_file_path:
            self.make_parent_path(new_file_path)
            open(new_file_path, 'a').close()
            self.fill_store()
            print(new_file_path)
        else:
            print("Canceled")

    def move_to(self, widget):
        print("Move file/folder here:")
        move_to_path = self.show_input_dialog(widget, 'Move To', 'Where do you want to move \'' + self.full_path + '\'?')
        if move_to_path:
            self.make_parent_path(move_to_path)
            os.rename(self.full_path, move_to_path)
            self.fill_store()
            print(move_to_path)
        else:
            print("Canceled")

    def copy_to(self, widget):
        print("Copy file/folder here:")
        copy_to_path = self.show_input_dialog(widget, 'Copy To', 'Where do you want to copy \'' + self.full_path + '\'?')
        if copy_to_path: 
            if(os.path.isfile(self.full_path)):
            	shutil.copy(self.full_path,copy_to_path)
            elif(os.path.isdir(self.full_path)):
                if os.path.exists(copy_to_path): # Remove if existing
                    shutil.rmtree(copy_to_path)
                shutil.copytree(self.full_path,copy_to_path)
            self.fill_store()
            print(copy_to_path)
        else:
            print("Canceled")

    def make_parent_path(self, path):
        parent_path = os.path.dirname(path)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

    def open_in_terminal(self, widget):
        print("Open terminal here:")
        print(self.current_directory)
        subprocess.Popen("lxterminal --working-directory='" + self.current_directory + "'", shell=True)

    def toggle_hidden(self, widget):
        self.show_hidden = not self.show_hidden
        self.fill_store()

    def on_up_clicked(self, widget):
        self.current_directory = os.path.dirname(self.current_directory)
        self.full_path = self.current_directory
        self.fill_store()
        sensitive = True
        if self.current_directory == "/": sensitive = False
        self.upButton.set_sensitive(sensitive)
        self.set_window_title()
        self.set_path()

    def on_key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_n:
                subprocess.Popen(["/usr/bin/files.py"], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
                return True
            if event.keyval == Gdk.KEY_Up:
                self.on_up_clicked(widget)
                return True
            if event.keyval == Gdk.KEY_h:
                self.toggle_hidden(widget)
                return True
            if event.keyval == Gdk.KEY_r:
                self.fill_store()
                return True
            if event.keyval == Gdk.KEY_d:
                print(self.show_input_dialog(widget, 'Move File', 'Where do you ant to move your file?'))
                return True
        return False
        print(event.keyval)

    # show a dialog for different file events
    def show_input_dialog(self, widget, title, message):
            
        dialogWindow = Gtk.MessageDialog(parent=self.window,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL
            )

        dialogWindow.set_title(title)
        dialogWindow.set_markup(message)

        dialogBox = dialogWindow.get_content_area()
        userEntry = Gtk.Entry()
        userEntry.set_text(self.full_path)
        userEntry.set_visibility(True)
        userEntry.set_size_request(250,0)
        dialogBox.pack_end(userEntry, False, False, 0)

        dialogWindow.show_all()
        response = dialogWindow.run()
        text = userEntry.get_text() 
        dialogWindow.destroy()
        if (response == Gtk.ResponseType.OK) and (text != ''):
            return text
        else:
            return None

    # show a dialog for delete events
    def show_question_dialog(self, widget, title, message):
            
        dialogWindow = Gtk.MessageDialog(parent=self.window,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO
            )

        dialogWindow.set_title(title)
        dialogWindow.set_markup(message)

        dialogWindow.show_all()
        response = dialogWindow.run()
        dialogWindow.destroy()
        if (response == Gtk.ResponseType.YES):
            return self.full_path
        else:
            return None

    def main(self):
        Gtk.main()

if __name__ == "__main__":
    files = Files()
    files.main()
