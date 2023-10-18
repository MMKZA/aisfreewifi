from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform  # Import platform module
from kivy.clock import mainthread
import re, requests

# Import Android-specific classes
from jnius import autoclass, PythonJavaClass, java_method

# Define the URL for the AIS login
login_url = 'https://wifi.ais.co.th/login'  # Replace with the correct URL

class SMSReceiver(PythonJavaClass):
    __javainterfaces__ = ['android/content/BroadcastReceiver']

    @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
    def onReceive(self, context, intent):
        message = intent.getStringExtra("message")
        SMSReaderApp.process_sms(message)

class SMSReaderApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.text_input = TextInput(multiline=False, text='0991898463')
        layout.add_widget(Label(text='Enter Phone Number:'))
        layout.add_widget(self.text_input)
        login_button = Button(text='Login')
        login_button.bind(on_press=self.ais_login)
        layout.add_widget(login_button)
        self.sms_label = Label(text="Waiting for SMS...")
        layout.add_widget(self.sms_label)
        self.verification_label = Label(text="Verification Code: ")
        layout.add_widget(self.verification_label)
        return layout

    def on_start(self):
        if platform == 'android':
            self.register_sms_receiver()

    def register_sms_receiver(self):
        self.sms_receiver = SMSReceiver()
        filter = IntentFilter()
        filter.addAction("android.provider.Telephony.SMS_RECEIVED")
        context = autoclass('org.kivy.android.PythonActivity').mActivity
        context.registerReceiver(self.sms_receiver, filter)

    @mainthread
    def process_sms(self, message):
        verification_code = re.search(r'\d{6}', message).group(0) if re.search(r'\d{6}', message) else None

        if verification_code:
            self.verification_label.text = f"Verification Code: {verification_code}"
            self.sms_label.text = f"Verification Code Received: {verification_code}"
            self.ais_login(None, verification_code)

    def ais_login(self, instance, verification_code=None):
        # First, perform the initial registration POST request
        post_link = 'https://wifi.ais.co.th/register'
        phone_number = self.text_input.text
        payload = {
            'txtMobile': phone_number,
            'ddlOperator': 'True',
            'ddlAge': '18-24',
            'en_speak': 'true',
            'txtLanguage': 'EN',
        }
        post_response = requests.post(post_link, data=payload)

        # Check the response from the initial registration
        if post_response.status_code == 200:
            self.sms_label.text = "Registration Successful"
            self.sms_label.color = (0, 1, 0, 1)  # Set the label text color to green
        else:
            self.sms_label.text = "Registration Failed"
            self.sms_label.color = (1, 0, 0, 1)  # Set the label text color to red

        # If the verification code is provided (e.g., from SMS)
        if verification_code:
            # Use the provided verification code to make the login POST request
            login_link = 'https://wifi.ais.co.th/login'
            data = {
                'chkRememberMe': 'true',
                'txtUsername': f'{phone_number}@aisads',
                'txtPassword': verification_code,
            }
            login_response = requests.post(login_link, data=data)

            # Check the response from the login
            if login_response.status_code == 200:
                self.sms_label.text = "Login Successful"
                self.sms_label.color = (0, 1, 0, 1)  # Set the label text color to green
            else:
                self.sms_label.text = "Login Failed"
                self.sms_label.color = (1, 0, 0, 1)  # Set the label text color to red


if __name__ == '__main__':
    SMSReaderApp().run()
