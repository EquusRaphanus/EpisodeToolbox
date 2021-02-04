#!/usr/bin/env python
import os
import sys
import subprocess
import re
import datetime
import Tkinter as tk


def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return "break"


# Subclass tk.Tk to create base window with our custom settings.
class Window(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Set minimum window size
        self.minsize(height=565, width=850)

        # Raise window when opened
        self.lift()

        # Set the icon image for this app
        # self.iconphoto(self, tk.PhotoImage(file='resources/EpisodeGif.gif'))

        # Set the "app_name," so AppleScript can raise the window
        self.app_name = "EpisodeTools"

        # Function to run OS specific code to bind "Select All" and ensure the window
        # is raised.
        self.os_detect()

    # Some Mac specific stuff and binding "Select All"
    # I develop this on Mac and Linux but use this exclusively on Mac so I figured it was
    # best to move this multi-line if statement into a method
    def os_detect(self):
        if sys.platform == "darwin":

            # Making sure window is raised
            osa_script = '''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "{}" to true' '''.\
                format(self.app_name)

            # Uncomment the next line for Py2App Building
            os.system(osa_script)

            # Binding "Select All" to cmd + A
            self.bind('<Command-a>', Window.select_all)
            self.bind('<Command-A>', Window.select_all)
        else:
            # Binding "Select All" to ctrl + A
            self.bind('<Control-a>', Window.select_all)
            self.bind('<Control-A>', Window.select_all)

    # Actually defining what "Select All" means, because apparently
    # this needed to be defined.
    def select_all(self):
        try:
            self.widget.select_range(0, 'end')
            self.widget.icursor('end')
            return 'break'
        except AttributeError:
            self.widget.tag_add(tk.SEL, "1.0", tk.END)
            self.widget.mark_set(tk.INSERT, "1.0")
            self.widget.see(tk.INSERT)
            return 'break'


# Subclassing tk.Frame because I got tired of typing "self.pack" so many
# times and having to keep track of which way I wanted it to pack, so I
# subclassed the different pack options into differently named widgets.

# Subclassing base tk.Frame for settings I want on *all* frames.
class BaseFrame(tk.Frame):
    def __init__(self, window, *args, **kwargs):
        tk.Frame.__init__(self, window, *args, **kwargs)

        # Allowing focus to move from entry box when I click on BG
        # so output can update
        self.bind("<1>", lambda event: self.focus_set())

        # Pseudo Dark Mode
        # self["bg"] = "#1b1b1b"


# Subclassing BaseFrame for a frame that automatically
# fills available space.
class FullFrame(BaseFrame):
    def __init__(self, window, *args, **kwargs):
        BaseFrame.__init__(self, window, *args, **kwargs)
        self.pack(fill=tk.BOTH, expand=1)


# Subclassing BaseFrame for a frame that automatically expands
# width-wise, or x-oriented.
class WideFrame(BaseFrame):
    def __init__(self, window, *args, **kwargs):
        BaseFrame.__init__(self, window, *args, **kwargs)
        self.pack(fill=tk.X, expand=1)

# Subclassing tk.Entry to include a settable placeholder text.
class EntryCustom(tk.Entry):
    def __init__(self, window, label, **kwargs):
        self.input = tk.StringVar()
        tk.Entry.__init__(self, window, textvariable=self.input, **kwargs)
        # self.config(bg="#1b1b1b", fg="#dedede", disabledbackground="#1b1b1b", disabledforeground="#646464")
        self.output = tk.StringVar()
        self.ready = tk.BooleanVar()
        self.placeholder_state = None
        self.label = label
        self.placeholder = "{}...".format(label)
        self.add_placeholder(self.placeholder)
        self.input.trace('w', self.get_text)

        self.pack(fill=tk.X, expand=1)

    # noinspection PyUnusedLocal
    def get_text(self, *args, **kwargs):
        if self.input.get() != ("" or self.label):
            self.output.set(self.input.get())
            if self.output.get() != "":
                self.ready.set(True)
            else:
                self.ready.set(False)

    class PlaceholderState(object):
        __slots__ = ('normal_color', 'normal_font', 'placeholder_text',
                     'placeholder_color', 'placeholder_font', 'with_placeholder')

    def add_placeholder(self, placeholder, color='grey', font=None):
        normal_color = self.cget('fg')
        normal_font = self.cget('font')

        if font is None:
            font = normal_font

        state = EntryCustom.PlaceholderState()
        state.normal_color = normal_color
        state.normal_font = normal_font
        state.placeholder_color = color
        state.placeholder_font = font
        state.placeholder_text = placeholder
        state.with_placeholder = True

        # noinspection PyUnusedLocal
        def on_focusin(event, field=state):
            if field.with_placeholder:
                self.delete(0, 'end')
                self.config(fg=state.normal_color, font=state.normal_font)

                field.with_placeholder = False

        # noinspection PyUnusedLocal
        def on_focusout(event, field=state):
            if self.get() == "":
                self.insert(0, state.placeholder_text)
                self.config(fg=state.placeholder_color, font=state.placeholder_font)

                field.with_placeholder = True

        self.insert(0, placeholder)
        self.config(fg=color, font=font)

        self.bind('<FocusIn>', on_focusin, add='+')
        self.bind('<FocusOut>', on_focusout, add='+')

        self.placeholder_state = state

        return state

# Subclassing text to make all the tab button focus the next widget instead of entering a tab.
class TextCustom(tk.Text):
    def __init__(self, window, *args, **kwargs):
        tk.Text.__init__(self, window, width=50, height=1, state='normal', borderwidth=1, relief=tk.SUNKEN,
                         *args, **kwargs)
        self.pack(fill=tk.BOTH, expand=True)
        self.bind("<Tab>", focus_next_widget)

        # self.config(bg="#1b1b1b", fg="#dedede")

# There was probably a better way to incorporate this button, but it was very much an afterthought
# added almost a year and a half after the rest of the codebase.
class ButtonCustom(tk.Button):
    def __init__(self, window, *args, **kwargs):
        tk.Button.__init__(self, window, height=1, width=3, fg="black", command=None, *args, **kwargs)
        self.pack(expand=0)

# The EpisodeFrame should expand on x-axis, and hass entries for title, guest, season, number, UUID.
class EpisodeFrame(WideFrame):
    def __init__(self, window, *args, **kwargs):
        self.ready = tk.BooleanVar()
        self.fields = []
        WideFrame.__init__(self, window, *args, **kwargs)
        self.ep_title = EntryCustom(self, "Episode Title")
        self.ep_guest = EntryCustom(self, "Episode Guest")
        self.ep_guest.configure(takefocus=False)
        self.ep_season = EntryCustom(self, "Season")
        self.ep_number = EntryCustom(self, "Episode Airing Order")
        self.ep_uuid = EntryCustom(self, "Episode UUID")
        self.fields.extend([self.ep_title, self.ep_season, self.ep_number, self.ep_uuid])
        [field.ready.trace('w', self.ready_set) for field in self.fields]

    # noinspection PyUnusedLocal
    def ready_set(self, *args, **kwargs):
        if self.ep_title.ready.get() and \
                self.ep_guest.ready.get() and \
                self.ep_season.ready.get() and \
                self.ep_number.ready.get() and \
                self.ep_uuid.ready.get():
            self.ready.set(True)
        else:
            self.ready.set(False)


class NClipsFrame(WideFrame):
    def __init__(self, window, *args, **kwargs):
        WideFrame.__init__(self, window, *args, **kwargs)

        class LabelCustom(tk.Label):
            def __init__(self, n_clips_frame, label="Enter number of clips:"):
                tk.Label.__init__(self,
                                  n_clips_frame,
                                  text=label,
                                  anchor=tk.W)
                self.pack(fill=tk.X)

        class ScaleCustom(tk.Scale):
            def __init__(self, n_clips_frame, starting=3, ending=5):
                self.value = tk.IntVar()
                tk.Scale.__init__(self,
                                  n_clips_frame,
                                  from_=starting,
                                  to=ending,
                                  variable=self.value,
                                  orient=tk.HORIZONTAL,
                                  tickinterval=1)
                self.value.set(4)
                self.pack(padx=10, fill=tk.X, expand=1)

        self.label = LabelCustom(self)
        self.scale = ScaleCustom(self)


class PodFrame(WideFrame):
    def __init__(self, window, *args, **kwargs):
        WideFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.fields = []
        self.pod_title = EntryCustom(self, "Podcast Title")
        self.pod_description = EntryCustom(self, "Podcast Description")
        self.pod_preroll_adv = EntryCustom(self, "Pre-Roll Advertisers")
        self.pod_adlocations = EntryCustom(self, "Mid/Post-Roll AdLocations")
        self.pod_midroll_adv = EntryCustom(self, "Mid-Roll Advertisers")
        self.pod_postroll_adv = EntryCustom(self, "Post-Roll Advertisers")
        self.fields.extend([self.pod_title,
                            self.pod_description,
                            self.pod_preroll_adv,
                            self.pod_adlocations,
                            self.pod_midroll_adv,
                            self.pod_postroll_adv])
        [field.ready.trace('w', self.ready_set) for field in self.fields]

    # noinspection PyUnusedLocal
    def ready_set(self, *args, **kwargs):
        if self.pod_title.ready.get() and \
                self.pod_description.ready.get() and \
                self.pod_preroll_adv.ready.get() and \
                self.pod_adlocations.ready.get() and \
                self.pod_midroll_adv.ready.get() and \
                self.pod_postroll_adv.ready.get():
            self.ready.set(True)
        else:
            self.ready.set(False)


class ClipsFrame(FullFrame):

    # noinspection PyShadowingNames
    class ClipFrame(WideFrame):
        def __init__(self, window, number, total_clips, *args, **kwargs):
            WideFrame.__init__(self, window, *args, **kwargs)
            self.pack_configure(pady=(0, 5))
            self.ready = tk.BooleanVar()
            self.fields = []
            self.active = tk.BooleanVar()
            self.number = number
            self.total_clips = total_clips
            self.title = EntryCustom(self, "Clip {} Title".format(self.number))
            self.description = EntryCustom(self, "Clip {} Description".format(self.number))
            self.uuid = EntryCustom(self, "Clip {} UUID".format(self.number))
            self.fields.extend([self.title, self.description, self.uuid])
            [field.ready.trace('w', self.ready_set) for field in self.fields]

        # noinspection PyUnusedLocal
        def ready_set(self, *args, **kwargs):
            if self.title.ready.get() and self.description.ready.get() and self.uuid.ready.get():
                self.ready.set(True)
            else:
                self.ready.set(False)

    def __init__(self, window, *args, **kwargs):
        FullFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.fields = []
        self.total_clips = 4
        self.clips = [self.ClipFrame(self, n, self.total_clips) for n in range(1, 6)]
        # noinspection PyTypeChecker
        self.clips.insert(0, self.total_clips)
        self.fields.extend(self.clips[1:])
        [field.ready.trace('w', self.ready_set) for field in self.fields]
        self.show_or_hide_clips()

    # noinspection PyUnusedLocal
    def show_or_hide_clips(self, value=None, *args, **kwargs):
        if value is not None:
            self.total_clips = value
        for clip in self.clips[1:]:
            if clip.number > self.total_clips:
                clip.active.set(False)
                clip.pack_forget()
            else:
                clip.active.set(True)
                clip.pack(pady=(0, 10), fill=tk.X, expand=1)

    # noinspection PyUnusedLocal
    def ready_set(self, *args, **kwargs):
        for clip in self.clips[1:]:
            if clip.active.get():
                if clip.ready.get():
                    self.ready.set(True)
                else:
                    self.ready.set(False)


class ResultFrame(FullFrame):
    def __init__(self, window, *args, **kwargs):
        FullFrame.__init__(self, window, *args, **kwargs)
        self.pack_configure(pady=5)
        self.button = ButtonCustom(self)
        self.label = tk.Label(self)
        self.label.pack()
        self.label.pack_configure(side=tk.RIGHT)
        self.button.pack_configure(side=tk.RIGHT)


class EpisodeURLFrame(ResultFrame):
    def __init__(self, window, *args, **kwargs):
        ResultFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.episode_url = TextCustom(self)
        self.label.configure(text="Copy:")
        self.button.configure(text="Copy", command=self.copy_to_clipboard)
        self.episode_url.configure(wrap=tk.NONE)
        self.episode_url.pack_configure(fill=tk.X)
        self.pack_configure(fill=tk.X, expand=0)

    def copy_to_clipboard(self):
        url = self.episode_url.get('1.0', 'end'+'-1c')
        process = subprocess.Popen(
            'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
        process.communicate(url.encode('utf-8'))


class PublishEmailFrame(ResultFrame):
    def __init__(self, window, *args, **kwargs):
        ResultFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.label.configure(text="Copy:")
        self.button.configure(text="Copy", command=self.copy_to_clipboard)
        self.email1 = TextCustom(self)
        # self.email2 = TextCustom(self)

    def copy_to_clipboard(self):
        email = self.email1.get('1.0', 'end'+'-1c')
        process = subprocess.Popen(
            'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
        process.communicate(email.encode('utf-8'))


class SiteEmailFrame(ResultFrame):
    def __init__(self, window, *args, **kwargs):
        ResultFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.label.configure(text="Email:")
        self.site_subject_frame = BaseFrame(self)
        self.site_subject_frame.pack(fill=tk.X, expand=0)
        self.site_email_subject = TextCustom(self.site_subject_frame)
        self.site_email_subject.configure(wrap=tk.NONE)
        self.site_email_subject.pack_configure(fill=tk.X)
        self.site_email_body = TextCustom(self)


class PodcastEmailFrame(ResultFrame):
    def __init__(self, window, *args, **kwargs):
        ResultFrame.__init__(self, window, *args, **kwargs)
        self.ready = tk.BooleanVar()
        self.label.configure(text="Email:")
        self.podcast_subject_frame = BaseFrame(self)
        self.podcast_subject_frame.pack(fill=tk.X, expand=0)
        self.podcast_email_subject = TextCustom(self.podcast_subject_frame)
        self.podcast_email_subject.pack_configure(fill=tk.X)
        self.podcast_email_subject.configure(wrap=tk.NONE)
        self.podcast_email_body = TextCustom(self)


class MainUILayout(FullFrame):

    class TopFrame(BaseFrame):
        def __init__(self, window, *args, **kwargs):
            BaseFrame.__init__(self, window, *args, **kwargs)
            self.pack(fill=tk.X, pady=10)
            self.subtitle = tk.Label(self,
                                     text="a.k.a. TITLE1",
                                     anchor=tk.S)
            self.subtitle.pack()

    class MiddleFrame(FullFrame):
        def __init__(self, window, *args, **kwargs):
            FullFrame.__init__(self, window, *args, **kwargs)
            self.pack_configure(padx=10)
            self.input_frame_left = FullFrame(self)
            self.input_frame_left.pack_configure(padx=(0, 5), side=tk.LEFT)
            self.input_frame_right = FullFrame(self)
            self.input_frame_right.pack_configure(padx=(5, 0), side=tk.LEFT)
            self.results_frame = FullFrame(self)
            self.results_frame.pack_configure(padx=10, side=tk.RIGHT)

    class BottomFrame(BaseFrame):
        def __init__(self, window, *args, **kwargs):
            BaseFrame.__init__(self, window, *args, **kwargs)
            self.pack(fill=tk.X, pady=(5, 10))
            self.username = EntryCustom(self, "Enter your name (First Last)...")
            self.username.pack(side=tk.LEFT, expand=0, padx=30)
            self.change_title = tk.BooleanVar()
            tk.Checkbutton(self, variable=self.change_title, takefocus=False, anchor=tk.N).pack(side=tk.RIGHT, padx=30)
            tk.Label(self, text="Change the Title...").pack(side=tk.RIGHT)

    def __init__(self, window, *args, **kwargs):
        FullFrame.__init__(self, window, *args, **kwargs)
        self.top_frame = self.TopFrame(self)
        self.middle_frame = self.MiddleFrame(self)
        self.bottom_frame = self.BottomFrame(self)


def episode_date():
    now = datetime.datetime.now()
    if now.strftime("%H:%M:%S") < datetime.time(12, 0).strftime("%H:%M:%S"):
        now = now - datetime.timedelta(days=1)
    return now.strftime("%m/%d/%y")


class Episode(object):
    title = str(None)
    season = str(None)
    number = str(None)
    uuid = str(None)
    guest_str = str(None)
    clip_info = []
    username = str(None)
    date = episode_date()

    class Clip(object):
        total_clips = None
        guest_list = None

        def __init__(self, number=None, title=None, description=None, uuid=None):
            self.number = number
            self.title = title
            self.description = description
            self.uuid = uuid

        def update_clip(self, title, description, uuid):
            self.title = title
            self.description = description
            self.uuid = uuid
            return self.title, self.description, self.uuid

        @property
        def active(self):
            if self.number > self.total_clips:
                return False
            else:
                return True

        @property
        def url(self):
            return "https://www.website.com/episode-clips/{0}/the-episode-title-{1}".format(
                self.uuid, re.sub(r'-{2,}', '-', re.sub(r'[\W]', '-', self.title.lower())))

        @property
        def publish_email_string(self):
            if self.guest_list is None:
                return "Clip {}: {}".format(self.number, self.url)
            elif self.title.endswith(" - Extended"):
                return "Extended: {}".format(self.url)
            else:
                if len(self.guest_list) > 1:
                    if any(guest in self.guest_list for guest in self.title):
                        return "Non-extended: {}".format(self.url)
                elif self.guest_list[0] in self.title:
                    return "Non-extended: {}".format(self.url)
                else:
                    return "Clip {}: {}".format(self.number, self.url)

        @property
        def site_email_script_string(self):
            return """<b>{0}</b><br><i>{1}</i><br><a href='\\''{2}'\\''>{2}</a>""".format(re.sub("'", "'\\''",
                                                                                                re.sub('"', '\\"',
                                                                                                        self.title)),
                                                                                          re.sub("'", "'\\''",
                                                                                                 re.sub('"', '\\"',
                                                                                                        self.description
                                                                                                        )),
                                                                                          re.sub("'", "'\\''",
                                                                                                 re.sub('"', '\\"',
                                                                                                        self.url)))

        @property
        def site_email_string(self):
            return """{0}\n{1}\n{2}\n""".format(self.title, self.description, self.url)

    def __init__(self):
        self.clip_info.append(None)
        self.Clip.total_clips = self.clip_info[0]
        self.Clip.guest_list = self.guest_list

    @property
    def guest_list(self):
        if self.title is None:
            pass
        elif self.title in ("", "Episode Title..."):
            return ["Episode Guest..."]
        elif self.title.rfind(" - ") > -1:
            guests = self.title[(self.title.rfind(" - ") + 3):]
            if guests.rfind(" & ") > -1 or guests.rfind(", ") > -1:
                guests.replace(" & ", ", ")
                return guests.split(", ")
            else:
                return [guests]
        else:
            pass

    @property
    def guest(self):
        if self.guest_list is None or self.guest_list == ["Episode Guest..."]:
            return "Episode Guest..."
        elif len(self.guest_list) > 1:
            return "{}".format(" & ".join(self.guest_list))
        else:
            return self.guest_list[0]

    # noinspection PyAttributeOutsideInit
    @guest.setter
    def guest(self, value):
        self._guest = value

    @property
    def url(self):
        if self.title is None:
            pass
        else:
            return "https://www.website.com/full-episodes/{0}/the-episode-title-{1}-season-{2}-ep-{3}".format(
                self.uuid,
                re.sub(r'-{2,}', '-', re.sub(r'[\W]', '-', self.title.lower())),
                self.season.lstrip("0"),
                self.number.lstrip("0"))

    @property
    def clips(self):
        if len(self.clip_info) > 2:
            clips = [self.Clip(n, self.clip_info[n][0], self.clip_info[n][1],
                               self.clip_info[n][2]) for n in range(1, self.clip_info[0] + 1)]
            # noinspection PyTypeChecker
            clips.insert(0, self.clip_info[0])
            return clips

    @property
    def email_string(self):
        return """Full Episode: {0}""".format(self.url)

    @property
    def email_script_string(self):
        return """<b>Full Episode:</b> <a href='\\''{0}'\\''>{0}</a>""".format(self.url)

    @property
    def publish_email_1(self):
        if self.clips[1] is None:
            pass
        else:
            return """{0}

{1}""".format(self.email_string, "\n".join(clip.publish_email_string for clip in self.clips[1:]))

    @property
    def publish_email_2(self):
        return """Hey all,<p>The Episde page has updated and is now reflecting tonight's content!\
<p>Best,<br>{0}""".format(self.username)

    @property
    def site_email_subject(self):
        subject = "[NEW CLIPS] The Episode - {0} - {1}".format(self.date, self.guest)
        subject = subject.rstrip()
        return subject

    @property
    def site_email_body(self):
        if self.clips[1] is None:
            pass
        else:
            return """Good morning,
            
Below are clips for the {0} episode of The Episode!

{1}

{2}

Best,
{3}""".format(self.date, "\n".join((clip.site_email_string for clip in self.clips[1:self.clip_info[0] + 1])),
              self.email_string, self.username)

    @property
    def site_email_script_body(self):
        if self.clips[1] is None:
            pass
        else:
            return """Good morning,<p>Below are clips for the {0} episode of The Episode!<p>{1}<p>{2}<p>\
Best,<br>{3}""".format(self.date, "<p>".join(
                (clip.site_email_script_string for clip in self.clips[1:self.clip_info[0] + 1])),
                       self.email_script_string, self.username)


class Podcast:
    username = str(None)
    date = episode_date

    def __init__(self,
                 title=None,
                 description=None,
                 pre_roll_ads=None,
                 adlocations=None,
                 mid_roll_ads=None,
                 post_roll_ads=None):
        self.title = title
        self.description = description
        self.preroll_ads = pre_roll_ads
        self.adlocations = adlocations
        # self.midroll_tc = self.adlocations[:-1].join(", ")
        self.midroll_ads = mid_roll_ads
        # self.postroll_tc = self.adlocations[-1].join()
        self.postroll_ads = post_roll_ads

    @property
    def subject(self):
        subject = "The Episode Podcast - {0}: {1}".format(self.date, self.title)
        subject = subject.rstrip()
        return subject

    @property
    def body(self):
        return """Hey all,
        
Tonight's podcast episode information below:

{0}
{1}

Ad Pre-Roll: 00:05 - {2}
Ad Mid-Roll: {3} - {4}
Ad Post-Roll: {5} - {6}
URL: https://itunes.apple.com/us/podcast/the-episode-podcast/id1234567890?mt=2

Best,
{7}""".format(self.title,
              self.description,
              self.preroll_ads,
              ", ".join(self.adlocations[:-1]),
              self.midroll_ads,
              self.adlocations[-1],
              self.postroll_ads,
              self.username)

    @property
    def script_body(self):
        return """Hey all,<p>Tonight'\\''s podcast episode information below:\
<p><b>{0}</b><br><i>{1}</i><p><i>Ad Pre-Roll:</i> 00:05 - {2}<br><i>Ad Mid-Roll:</i> {3} - {4}<br><i>Ad Post-Roll:\
</i> {5} - {6}<br><i>URL:</i> <a href='\\''https://itunes.apple.com/us/podcast/the-episode-podcast/id1234567890?mt=2'\\''>https://itunes.apple.com/us/podcast/the-episode-podcast/\
id1234567890?mt=2</a><p>Best,<br>{7}""".format(self.title,
                                               re.sub("'", "'\\''", re.sub('"', '\\"', self.description)),
                                               self.preroll_ads,
                                               ", ".join(self.adlocations[:-1]),
                                               self.midroll_ads,
                                               self.adlocations[-1],
                                               self.postroll_ads,
                                               self.username)


class EpisodeApp(Window):
    def __init__(self, *args, **kwargs):
        Window.__init__(self, *args, **kwargs)
        self.title("Title 1")
        self.main_ui = MainUILayout(self)
        self.ep_logic = Episode()
        self.pod_logic = Podcast()
        self.main_ui.bottom_frame.change_title.trace('w', self.changing_title)
        self.episode_frame = EpisodeFrame(self.main_ui.middle_frame.input_frame_left)
        self.n_clips_frame = NClipsFrame(self.main_ui.middle_frame.input_frame_left)
        self.pod_frame = PodFrame(self.main_ui.middle_frame.input_frame_left)
        self.clips_frame = ClipsFrame(self.main_ui.middle_frame.input_frame_right)
        self.episode_url_frame = EpisodeURLFrame(self.main_ui.middle_frame.results_frame)
        self.publish_email_frame = PublishEmailFrame(self.main_ui.middle_frame.results_frame)
        self.site_email_frame = SiteEmailFrame(self.main_ui.middle_frame.results_frame)
        self.site_email_frame.button.configure(text="Email", command=self.email_site)
        self.podcast_email_frame = PodcastEmailFrame(self.main_ui.middle_frame.results_frame)
        self.podcast_email_frame.button.configure(text="Email", command=self.email_podcast)
        # Initial Logic Set
        self.update_logic()
        self.update_guest()
        # Traces
        self.n_clips_frame.scale.value.trace(
            'w', lambda var_name, var_index, operation: self.clips_frame.show_or_hide_clips(
                self.n_clips_frame.scale.value.get()))

        self.main_ui.bottom_frame.username.ready.trace('w', self.update_logic)
        self.episode_frame.ep_title.ready.trace('w', self.update_logic)
        self.episode_frame.ep_season.ready.trace('w', self.update_logic)
        self.episode_frame.ep_number.ready.trace('w', self.update_logic)
        self.episode_frame.ep_uuid.ready.trace('w', self.update_logic)
        self.episode_frame.ep_title.ready.trace('w', self.update_guest)
        # self.episode_frame.ep_guest.ready.trace('w', self.update_guest)
        self.pod_frame.pod_title.ready.trace('w', self.update_logic)
        self.pod_frame.pod_description.ready.trace('w', self.update_logic)
        self.pod_frame.pod_preroll_adv.ready.trace('w', self.update_logic)
        self.pod_frame.pod_adlocations.ready.trace('w', self.update_logic)
        self.pod_frame.pod_midroll_adv.ready.trace('w', self.update_logic)
        self.pod_frame.pod_postroll_adv.ready.trace('w', self.update_logic)
        self.n_clips_frame.scale.value.trace('w', self.update_logic)
        [(clip.title.ready.trace('w', self.update_logic), clip.description.ready.trace('w', self.update_logic),
          clip.uuid.ready.trace('w', self.update_logic))
         for clip in self.clips_frame.clips[1:] if clip.active.get()]
        self.episode_frame.ready.trace('w', self.update_results)
        self.pod_frame.ready.trace('w', self.update_results)
        self.clips_frame.ready.trace('w', self.update_results)
        self.update()

    def email_site(self):
        if sys.platform == "darwin":
            email_script = """/usr/bin/osascript \
-e 'tell application "Microsoft Outlook.app"' \
-e 'set newMessage to make new outgoing message with properties {{subject: "{0}", content: "{1}"}}' \
-e 'make new recipient at newMessage with properties {{email address:{{name:"{2}"}}}}' \
-e 'open newMessage' -e 'end tell'"""
            site_email = email_script.format(self.site_email_frame.site_email_subject.get('1.0', 'end'+'-1c'),
                                             self.ep_logic.site_email_script_body, "Site")
            bell_email = email_script.format(self.site_email_frame.site_email_subject.get('1.0', 'end' + '-1c'),
                                             re.sub("<b>Full", "<b>Download Here:</b> <p><b>Full",
                                                    self.ep_logic.site_email_script_body), "Bell")
            print(site_email)
            print(bell_email)
            os.system(site_email)
            os.system(bell_email)

    def email_podcast(self):
        if sys.platform == "darwin":
            email_script = """/usr/bin/osascript \
-e 'tell application "Microsoft Outlook.app"' \
-e 'set newMessage to make new outgoing message with properties {{subject: "{0}", content: "{1}"}}' \
-e 'make new recipient at newMessage with properties {{email address:{{name:"{2}"}}}}' \
-e 'open newMessage' -e 'end tell'"""
            podcast_email = email_script.format(self.podcast_email_frame.podcast_email_subject.get('1.0', 'end'+'-1c'),
                                             self.pod_logic.script_body, "Podcast")
            print(podcast_email)
            os.system(podcast_email)

    # noinspection PyUnusedLocal
    def update_logic(self, *args, **kwargs):
        self.ep_logic.username = self.main_ui.bottom_frame.username.get()
        self.pod_logic.username = self.main_ui.bottom_frame.username.get()
        self.ep_logic.title = self.episode_frame.ep_title.get()
        self.ep_logic.season = self.episode_frame.ep_season.get()
        self.ep_logic.number = self.episode_frame.ep_number.get()
        self.ep_logic.uuid = self.episode_frame.ep_uuid.get()
        self.episode_frame.ep_guest.input.set(self.ep_logic.guest)
        if self.episode_frame.ep_guest.input.get() not in {"Episode Guest...", ""}:
            self.episode_frame.ep_guest.input.set(self.ep_logic.guest)
            self.episode_frame.ep_guest.placeholder = self.ep_logic.guest

        # self.episode_frame.ep_guest.placeholder = self.ep_logic.guest
        self.ep_logic.clip_info[0] = self.n_clips_frame.scale.value.get()
        self.ep_logic.clip_info[1:] = [(clip.title.get(), clip.description.get(), clip.uuid.get())
                                       for clip in self.clips_frame.clips[1:]]
        self.pod_logic.title = self.pod_frame.pod_title.get()
        self.pod_logic.description = self.pod_frame.pod_description.get()
        self.pod_logic.preroll_ads = self.pod_frame.pod_preroll_adv.get()
        self.pod_logic.adlocations = (self.pod_frame.pod_adlocations.get()).split(", ")
        self.pod_logic.midroll_ads = self.pod_frame.pod_midroll_adv.get()
        self.pod_logic.postroll_ads = self.pod_frame.pod_postroll_adv.get()
        self.ep_logic.Clip.guest_list = self.ep_logic.guest_list
        self.update_results()

    # noinspection PyUnusedLocal
    def update_results(self, *args, **kwargs):
        self.episode_url_frame.episode_url.configure(state='normal')
        self.episode_url_frame.button.configure(state='normal')
        self.publish_email_frame.email1.configure(state='normal')
        self.publish_email_frame.button.configure(state='normal')
        # self.publish_email_frame.email2.configure(state='normal')
        self.site_email_frame.site_email_subject.configure(state='normal')
        self.site_email_frame.site_email_body.configure(state='normal')
        self.site_email_frame.button.configure(state='normal')
        self.podcast_email_frame.podcast_email_subject.configure(state='normal')
        self.podcast_email_frame.podcast_email_body.configure(state='normal')
        self.podcast_email_frame.button.configure(state='normal')
        self.episode_url_frame.episode_url.delete("1.0", 'end')
        self.publish_email_frame.email1.delete("1.0", 'end')
        # self.publish_email_frame.email2.delete("1.0", 'end')
        self.site_email_frame.site_email_subject.delete("1.0", 'end')
        self.site_email_frame.site_email_body.delete("1.0", 'end')
        self.podcast_email_frame.podcast_email_subject.delete("1.0", 'end')
        self.podcast_email_frame.podcast_email_body.delete("1.0", 'end')
        self.episode_url_frame.episode_url.insert('1.0', self.ep_logic.url)
        self.publish_email_frame.email1.insert('1.0', self.ep_logic.publish_email_1)
        # self.publish_email_frame.email2.insert('1.0', self.ep_logic.publish_email_2)
        self.site_email_frame.site_email_subject.insert('1.0', self.ep_logic.site_email_subject)
        self.site_email_frame.site_email_body.insert('1.0', re.sub("'\''", "'",
                                                                   re.sub('\\"', '"', self.ep_logic.site_email_body)))
        # self.site_email_frame.site_email_body.insert('1.0', self.ep_logic.site_email_body)
        self.podcast_email_frame.podcast_email_subject.insert('1.0', self.pod_logic.subject)
        self.podcast_email_frame.podcast_email_body.insert('1.0', re.sub("\\'\\\'\\'", "'",
                                                                   re.sub('\\"', '"', self.pod_logic.body)))
        # self.podcast_email_frame.podcast_email_body.insert('1.0', self.pod_logic.body)
        self.episode_url_frame.episode_url.configure(state='disabled')
        self.episode_url_frame.button.configure(state='disabled')
        self.publish_email_frame.email1.configure(state='disabled')
        self.publish_email_frame.button.configure(state='disabled')
        # self.publish_email_frame.email2.configure(state='disabled')
        self.site_email_frame.site_email_subject.configure(state='disabled')
        self.site_email_frame.site_email_body.configure(state='disabled')
        self.site_email_frame.button.configure(state='disabled')
        self.podcast_email_frame.podcast_email_subject.configure(state='disabled')
        self.podcast_email_frame.podcast_email_body.configure(state='disabled')
        self.podcast_email_frame.button.configure(state='disabled')
        if self.episode_frame.ready.get():
            self.episode_url_frame.episode_url.configure(state='normal')
            self.episode_url_frame.button.configure(state='normal')
            if self.clips_frame.ready.get():
                self.publish_email_frame.email1.configure(state='normal')
                self.publish_email_frame.button.configure(state='normal')
        #        self.publish_email_frame.email2.configure(state='normal')
                self.site_email_frame.site_email_subject.configure(state='normal')
                self.site_email_frame.site_email_body.configure(state='normal')
                self.site_email_frame.button.configure(state='normal')
            else:
                self.publish_email_frame.email1.configure(state='disabled')
                self.publish_email_frame.button.configure(state='disabled')
        #       self.publish_email_frame.email2.configure(state='disabled')
                self.site_email_frame.site_email_subject.configure(state='disabled')
                self.site_email_frame.site_email_body.configure(state='disabled')
                self.site_email_frame.button.configure(state='disabled')
        else:
            self.episode_url_frame.episode_url.configure(state='disabled')
            self.episode_url_frame.button.configure(state='disabled')
        if self.pod_frame.ready.get():
            self.podcast_email_frame.podcast_email_subject.configure(state='normal')
            self.podcast_email_frame.podcast_email_body.configure(state='normal')
            self.podcast_email_frame.button.configure(state='normal')
        else:
            self.podcast_email_frame.podcast_email_subject.configure(state='disabled')
            self.podcast_email_frame.podcast_email_body.configure(state='disabled')
            self.podcast_email_frame.button.configure(state='disabled')

    # noinspection PyUnusedLocal
    def update_guest(self, *args, **kwargs):
        self.ep_logic.guest = self.episode_frame.ep_uuid.get()
        if self.episode_frame.ep_guest.get() in {"Episode Guest...", ""}:
            self.episode_frame.ep_guest.configure(state='disabled')
        else:
            self.episode_frame.ep_guest.placeholder = self.ep_logic.guest
            self.episode_frame.ep_guest.configure(state='normal')

    # noinspection PyUnusedLocal
    def changing_title(self, *args, **kwargs):
        if self.main_ui.bottom_frame.change_title.get():
            self.title("Title 2")
            self.main_ui.top_frame.subtitle.configure(text="a.k.a. TITLE2")
        else:
            self.title("Title 1")
            self.main_ui.top_frame.subtitle.configure(text="a.k.a. TITLE1")


if __name__ == '__main__':
    root = EpisodeApp()
    root.mainloop()
