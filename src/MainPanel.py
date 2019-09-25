import time
import json
from kivy.core.text import Label
from drinks import drink_list, ingredients
from kivy.properties import StringProperty, ListProperty
from kivy.uix.progressbar import ProgressBar
from functools import partial
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.image import Image
from kivy.clock import Clock
from database import Database
from HectorConfig import config
from pygame import mixer

## Für LND-Script (if file exists)
from pathlib import Path
import subprocess

from HectorHardware import HectorHardware


class MainPanel(Screen):
    buttonText = ListProperty([StringProperty(),
                               StringProperty(),
                               StringProperty(),
                               StringProperty(),
                               StringProperty(),
                               StringProperty(),
                               StringProperty(),
                               StringProperty()])

    buttonColor = ListProperty([ListProperty(),
                                ListProperty(),
                                ListProperty(),
                                ListProperty(),
                                ListProperty(),
                                ListProperty(),
                                ListProperty(),
                                ListProperty()])

    db = None
    drinkOnScreen = None
    screenPage = None
    maxScreenPage = None

    def __init__(self, **kwargs):
        super(MainPanel, self).__init__(**kwargs)

        self.db = Database("h9k")

        self.db.createIfNotExists()

        self.screenPage = 1

        items = len(drink_list) % 8
        self.maxScreenPage = (len(drink_list) // 8)

        if items > 0:
            self.maxScreenPage += 1

        self.drinkOnScreen = list()
        self.drinkOnScreen = drink_list[:8]

        self.fillButtons(self.drinkOnScreen)
        self.initVent()

    def initVent(self):
        print("Prepare vets.")
        h = HectorHardware(config)
        h.light_on()
        time.sleep(1)
        h.arm_in()

        h.pump_stop()
        for vnum in range(12):
            print("Vent %d closing..." % (vnum,))
            time.sleep(1)
            h.valve_close(vnum)
        h.light_off()

    def isalcoholic(self, drink):
        for ing, _ in drink["recipe"]:
            if ingredients[ing][1]: return True
        return False

    def fillButtons(self, drinks):
        countDrinksOnScreen = len(drinks)
        count = 0
        while count < countDrinksOnScreen:
            self.buttonText[count] = drinks[count]['name']
            if self.buttonText[count].startswith("..."):
                self.buttonColor[count] = [.3, .3, .3, 1]
            elif self.isalcoholic(drinks[count]):
                self.buttonColor[count] = [1, 0, 0, 1]
            else: # non-alcoholic
                self.buttonColor[count] = [0, 1, 0, 1]
            count += 1

        while count < 8:
            self.buttonText[count] = ''
            self.buttonColor[count] = [1, 1, 1, 1]
            count += 1

    def choiceDrink(self, *args):
        self.readPumpConfiguration()
        if len(self.drinkOnScreen) -1 < args[0]:
            print("no drinks found.")
            return

        ## Start Script to create Invoice
        print("start lnd-invoicetoqr.sh")
        subprocess.call("lnd/lnd-invoicetoqr.sh")
        print("end lnd-invoicetoqr.sh")

        root = BoxLayout(orientation='vertical')
        root2 = BoxLayout()
        root2.add_widget(Image(source='lnd/temp/tempQRCode.png'))
        root2.add_widget(
            Label(text='Please be sure\n that a glass \nwith min 200 ml \nis placed onto the black fixture.', font_size='30sp'))
        root.add_widget(root2)

        ## This was commented out to be sure the user only gets a drink after paying the bill.
        #contentOK = Button(text='OK', font_size=60, size_hint_y=0.15)
        #root.add_widget(contentOK)

        contentCancel = Button(text='Cancel', font_size=60, size_hint_y=0.15)
        root.add_widget(contentCancel)

        popup = Popup(title='Not your coins, not your cocktail :-)', content=root,
                      auto_dismiss=False)

        ## This was commented out to be sure the user only gets a drink after paying the bill.
        #def closeme(button):
        #    popup.dismiss()
        #    Clock.schedule_once(partial(self.doGiveDrink, args[0]), .01)

        ## This was commented out to be sure the user only gets a drink after paying the bill.
        #contentOK.bind(on_press=closeme)

        def cancelme(button):
            print("cancel button pressed")
            popup.dismiss()

        #Button cancel payment, is not working right now
        contentCancel.bind( on_press=cancelme )

        ## Beginn Function to periodically check the payment using lnd-checkinvoice1.sh
        def checkPayment(parent):

            print("start check script")

            ## while loop to check if lnd-checkinvoice1.sh returns SETTLED, if not wait for a second and start over
            paymentSettled = False
            counter = 0
            while paymentSettled == False:
                ## run lnd-checkinvoice1.sh and write output to variable s
                s = subprocess.check_output(["sh","lnd/lnd-checkinvoice1.sh"])
                print(s)
                counter +=1
                print( counter )

                ## check if s is 'SETTLED', if so, close popup and start doGiveDrink
                if (b'SETTLED' in s):
                    paymentSettled = True
                    popup.dismiss()
                    Clock.schedule_once(partial(self.doGiveDrink, args[0]), .01)
                elif (counter > 5):
                    paymentSettled = True
                    popup.dismiss()
                    Clock.schedule_once( partial( self.doGiveDrink, args[0] ), .01 )
                else:
                    ## if not 'SETTLED' wait a second and start over
                    paymentSettled = False
                    time.sleep(1)
                pass
            pass

            print("end check script")
            ## End Function to periodically check the payment using lnd-checkinvoice1.sh

        ## start 'checkPayment-loop' when loading popup
        popup.bind(on_open=checkPayment)

        popup.open()


    def doGiveDrink(self, drink, intervaltime):

        root = BoxLayout(orientation='vertical')
        content = Label(text='Take a break -- \nYour \n\n' + self.drinkOnScreen[drink]["name"]+'\n\nwill be mixed.', font_size='40sp')
        root.add_widget(content)
        popup = Popup(title='Life, the Universe, and Everything. There is an answer.', content=root,
                      auto_dismiss=False)
        mixer.init()
        mixer.music.load(/home/pi/Music/TestRaspi.mp3)
        mixer.music.play()


        def makeDrink(parentwindow):
            drinks = self.drinkOnScreen[drink]

            hector = HectorHardware(config)
            hector.light_on()
            time.sleep(1)
            hector.arm_out()

            for ingridient in drinks["recipe"]:
                hector.valve_dose(pumpList[ingridient[0]], ingridient[1])
                time.sleep(.1)
                print("IndexPumpe: ", pumpList[ingridient[0]])
                print("Ingredient: ", ingridient[0])
                print("Output in ml: ", ingridient[1])
                self.db.countUpIngredient(ingridient[0],ingridient[1])

            time.sleep(1)
            self.db.countUpDrink(drinks["name"])
            hector.arm_in()
            hector.light_off()
            hector.finger(1)
            hector.ping(3)
            hector.finger(0)
            print(drinks["name"])
            parentwindow.dismiss()

        popup.bind(on_open=makeDrink)

        popup.open()

    def back(self):
        if self.screenPage == 1:
            self.screenPage = self.maxScreenPage
        else:
            self.screenPage -= 1

        self.drinkOnScreen = drink_list[(self.screenPage * 8) - 8:8 * self.screenPage]
        self.fillButtons(self.drinkOnScreen)

    def forward(self):
        if self.screenPage == self.maxScreenPage:
            self.screenPage = 1
        else:
            self.screenPage += 1
        i = (self.screenPage * 8) - 8
        self.drinkOnScreen = drink_list[i:8 * self.screenPage]
        self.fillButtons(self.drinkOnScreen)

    def readPumpConfiguration(self):
        x = json.load(open('servo_config.json'))
        global pumpList
        pumpList = {}
        for key in x:
            chan = x[key]
            pumpList[chan['value']] = chan['channel']

        return pumpList

    pass
