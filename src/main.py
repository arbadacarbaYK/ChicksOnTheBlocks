#This file is relevant for Kivy and imports parts needed for the UI 
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from MainPanel import MainPanel
from ConfigureScreen import Configure

Config.set('graphics', 'fullscreen', 'auto') # 'auto' -> Fullscreen | '0' -> NormalMode


class MyScreenManager(ScreenManager):
    pass


myfile = open('window-image-conf', 'r')

root_widget = Builder.load_string(myfile.read())


class Panel(App):
    def build(self):
        return root_widget


if __name__ == "__main__":
    Panel().run()
