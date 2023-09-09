import audioop
import base64
import json
import os
from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
import vosk

app = Flask(__name__)
sock = Sock(app)

account_sid = 'AC5e69a82ff2fcd6e939928a173c9baf3d'
auth_token = '7291ec85c150b95270f58596c3d01267'
twilio_client = Client(account_sid, auth_token)
model = vosk.Model('model')

CL = '\x1b[0K'
BS = '\x08'

transcribed_text = ""

@app.route('/call', methods=['POST'])
def call():
    """Accept a phone call."""
    global transcribed_text
    response = VoiceResponse()

    # Start the streaming
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)

    # Play your greeting
    response.play('https://audio.jukehost.co.uk/W9WoQPsIRF4BPOLNoU7b2RrqUrWaDHCh')

    # Add a pause
    response.pause(length=5)

    if transcribed_text:
        response.say(transcribed_text)
    else:
        response.say("Sorry, I couldn't transcribe your message.")

    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}




@sock.route('/stream')
def stream(ws):
    """Receive and transcribe audio stream."""
    global transcribed_text
    rec = vosk.KaldiRecognizer(model, 16000)
    while True:
        message = ws.receive()
        packet = json.loads(message)
        if packet['event'] == 'start':
            print('Streaming is starting')
        elif packet['event'] == 'stop':
            print('\nStreaming has stopped')
        elif packet['event'] == 'media':
            audio = base64.b64decode(packet['media']['payload'])
            audio = audioop.ulaw2lin(audio, 2)
            audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
            if rec.AcceptWaveform(audio):
                r = json.loads(rec.Result())
                transcribed_text = CL + r['text'] + ' '
                print(CL + r['text'] + ' ', end='', flush=True)
            else:
                r = json.loads(rec.PartialResult())
                transcribed_text = CL + r['partial'] + BS * len(r['partial'])
                print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)


if __name__ == '__main__':
    from pyngrok import ngrok
    port = 5000
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/call')
    print(f'Waiting for calls on {number.phone_number}')

    app.run(port=port)