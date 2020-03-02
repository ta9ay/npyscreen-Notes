#NOTE: not handling duplicate note names. Probem? possibly. Will cause the lookup_dictionary to not work. How to fix?
#NOTE: after editing once, cant select the same note again. have to select another to do it. fix?
#NOTE: 


import npyscreen
import curses
from pathlib import Path
import os
import time
from datetime import datetime
import json
import sys 

NOTE_DATABASE = "database/"

# Initialize lookup table
def update_lookup(k,v):
    path = Path('data') / 'lookup.txt'
    with open(path,"r") as json_file:
        LOOKUP_TABLE = json.load(json_file)
    
    k=k.replace("\t","*").replace(" ","*")
    LOOKUP_TABLE[k] = v
    with open(path,"w") as json_file:
        json.dump(LOOKUP_TABLE,json_file)

def update_todo(todos):
    path = Path('data') / 'todos.txt'
    existing_todos = []
    with open(path,"r+") as fp:
        for line in fp:
            existing_todos.append(line)
        s = set(existing_todos)
        for todo in todos:
            if todo + "\n" not in s:
                fp.write(todo + "\n")

def remove_from_lookup(k):
    path = Path('data') / 'lookup.txt'
    with open(path,"r") as json_file:
        LOOKUP_TABLE = json.load(json_file)
    k=k.replace("\t","*").replace(" ","*")
    del LOOKUP_TABLE[k]
    with open(path,"w") as json_file:
        json.dump(LOOKUP_TABLE,json_file)

# Function to generate display names of notes
def generate_name(fp):
        for line in fp:
            if "Title: " in line:
                name = line.strip().replace("Title: ","")
            if "Date: " in line:
                date = line.strip().replace("Date: ","")
        return date + "\t" + "\t" + name



# Main setup
class MyNotesApp(npyscreen.StandardApp):
    def onStart(self):
        self.note_path="" # Used to pass path between both forms. Find better Alternative?
        self.edit_details= {}
        self.edit_details['edit'] = False

        self.addForm("MAIN", Navigation, name="Notes!")
        self.addForm("NotesTemplate", NotesTemplate, name='New Note')

class Notebooks(npyscreen.BoxTitle):
    
    def when_value_edited(self):
        if self.value is not None:
            # Function to manage view of notes.
            notebook_name = str(self.values[self.value])
            self.parent.populateNotes([notebook_name]) #passing notebook_name as list so it can display more than one notebook with the same function

class Notes(npyscreen.BoxTitle):
    def when_value_edited(self):
        if self.value is not None:
            note_name = str(self.values[self.value]).replace("\t","*").replace(" ","*")
            # self.parent.editNote(note_name)
            self.parent.editNote(note_name)

class Todos(npyscreen.BoxTitle):
    def when_value_edited(self):
        if self.value is not None:    
            todo_selected =  self.values[self.value]
            self.parent.deleteTodo(todo_selected)

class Console(npyscreen.BoxTitle):
    _contained_widget=npyscreen.MultiLineEdit


class DeleteButton(npyscreen.ButtonPress):
    def whenPressed(self):
        self.parent.deletePopup()


# Navigation Screen
class Navigation(npyscreen.FormBaseNew): #do i really need both cancel and ok? 
    # self.notebookname
    # self.notebook_list
    # self.notes_list
    # self.console
    # self.current_notebook_path
    def create(self):

        y, x = self.useable_space()
        new_handlers = { 
            # This is where I should add keyboard shortcuts. 
            # curses.ascii.alt(curses.ascii.NL): self.inputbox_clear
            "^Q" : self.cancel_input,
            curses.ascii.alt(curses.KEY_ENTER): self.run_commands,
            "^S" : self.run_commands ##FIGURE OUT A WAY TO USE ENTER KEY !
        }
        self.add_handlers(new_handlers)

        # NOTEBOOKS
        self.notebook_list = self.add(Notebooks,scroll_exit=True,name="Notebooks",max_width=x//5, max_height=y*3//5, relx=1,rely=1)
        # Fetch and populate notebooks
        self.populateNotebooks()



        # To_do
        self.todo = self.add(Todos,scroll_exit=True, name = "To-Do",max_width=x//5, relx=1)
        #populate todos
        self.populateTodo()

        # NOTES
        # self.notes_list = self.add(npyscreen.BoxTitle,scroll_exit=True, name = "Notes",max_height=y*4//5,relx=(x//5)+1,rely=1)
        self.notes_list = self.add(Notes,scroll_exit=True, name = "Notes",max_height=y*4//5,relx=(x//5)+1,rely=1)
        #populate notes
        # self.notes_list.values=["Notes here", "Another one"]
        self.populateNotes()
        
        
        # Console
        self.console = self.add(Console,scroll_exit=True, name = "Console. Use Ctrl+S to run commands",relx=(x//5)+1)

    def populateNotebooks(self):
        notebook_folder = Path(NOTE_DATABASE)
        notebooks = [ f.name for f in os.scandir(notebook_folder) if f.is_dir() ]
        self.notebook_list.values=notebooks

    def populateNotes(self,notebook="nil"):
        self.notebook_name=notebook
        notes_display_name=[]
        if self.notebook_name=="nil":
            self.notes_list.values=["Select a Notebook"]
        else:
            for notebook_name in self.notebook_name:
            # self.notes_list.values=[notebook_name]
                self.current_notebook_path = Path(NOTE_DATABASE) / str(notebook_name)
                # notes_name = [ f.name for f in os.scandir(self.current_notebook_path) if f.is_file() ]
                for f in os.scandir(self.current_notebook_path):
                    if f.is_file():
                        fp = open(f,'r')
                        name = generate_name(fp)

                        notes_display_name.append(name)
                        # name = str(fp.read(40)).split("\n")[0].replace("Title: ","")
                        # notes_display_name.append(name)
            self.notes_list.values = notes_display_name
        self.notes_list.display()


    def populateTodo(self):
        todo_folder = Path('data') / 'todos.txt'
        with open(todo_folder,"r") as fp:
            todos = [line.replace("\n","") for line in fp]
        self.todo.values=todos
        self.todo.value = None
        self.todo.display()
    
    def cancel_input(self, _input):
        # Use tab to select options
        exit(0)

    # Running console commands here
    def run_commands(self,_input): 
        command=self.console.value
        
        if self.editw==3:
            command = command.strip().lower().split(" ")
            if command[0]=="help":                                      #NOTE:add popup window
                self.console.value=""
                self.console.display() 
                self.spawn_notify_popup()
                # self.edit_popup()
            elif command[0]=="new" and len(command)>1:
                if command[1]=="notebook":
                    if len(command)==3:
                        # create notebook
                        self.flash_message("Creating new notebook '" + str(command[2]) +"'",1)
                        path = Path(NOTE_DATABASE) / str(command[2])
                        if path.exists():
                            self.flash_message("Notebook already exists!",1)
                        else:
                            path.mkdir()
                            self.flash_message("Notebook created",1)
                            # Update Notebook list
                            self.populateNotebooks()
                            self.notebook_list.display()

                        
                    else:
                        self.flash_message("Unrecognized command. Use command 'new notebook <notebook name>'",2)
                elif command[1]=="note":
                    if len(command)==2: # use current active notebook
                        if self.notebook_name=="nil" or len(self.notebook_name)>1: #second condition to handle the problems with creating note after "view all" 
                            self.flash_message("You need to select a notebook or specifiy the name of the notebook with command 'new note <notebook name>",3)
                        else:
                            self.flash_message("Creating note in " + "".join(self.notebook_name),1)
                            #use self.current_notebook_path here
                            self.parentApp.note_path=self.current_notebook_path
                            self.parentApp.switchForm("NotesTemplate")

                    elif len(command)==3: # use a different notebook with name specified
                        path = Path(NOTE_DATABASE) / str(command[2])
                        if path.exists():
                            self.flash_message("Creating note in " + str(command[2]),1)
                            self.parentApp.note_path = Path(NOTE_DATABASE) / str(command[2])
                            self.parentApp.switchForm("NotesTemplate")
                        else:
                            self.flash_message("Notebook doesn't exist!",1)
                    else:
                        self.flash_message("Unrecognized command. Use command 'new note' OR new note <notebook name>'",3)

                else:
                    self.flash_message("Unrecognized command. Use 'help' to see list of available commands",3)
            elif command[0] == "view":
                if len(command) == 2 and command[1]=="all":
                    #view all notes from all notebooks
                    # path = Path(NOTE_DATABASE)
                    all_notebooks = []
                    for f in os.scandir(NOTE_DATABASE):
                        if f.is_dir():
                            all_notebooks.append(f.name)
                    self.populateNotes(all_notebooks)
                    self.notebook_list.display()
                    self.notebook_list.value=None
                    self.console.value = ""
                    self.console.display()
                
                # NOTE: Include tag search. 
                else:
                    self.flash_message("Unrecognized command. Use 'view all' to view all notes",3)
            
            
            else:
                self.flash_message("Unrecognized command. Use 'help' to see list of available commands",3)
        
    def editNote(self,note):
        p = Path('data') / 'lookup.txt'
        with open(p,"r") as json_file:
            LOOKUP_TABLE = json.load(json_file)
        lookup_list = [x for x in LOOKUP_TABLE.keys()]

        if note in lookup_list:
            note_path = LOOKUP_TABLE[note][1] + ".txt"
            found_body = False
            body_text = ""
            fp = open(note_path,"r")
            for line in fp:
                if "Title: " in line:
                    title = line.strip().replace("Title: ","")
                if "Date: " in line:
                    date = line.strip().replace("Date: ","")
                if "Tags: " in line:
                    tags = line.strip().replace("Tags: ","")
                if "Body: " in line:
                    found_body = True
                if found_body == True:
                    body_text+=line

            self.parentApp.edit_details['title'] = title
            self.parentApp.edit_details['date'] = date
            self.parentApp.edit_details['body'] = body_text.replace("Body: ","")
            self.parentApp.edit_details['tags'] = tags.strip().replace("Tags: ","").replace("[","").replace("]","").replace("'","")
            self.parentApp.edit_details['edit'] = True
            self.parentApp.edit_details['file_name'] = note
            self.parentApp.edit_details['file_path'] = note_path
            # self.notes_list.value=None
            self.flash_message("Editing..",1)
            self.parentApp.switchForm('NotesTemplate')
            
        elif note=="Select*a*Notebook":
            pass
        else:
            self.flash_message("Something went wrong",2)
        

    def flash_message(self,message,sec):
        self.console.value = message
        self.console.display()
        time.sleep(sec)
        self.console.value=""
        self.console.display()       

    def deleteTodo(self, todo):
        
        confirm = npyscreen.notify_ok_cancel("Are you sure you want to delete this To-Do?", title = "Delete To-Do")
        if confirm:
            path = Path('data') / 'todos.txt'
            todos = []
            todo = todo +"\n"
            with open(path,"r") as fp:
                for line in fp:
                    todos.append(line)
            if todo in todos:
                todos.remove(todo)
            with open(path,"w") as fp:
                for todo in todos:
                    fp.write(todo)
        # self.todo.value = ""
        self.populateTodo()




    def spawn_notify_popup(self):
        npyscreen.notify_confirm(
'''Use Ctrl+S to run commands.\n
Use 'Tab' to navigate between windows and buttons.\n
Use Ctrl+Q to exit.\n
Use "L" on a list to search results.\n
Select a To-Do to delete it.\n
\t\t------\t------
\t\t------\t------
List of available commands:\n
\tnew\n 
\t\tnote: Creates new note in selected notebook\n
\t\t----
\t\tnote <notebook-name>: Creates new note in specified notebook\n
\t\t----
\t\tnotebook <name>: Creates new notebook using specified name\n
\t------\n
\tview\n
\t\tall: List all notes from all notebooks

'''
            , title= 'Help',wide=True)

    def afterEditing(self):
        self.parentApp.setNextForm("NotesTemplate")

    def beforeEditing(self):
        self.notes_list.value=None
        self.populateNotes(self.notebook_name)
        self.populateTodo()
        




# Notes Template
class NotesTemplate(npyscreen.Form):
    def create(self):
        self.title  = self.add(npyscreen.TitleText, name='Title')
        self.date = self.add(npyscreen.TitleFixedText,name="Date")
        self.body   = self.add(npyscreen.MultiLineEdit, max_height=25, rely=9)
        self.tags  = self.add(npyscreen.TitleText, name='Tags')
        new_handlers = { 
            # This is where I should add keyboard shortcuts. 
            # curses.ascii.alt(curses.ascii.NL): self.inputbox_clear
            "^D" : self.inputbox_clear,
            "^Q" : self.cancel_input
        }
        self.add_handlers(new_handlers)
        self.exitButton = self.add(DeleteButton, name="Delete", relx=2, rely=-3)
        
        self.savenoteflag = True

    def set_values(self):
        if self.parentApp.edit_details['edit'] == True: # Check if note is new or being edited. If old, keep everything same from old note.
            self.title.value = self.parentApp.edit_details['title']
            self.body.value = self.parentApp.edit_details['body']
            self.date.value = self.parentApp.edit_details['date']
            self.tags.value = self.parentApp.edit_details['tags']
            self.title.display()
            self.body.display()
            self.date.display()
            self.tags.display()

        else:
            self.date.value = value=datetime.today().strftime('%d-%m-%Y')
            self.body.value = """Add text here.\n^D to clear textbox.\n^Q to cancel.\nTags are optional and should be comma seperated values."""
            self.date.display()
            self.body.display()
            self.parentApp.edit_details['title'] = ""
            self.parentApp.edit_details['date'] = ""
            self.parentApp.edit_details['body'] = ""
            self.parentApp.edit_details['tags'] = ""
            
            self.parentApp.edit_details['file_name'] = ""
            self.parentApp.edit_details['file_path'] = ""


    def inputbox_clear(self, _input):
        self.body.value=""
        self.body.display()

    

    def savenote(self): # NOTE: Need to catch errors here. Currently file saves even if there are errors in the text.
        tags = [tag.strip().lower() for tag in str(self.tags.value).split(",")]
        # Writing to file.
        if self.parentApp.edit_details['edit'] == True:
            file_name = self.parentApp.edit_details['file_name']
            path = self.parentApp.edit_details['file_path'].replace(".txt","")
            file_new = open(str(path)+".txt", "r")
            key = generate_name(file_new)
            remove_from_lookup(key)
        else:
            file_name = datetime.today().strftime('%Y-%m-%d-%H:%M:%S').replace(":","")
            path = Path(self.parentApp.note_path) / file_name
        # Check for todos
        todos = []
        text = str(self.body.value).split("\n")
        for line in text:
            if line.startswith(">>"):
                todos.append(line)

        update_todo(todos)


        # Write to file
        file_new = open(str(path)+".txt", "w") 
        data = ["Title: "+ self.title.value + "\n",
            "Tags: " + str(tags) + "\n",
            "Date: " + self.date.value + "\n",
            "Body: " + self.body.value + "\n"
            ]
        file_new.writelines(data)
        file_new.close()
        

        # Updating the lookup_table
        '''
        Using a lookup table to keep track of all notes and their respective attributes to make searching/editing easier.
        Format: {
                    display_name:[
                        name_of_file, 
                        path, 
                        [tags] 
                        ]
                } 
        '''
        file_new = open(str(path)+".txt", "r")
        key = generate_name(file_new)
        value = [file_name,str(path),tags]
        file_new.close()

        update_lookup(key,value)
        

        # Clearing variables
        self.title.value = ""
        self.tags.value = ""
        self.date.value = datetime.today().strftime('%d-%m-%Y')
        self.body.value = """Add text here.\n^D to clear textbox.\n^Q to cancel.\nTags are optional and should be comma seperated values."""
        self.parentApp.edit_details['edit'] = False


    def cancel_input(self, _input="nil"):
        # self.body.value=""        # Probably don't have to do all this. Just not write any values. 
        # self.tags.get_selected_objects=[] # However, exit returns to terminal. need to go back to previous form.
        # self.title.value=""
        # self.myDate.value=""
        if _input=="nil":
            notify_result = npyscreen.notify_ok_cancel("Delete Note? Use tab to select options", title= 'DELETE')
            if notify_result:
                self.parentApp.switchForm("MAIN")
                self.savenoteflag = False
                self.parentApp.edit_details['edit'] = False
            else:
                self.savenoteflag = True
        else:
            notify_result = npyscreen.notify_ok_cancel("Discard note? Use tab to select options", title= 'EXIT')
            if notify_result:
                self.parentApp.switchForm("MAIN")
                self.savenoteflag = False
                self.parentApp.edit_details['edit'] = False
            else:
                self.savenoteflag = True    

    
    
    def deletePopup(self):
        if self.parentApp.edit_details['edit'] == False: # This is true for new notes that haven't been saved yet.
            self.cancel_input()
        else: # This for existing notes
            notify_result = npyscreen.notify_ok_cancel("Delete Note? This action cannot be un-done", title= 'DELETE')
            if notify_result:
                
                path = self.parentApp.edit_details['file_path']
                if os.path.exists(path):
                    try:
                        file_new = open(str(path), "r")
                        key = generate_name(file_new)
                        file_new.close()
                        os.remove(path) # NOTE: Throwing error. File already being used.
                        self.savenoteflag = False
                        self.parentApp.switchForm("MAIN")
                        

                    except:
                        npyscreen.notify_confirm("Something went wrong", title="Error", wrap=True, wide=False, editw=0)
                        
                    else:
                        remove_from_lookup(key)
                    
                # else:
                    # pass


            else:
                pass 
            
            
                




    def afterEditing(self):
        if self.savenoteflag:
            self.savenote()
        self.parentApp.setNextForm("MAIN")

    def beforeEditing(self):
        
        self.set_values()


App = MyNotesApp()
App.run()
