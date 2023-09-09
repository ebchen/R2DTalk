import time
from flask import Flask, redirect, request, url_for
from twilio.twiml.voice_response import VoiceResponse
import os
from twilio.rest import Client

account_sid = 'AC5e69a82ff2fcd6e939928a173c9baf3d'
auth_token = '7291ec85c150b95270f58596c3d01267'
client = Client(account_sid, auth_token)

app = Flask(__name__)

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming phone calls"""
    resp = VoiceResponse()

    resp.say('Hello, this is Pam at Dim Sum House. How can I help?')
    resp.record(maxLength=5)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True, port=5000)