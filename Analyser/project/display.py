#!/usr/bin/python3
# -*- coding: utf-8 -*-


import extractor
import functools
import math
import os
import pathlib
import re
import shutil
import time
import platform

from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter.messagebox import askokcancel, showerror, showinfo, showwarning
from tkinter.scrolledtext import ScrolledText

# macOS only:
#   from Foundation import NSBundle

# Platform specific settings
macOS = (platform.system() == 'Darwin')
cmdkw = 'Command' if macOS else 'Ctrl'
delkw = 'Delete'
optkw = 'Opt' if macOS else 'Alt'
sftkw = 'Shift'
upakw = '↑'
dwnkw = '↓'
brlkw = '['
brrkw = ']'

# Keyboard event bindings
cmdbd = 'Command' if macOS else 'Control'
cmabd = 'comma'
delbd = 'Delete'
optbd = 'Alt'
sftbd = 'Shift'
upabd = 'uparrow'
dwnbd = 'downarrow'
brlbd = 'bracketleft'
brrbd = 'bracketright'

# accelerator & event
short = lambda *args: '-'.join(args) if macOS else '+'.join(args)
event = lambda *args: '<' + '-'.join(args) + '>'

# File name regex
FILE = re.compile(r'''
    \A(?P<name>.*?)(?P<copy>\ copy)?(?P<fctr>\ [0-9]+)?[.](?P<exts>.*)\Z
''', re.VERBOSE)

# Extracting Label
NUMB = lambda number: '''

       Extracting... Frame {:>2d}

'''.format(number)

# Loading Label
TEXT = lambda percent: '''

          Loading... {:>2.2f}%

   +------------------------------+
   |{sharp}{space}|
   +------------------------------+

'''.format(percent,
    sharp = '#' * math.ceil(30 * percent / 100),
    space = ' ' * (30 - math.ceil(30 * percent / 100))
)

# Exporting Label
EXPT = lambda percent: '''

         Exporting... {:>2.2f}%

   +------------------------------+
   |{sharp}{space}|
   +------------------------------+

'''.format(percent,
    sharp = '#' * math.ceil(30 * percent / 100),
    space = ' ' * (30 - math.ceil(30 * percent / 100))
)


class Display(extractor.Extractor):

    _cpflg = False
    _cpstr = 1

    ##########################################################################
    # Data modules.
    ##########################################################################

    def __init__(self):
        # root window setup
        self.master = Tk()
        self.master.title('PCAP Tree Viewer')
        self.master.geometry('674x476')
        self.master.resizable(height=False)

        # frame setup
        self.frame = Frame(bd=8)
        self.frame.pack()

        # menu setup
        self.menu = Menu(self.master)
        self.master.config(menu=self.menu)
        self.menu_setup()

        self.init_display()
        self.master.mainloop()

    ##########################################################################
    # Methods.
    ##########################################################################

    def menu_setup(self):
        """Menu Strcuture:

        PCAP Tree Viewer | Home (macOS)
            * About PCAP Tree Viewer
            * Preferences...                          ⌘,
            * Service
                - No Services Apply (disabled)
                - System Preferences...
            -----------------------------------------------
            * Hide PCAP Tree Viewer                   ⌘H
            * Hide Others                            ⌥⌘H
            * Show All
            -----------------------------------------------
            * Quit PCAP Tree Viewer                   ⌘Q

        File
            * Open...                                 ⌘O
            * Open Recent
                * Recent File 0
                * Recent File 1
                * ......
                -------------------------------------------
                * Clear Menu
            * Close Window                            ⌘W
            * Save                                    ⌘S
            * Duplicate                              ⇧⌘S
            * Rename...
            * Move To...
            * Export...
            * Export as PDF...
            -----------------------------------------------
            * Print                                   ⌘P

        Edit
            * Copy                                    ⌘C
            * Select All                              ⌘A
            * Invert Selection                       ⇧⌘I
            -----------------------------------------------
            * Move to Trash                           ⌘⌫
            -----------------------------------------------
            * Find
                * Find...                             ⌘F
                * Find Next                           ⌘G
                * Find Previous                      ⇧⌘G
                * Use Selection for Find              ⌘E
                * Jump to Selection                   ⌘J

        Go
            * Up                                       ↑
            * Down                                     ↓
            * Previous Frame                          ⌥↑
            * Next Frame                              ⌥↓
            * Go to Frame...                         ⌥⌘G
            -----------------------------------------------
            * Back                                    ⌘[
            * Forward                                 ⌘]

        Window
            * Minimize                                ⌘M
            * Zoom

        Help
            * Search
            -----------------------------------------------
            * PCAP Tree Viewer Help

        """
        if macOS:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info and info['CFBundleName'] == 'Python':
                    info['CFBundleName'] = 'PCAP Tree Viewer'

        # home menu
        home_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Home', menu=home_menu)
        home_menu.add_cascade(label='About PCAP Tree Viewer', command=self.intr_cmd)
        home_menu.add_separator()
        home_menu.add_command(label='Preferences...', command=self.pref_cmd, accelerator=short(cmdkw, '，'))
        self.master.bind(event(cmdbd, cmabd), self.pref_cmd)
        home_menu.add_separator()
        serv_menu = Menu(home_menu, tearoff=0)
        home_menu.add_cascade(label='Service', menu=serv_menu)
        serv_menu.add_command(label='No Services Apply', state='disabled')
        serv_menu.add_command(label='System Preferences...', command=self.sysp_cmd)
        home_menu.add_separator()
        home_menu.add_command(label='Hide PCAP Tree Viewer', command=self.hide_cmd, accelerator=short(cmdkw, 'Ｈ'))
        self.master.bind(event(cmdbd, 'H'), self.hide_cmd)
        home_menu.add_command(label='Hide Others', command=self.wipe_cmd, accelerator=short(optkw, cmdkw, 'Ｈ'))
        self.master.bind(event(optbd, cmdbd, 'H'), self.wipe_cmd)
        home_menu.add_command(label='Show All', command=self.show_cmd)
        home_menu.add_separator()
        home_menu.add_command(label='Quit PCAP Tree Viewer', command=self.quit_cmd, accelerator=short(cmdkw, 'Ｑ'))
        self.master.bind(event(cmdbd, 'Q'), self.quit_cmd)

        # file menu
        file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open...', command=self.open_cmd, accelerator=short(cmdkw, 'Ｏ'))
        self.master.bind(event(cmdbd, 'O'), self.open_cmd)
        frct_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label='Open Recent', menu=frct_menu)
        try:
            with open('recent', 'r') as file_:
                file_real = False
                for (fctr, file_name) in enumerate(file_):
                    file_real = True if file_name else False
                    frct_menu.add_command(label=file_name, command=functools.partial(self.open_cmd, file_name))
        except Exception:
            file_real = False
        if file_real:
            frct_menu.add_separator()
            frct_menu.add_command(label='Clear Menu', command=functools.partial(self.rmrf_cmd, menu=frct_menu, fctr=fctr))
        else:
            frct_menu.add_command(label='Clear Menu', state='disabled')
        file_menu.add_separator()
        file_menu.add_command(label='Close Window', command=self.shut_cmd, accelerator=short(cmdkw, 'Ｗ'))
        self.master.bind(event(cmdbd, 'W'), self.shut_cmd)
        file_menu.add_command(label='Save', command=self.save_cmd, accelerator=short(cmdkw, 'Ｓ'))
        self.master.bind(event(cmdbd, 'S'), self.save_cmd)
        file_menu.add_command(label='Duplicate', command=self.copy_cmd, accelerator=short(sftkw, cmdkw, 'Ｓ'))
        self.master.bind(event(sftbd, cmdbd, 'S'), self.copy_cmd)
        file_menu.add_command(label='Rename...', command=self.mvrn_cmd)
        file_menu.add_command(label='Move To...', command=self.move_cmd)
        file_menu.add_command(label='Export...', command=self.expt_cmd)
        file_menu.add_command(label='Export as PDF...', command=functools.partial(self.expt_cmd, 'pdf'))
        file_menu.add_separator()
        file_menu.add_command(label='Print', command=self.expt_cmd, accelerator=short(cmdkw, 'Ｐ'))
        self.master.bind(event(cmdbd, 'P'), self.expt_cmd)

        # edit menu
        edit_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Copy', command=self.cmdc_cmd, accelerator=short(cmdkw, 'Ｃ'))
        self.master.bind(event(cmdbd, 'C'), self.cmdc_cmd)
        edit_menu.add_command(label='Select All', command=self.cmda_cmd, accelerator=short(cmdkw, 'Ａ'))
        self.master.bind(event(cmdbd, 'A'), self.cmda_cmd)
        edit_menu.add_command(label='Invert Selection', command=self.invt_cmd, accelerator=short(sftkw, cmdkw, 'Ｉ'))
        self.master.bind(event(sftbd, cmdbd, 'I'), self.invt_cmd)
        edit_menu.add_separator()
        edit_menu.add_command(label='Move to Trash', command=self.mvsh_cmd, accelerator=short(cmdkw, delkw))
        self.master.bind(event(cmdbd, delbd), self.mvsh_cmd)
        edit_menu.add_separator()
        find_menu = Menu(edit_menu, tearoff=0)
        edit_menu.add_cascade(label='Find', menu=find_menu)
        find_menu.add_command(label='Find...', command=self.find_cmd, accelerator=short(cmdkw, 'Ｆ'))
        self.master.bind(event(cmdbd, 'F'), self.find_cmd)
        find_menu.add_command(label='Find Next', command=functools.partial(self.find_cmd, 'next'), accelerator=short(cmdkw, 'Ｇ'))
        self.master.bind(event(cmdbd, 'G'), functools.partial(self.find_cmd, 'next'))
        find_menu.add_command(label='Find Previous', command=functools.partial(self.find_cmd, 'prev'), accelerator=short(sftkw, cmdkw, 'Ｇ'))
        self.master.bind(event(sftbd, cmdbd, 'G'), functools.partial(self.find_cmd, 'prev'))
        find_menu.add_command(label='Use Selection for Find', command=functools.partial(self.find_cmd, 'self'), accelerator=short(cmdkw, 'Ｅ'))
        self.master.bind(event(cmdbd, 'E'), functools.partial(self.find_cmd, 'self'))
        find_menu.add_command(label='Jump to Selection', command=functools.partial(self.find_cmd, 'jump'), accelerator=short(cmdkw, 'Ｊ'))
        self.master.bind(event(cmdbd, 'J'), functools.partial(self.find_cmd, 'jump'))

        # go menu
        goto_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Go', menu=goto_menu)
        goto_menu.add_command(label='Up', command=functools.partial(self.goto_cmd, 'up'), accelerator=short(upakw))
        self.master.bind(event(upabd), functools.partial(self.goto_cmd, 'up'))
        goto_menu.add_command(label='Down', command=functools.partial(self.goto_cmd, 'down'), accelerator=short(dwnkw))
        self.master.bind(event(dwnbd), functools.partial(self.goto_cmd, 'down'))
        goto_menu.add_command(label='Previous Frame', command=functools.partial(self.goto_cmd, 'prev'), accelerator=short(optkw, upakw))
        self.master.bind(event(optbd, upabd), functools.partial(self.goto_cmd, 'prev'))
        goto_menu.add_command(label='Next Frame', command=functools.partial(self.goto_cmd, 'next'), accelerator=short(optkw, dwnkw))
        self.master.bind(event(optbd, dwnbd), functools.partial(self.goto_cmd, 'next'))
        goto_menu.add_command(label='Go to Frame...', command=functools.partial(self.goto_cmd, 'go'), accelerator=short(optkw, cmdkw, 'Ｇ'))
        self.master.bind(event(optbd, cmdbd, 'G'), functools.partial(self.goto_cmd, 'go'))
        goto_menu.add_separator()
        goto_menu.add_command(label='Back', command=functools.partial(self.goto_cmd, 'back'), accelerator=short(cmdkw, brlkw))
        self.master.bind(event(cmdbd, brlbd), functools.partial(self.goto_cmd, 'back'))
        goto_menu.add_command(label='Forward', command=functools.partial(self.goto_cmd, 'fwd'), accelerator=short(cmdkw, brrkw))
        self.master.bind(event(cmdbd, brrbd), functools.partial(self.goto_cmd, 'fwd'))

        # window menu
        wind_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Window', menu=wind_menu)
        wind_menu.add_command(label='Minimize', command=self.mini_cmd, accelerator=short(cmdkw, 'Ｍ'))
        self.master.bind(event(cmdbd, 'M'), self.mini_cmd)
        wind_menu.add_command(label='Zoom', command=self.zoom_cmd)

        # help menu
        help_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Help', menu=help_menu)
        if not macOS:
            help_menu.add_command(label='Search', command=self.srch_cmd)
            help_menu.add_separator()
        help_menu.add_command(label='PCAP Tree Viewer Help', command=self.help_cmd)

    # About PCAP Tree Viewer
    def intr_cmd(self):
        toplevel = Toplevel(self.master)
        toplevel.title('About PCAP Tree Viewer')
        scrolledtext = ScrolledText(
                toplevel, font=('Courier New', 12),
                width=50, height=20
        )
        scrolledtext.pack()
        with open('about', 'r') as file_:
            for line in file_:
                scrolledtext.insert(END, line)
                scrolledtext.update()
        scrolledtext.config(state=DISABLED)
        toplevel.resizable(width=False, height=False)

    # Preferences
    def pref_cmd(self, *args):
        pass

    # System Preferences...
    def sysp_cmd(self):
        pass

    # Hide PCAP Tree Viewer
    def hide_cmd(self):
        self.master.withdraw()

    # Hide Others
    def wipe_cmd(self):
        pass

    # Show All
    def show_cmd(self):
        self.zoom_cmd()

    # Quit PCAP Tree Viewer
    def quit_cmd(self):
        os.remove('out')
        self.master.destroy()

    # Open...
    def open_cmd(self, name=None):
        self.open_file(name)

    # Clear Menu
    def rmrf_cmd(self, *, menu, fctr):
        open('recent', 'w').close()
        menu.delete(0, fctr+2)
        menu.add_command(label='Clear Menu', state=DISABLED)

    # Close Window
    def shut_cmd(self):
        if askokcancel(
                'Close Window',
                'Do you really want to close?'
            ):
            os.remove('out')
            self.master.destroy()

    # Save
    def save_cmd(self):
        self.save_file()

    # Duplicate
    def copy_cmd(self):
        ifnm = self._ifile.name
        fnmt = FILE.match(ifnm)
        if fnmt is None:
            return

        name = fnmt.group('name') or ''
        copy = fnmt.group('copy') or ''
        fctr = fnmt.group('fctr')
        exts = fnmt.group('exts') or ''

        if fctr:
            self._cpctr = 1 + (self._cpctr if self._cpflg else int(fctr))
            fctr = ' ' + str(self._cpctr)
        else:
            self._cpctr = 2 if copy else self._cpctr
            fctr = (' ' + str(sctr)) if copy else ''
        self._cpflg = True

        cpnm = name + copy + fctr + '.' + exts
        shutil.copyfile(ifnm, cpnm)

    # Rename...
    def mvrn_cmd(self):
        self.move_cmd()

    # Move To...
    def move_cmd(self):
        file_ = asksaveasfile(mode='w', defaultextension=".txt")
        if file_ is None:
            return
        os.rename(self._ifile.name, file_.name)

    # Export...
    def expt_cmd(self, fmt=None):
        pass

    # Copy
    def cmdc_cmd(self):
        data = []
        for index in range(self.listbox.size()):
            if self.listbox.selection_includes(index):
                data.append(self.listbox.get(index))

        data = '\n'.join(data)
        self.master.clipboard_clear()
        self.master.clipboard_append(data)

    # Select All
    def cmda_cmd(self):
        for index in range(self.listbox.size()):
            self.listbox.selection_set(index)
            self.listbox.yview(index)
            self.listbox.update()

    # Invert Selection
    def invt_cmd(self):
        for index in range(self.listbox.size()):
            if self.listbox.selection_includes(index):
                self.listbox.selection_clear(index)
            else:
                self.listbox.selection_set(index)
            self.listbox.yview(index)
            self.listbox.update()

    # Move to Trash
    def mvsh_cmd(self):
        os.remove(self._ifile.name)

    # Find
    def find_cmd(self, cmd=None):
        if cmd == 'next':
            pass
        elif cmd == 'prev':
            pass
        elif cmd == 'self':
            self.find_self()
        elif cmd == 'jump':
            self.find_jump()
        else:
            self._nindex = -1
            self._pindex = self.listbox.size()
            toplevel = Toplevel(self.master)

            frame = Frame(toplevel, bd=4)
            frame.pack()

            entry = Entry(frame, font=('Courier New', 12))
            entry.pack(side=LEFT)

            button_next = Button(frame,
                    text='Next',
                    font=('Courier New', 12),
                    command=functools.partial(self.find_next, entry.get())
            )
            button_next.pack(side=RIGHT)

            button_prev = Button(frame,
                    text='Previous',
                    font=('Courier New', 12),
                    command=functools.partial(self.find_prev, entry.get())
            )
            button_prev.pack(side=RIGHT)

    # Find Next
    def find_next(self, text):
        if self._nindex >= 0:
            self.listbox.selection_clear(self._nindex)
            self.listbox.update()

        if self._nindex >= self.listbox.size():
            self._nindex = -1

        for index in range(self._nindex+1, self.listbox.size()):
            if text in self.listbox.get(index):
                self.listbox.selection_set(index)
                self.listbox.yview(index)
                self.listbox.update()
                self._nindex = index
                break
        else:
            if self._nindex == -1:
                showerror(
                    'Find nothing...',
                    'No result on {text}'.format(text=text)
                )
            else:
                self._nindex = -1
                self.find_next(text)

    # Find Previous
    def find_prev(self, text):
        if self._pindex < self.listbox.size():
            self.listbox.selection_clear(self._pindex)
            self.listbox.update()

        if self._pindex <= 0:
            self._pindex = -1

        for index in range(self._pindex-1, -1, -1):
            if text in self.listbox.get(index):
                self.listbox.selection_set(index)
                self.listbox.yview(index)
                self.listbox.update()
                self._index = index
                break
        else:
            if self._pindex == 0:
                showinfo(
                    'Find nothing...',
                    'No result on {text}.'.format(text=text)
                )
            else:
                self._pindex = self.listbox.size()
                self.find_prev(text)

    # Use Selection for Find
    def find_self(self):
        flag = False
        for index in range(self.listbox.size()):
            if self.listbox.selection_includes(index):
                if flag:
                    showerror(
                        'Unsupported Operation',
                        "'Use Selection for Find' must be one line."
                    )
                    return
                text = self.listbox.get(index)
                flag = True

        toplevel = Toplevel(self.master)

        frame = Frame(toplevel, bd=4)
        frame.pack()

        label = Label(frame, text=text, font=('Courier New', 12))
        label.pack(side=LEFT)

        button_next = Button(frame,
                text='Next',
                font=('Courier New', 12),
                command=functools.partial(self.find_next, entry.get())
        )
        button_next.pack(side=RIGHT)

        button_prev = Button(frame,
                text='Previous',
                font=('Courier New', 12),
                command=functools.partial(self.find_prev, entry.get())
        )
        button_prev.pack(side=RIGHT)

    # Jump to Selection
    def find_jump(self):
        for index in range(self.listbox.size()):
            if self.listbox.selection_includes(index):
                break
        self.listbox.yview(index)
        self.listbox.update()

    # Go
    def goto_cmd(self, cmd=None):
        for index in range(self.listbox.size()):
            if self.listbox.selection_includes(index):
                self.listbox.selection_clear(index)
                break
        else:
            index = 0

        if cmd == 'up':
            self.goto_up(index)
        elif cmd == 'down':
            self.goto_down(index)
        elif cmd == 'pre':
            self.goto_prev(index)
        elif cmd == 'next':
            self.goto_next(index)
        elif cmd == 'go':
            self.goto_go()
        elif cmd == 'back':
            self.goto_back(index)
        elif cmd == 'fwd':
            self.goto_fwd(index)
        else:
            pass

    # Up
    def goto_up(self, index):
        if index + 1 >= self.listbox.size():
            index = -1
        self.listbox.selection_set(index + 1)
        self.listbox.yview(index + 1)
        self.listbox.update()

    # Down
    def goto_down(self, index):
        if index <= 0:
            index = self.listbox.size() + 1
        self.listbox.selection_set(index - 1)
        self.listbox.yview(index - 1)
        self.listbox.update()

    # Previous Frame
    def goto_prev(index):
        tmp = self.goto_back(index)
        if tmp is None:
            return

        for tmp in range(tmp+1, self.listbox.size()):
            if 'Frame' not in self.listbox.get(index):
                self.listbox.selection_set(tmp)
                self.listbox.update()
                break

    # Next Frame
    def goto_next(index):
        tmp = self.goto_fwd(index)
        if tmp is None:
            return

        for tmp in range(tmp+1, self.listbox.size()):
            if 'Frame' not in self.listbox.get(index):
                self.listbox.selection_set(tmp)
                self.listbox.update()
                break

    # Go to Frame...
    def goto_go(self):
        toplevel = Toplevel(self.master)

        frame = Frame(toplevel, bd=4)
        frame.pack()

        label = Label(frame, text='Frame ', font=('Courier New', 12))
        label.pack(side=LEFT)

        entry = Entry(frame, font=('Courier New', 12))
        entry.pack(side=LEFT)

        button = Button(frame,
            text='Go',
            font=('Courier New', 12),
            command=functools.partial(self.goto_frame, entry.get(), window=toplevel)
        )
        button.pack(side=RIGHT)

    def goto_frame(self, index, *, window):
        if (not isinstance(index, int)) or index < 1:
            showerror(
                'Unsupported Input',
                'Frame number must be a positive integer.'
            )
            window.destroy()
            self.goto_go()

        frame = 'Frame {index}'.format(index=index)
        for tmp in range(self.listbox.size()):
            if frame in self.listbox.get(tmp):
                self.listbox.yview(tmp)
                self.listbox.update()
                break
        else:
            showerror(
                'Not Found',
                'No frame ranged {index}.'.format(index=index)
            )
        window.destroy()

    # Back
    def goto_back(index):
        if index <= 0:
            index = self.listbox.size() - 1
        for tmp in range(index-1, 0, -1):
            if 'Frame' in self.listbox.get(index) \
                or 'Global Header' in self.listbox.get(index):
                self.listbox.selection_set(tmp)
                self.listbox.yview(tmp)
                self.listbox.update()
                break
        else:
            showwarning(
                'Hit the math.ceil!',
                'No frame in the front.'
            )
            return
        return tmp

    # Forward
    def goto_fwd(index):
        if index >= self.listbox.size() - 1:
            index = -1
        for tmp in range(index+1, self.listbox.size()):
            if 'Frame' in self.listbox.get(index) \
                or 'Global Header' in self.listbox.get(index):
                self.listbox.selection_set(tmp)
                self.listbox.yview(tmp)
                self.listbox.update()
                break
        else:
            showwarning(
                'Hit the floor!',
                'No frame down below.'
            )
            return
        return tmp

    # Minimize
    def mini_cmd(self):
        self.master.iconify()

    # Zoom
    def zoom_cmd(self):
        self.master.update()
        self.master.deiconify()

    # Search
    def srch_cmd(self):
        pass

    # PCAP Tree Viewer Help
    def help_cmd(self):
        pass

    def init_display(self):
        # scrollpad setup
        self.text = Text(
            self.frame, bd=0, font=('Courier New', 13),
            width=500, height=500
        )
        self.text.pack(side=LEFT, fill=BOTH)

        # start button setup
        self.button = Button(
            self.frame, text='Open ...',
            command=self.open_file, font=('Courier New', 13)
        )
        self.button.place(relx=0.5, rely=0.93, anchor=CENTER)

        with open('init', 'r') as file_:
            for line in file_:
                self.text.insert(END, line)
                self.text.update()
        self.text.config(state=DISABLED)

    def open_file(self, name=None):
        ifnm = name.strip() or askopenfilename(
            parent=self.master, title='Please select a file ...',
            filetypes=[('PCAP Files', '*.pcap'), ('All Files', '*.*')],
            initialdir='./', initialfile='in.pcap'
        )

        if pathlib.Path(ifnm).is_file():
            self._ifile = open(ifnm, 'rb')
            self.record_header(self._ifile)      # read PCAP global header

            self.button.place_forget()
            self.text.pack_forget()

            try:
                self.listbox.pack_forget()
                self.scrollbar.pack_forget()
            except:
                pass
            self._frnum = 1

            self.keep_file(ifnm)
            self.load_file()
        else:
            if askokcancel('Unsupported file!', 'Please retry.'):
                self.open_file()
            else:
                self.button.place()
                self.text.pack()

    def save_file(self, fmt=None):
        if fmt == 'None':
            file_ = asksaveasfile(mode='w', defaultextension=".txt")
            if file_ is None:
                return
            shutil.copyfile('out', file_.name)
        elif fmt == 'json':
            pass
        else:
            pass

    def load_file(self):
        # scrollpad setup
        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox = Listbox(self.frame, bd=0, font=('Courier New', 12),
                        width=500, height=500, yscrollcommand=self.scrollbar.set,
                        selectmode=EXTENDED, activestyle='none', takefocus=0
                    )
        self.listbox.pack(side=LEFT, fill=BOTH)
        self.scrollbar.config(command=self.listbox.yview)

        # loading label setup
        self.label = Label(self.frame, width=40, height=10, bd=4, anchor='w',
                        justify=LEFT, bg='green', font=('Courier New', 22)
                    )
        self.label.place(relx=0.5, rely=0.5, anchor=CENTER)

        # extracting pcap file
        while True:
            try:
                self.record_frames(self._ifile)      # read frames
                content = NUMB(self.length - 1)
                self.label.config(text=content)
                self.label.update()
            except EOFError:
                break

        time.sleep(1)

        # loading treeview
        percent = 0
        content = TEXT(percent)
        self.label.config(text=content)

        with open('out', 'r') as fout:
            _ctr = 0
            for (_lctr, line) in enumerate(fout):
                self.listbox.insert(END, line)
                self.listbox.update()
                self.listbox.yview(END)
                self.listbox.selection_clear(0, _lctr)
                if 'Frame' in line:
                    _ctr += 1
                    percent = 100.0 * _ctr / self.length
                    content = TEXT(percent)
                    self.label.config(text=content)
                    self.label.update()

        content = TEXT(100)
        self.label.config(text=content)
        self.label.update()

        # loading over
        time.sleep(2)
        self.listbox.yview(0)
        self.label.place_forget()

    def keep_file(self, name):
        records = []
        with open('recent', 'r') as file_:
            for line in file_:
                records.append(line.strip())

        try:
            index = records.index(name)
        except ValueError:
            index = 0
            if len(records) >= 10:
                records.pop()
        else:
            records.pop(index)
        finally:
            records.insert(0, name)

        with open('recent', 'w') as file_:
            record = '\n'.join(records)
            file_.write(record)


if __name__ == '__main__':
    Display()
