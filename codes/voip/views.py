from django.shortcuts import render

from sfapp2.utils.twilio import send_sms, list_sms
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
import uuid


# To store session variables
sessionID_to_callsid = {}
sessionID_to_confsid = {}
sessionID_to_destNo = {}


# Generate a session id for conference
def get_session_id(source_number, destination_number):
    return 'Conf' + source_number + '-To-' + destination_number + '-' +uuid.uuid4().hex


def get_client():
    try:
        twilio_client = Client(settings.TWILIO['TWILIO_ACCOUNT_SID'], settings.TWILIO['TWILIO_AUTH_TOKEN'])
        return twilio_client
    except Exception as e:
        msg = "Missing configuration variable: {}".format(e)
        return JsonResponse({'error': msg})


@csrf_exempt
def send_sms_api(request):
    send_sms(request.POST.get("to_number"),
             request.POST.get("msg"))
    return JsonResponse({'message': 'success'})

@csrf_exempt
def list_sms_api(request):
    messages = list_sms(request.POST.get("to_number"))
    return JsonResponse({'messages': messages}, safe=False)


@csrf_exempt
def twilio_call_status(request):
    print(request.POST)
    return HttpResponse('')


@csrf_exempt
def voip_callback(request, session_id):
    # print(request.POST)
    print("## Conference request received, session id:{0} Making a conference call".format(session_id))

    resp = VoiceResponse()

    # If Twilio's request to our app included already gathered digits, process them
    if 'Digits' in request.POST:
        # Get which digit the caller chose
        choice = request.POST.get('Digits')

        # Say a different message depending on the caller's choice
        if choice == '1':
            resp.say('Adding destination number to the conference!')
            resp.redirect('http://3.137.150.83:8001/voip/api_voip/add_user/' + session_id)
            print(str(resp))
            return HttpResponse(resp)
        elif choice == '2':
            resp.say('Thank you for calling, have a nice day!')
            # End the call with <Hangup>
            resp.hangup()
            print(str(resp))
            return HttpResponse(resp)
        else:
            # If the caller didn't choose 1 or 2, apologize and ask them again
            resp.say("Sorry, I don't understand that choice.")
    else:
        # Get user input
        gather = Gather(num_digits=1, action='http://3.137.150.83:8001/voip/api_voip/voip_callback/' + session_id)
        gather.say('Please Press 1 to connect to destination. Press 2 to end the call.')
        resp.append(gather)

    # If the user didn't choose 1 or 2 (or anything), repeat the message
    resp.redirect('http://3.137.150.83:8001/voip/api_voip/voip_callback/' + session_id)

    print(str(resp))
    return HttpResponse(resp)


@csrf_exempt
def add_user_to_conf(request, session_id):
    # print(request.POST)
    print("# Add user request received, session id:{}", session_id)
    destination_number = sessionID_to_destNo.get(session_id)
    print("Attemtping to add phone number to call: " + destination_number)

    client = get_client()
    resp = VoiceResponse()

    dial = Dial()
    dial.conference(destination_number)
    resp.append(dial)

    participant = client.conferences(destination_number).participants.create(
        from_=settings.TWILIO['TWILIO_NUMBER'],
        to=destination_number,
        conference_status_callback='http://3.137.150.83:8001/voip/api_voip/leave_conf/' + session_id,
        conference_status_callback_event="leave")

    print(participant)
    return HttpResponse(str(resp))


@csrf_exempt
def leave_conf(request, session_id):
    # print(request.POST)
    event = request.POST.get('SequenceNumber')
    conference_sid = request.POST.get('ConferenceSid')

    sessionID_to_confsid[session_id] = conference_sid
    print("Leave call request:", conference_sid, event, session_id)

    if request.POST.get('StatusCallbackEvent') == 'participant-leave':
        print("A Participant Left Call")
        client = get_client()
        # ends conference call if only 1 participant left
        participants = client.conferences(conference_sid).participants
        if participants and len(participants.list()) == 1:
            client.conferences(conference_sid).update(status='completed')
            print("Call ended")
        # ends conference call if original caller leaves before callee picks up
        elif len(participants.list()) == 0 and event == '2':
            client.calls(sessionID_to_callsid.get(session_id)).update(status='completed')
        print("Call ended")

    return HttpResponse('')


@csrf_exempt
def complete_call(request, session_id):
    # print(request.POST)
    print("## Ending conference call, callee rejected call")
    global sessionID_to_confsid

    try:
        client = get_client()
        participants = client.conferences(sessionID_to_confsid.get(session_id)).participants
        print('participants:', participants)

        # only does so if 1 participant left in the conference call (i.e. the caller)
        if participants and len(participants.list()) == 1:
            client.conferences(sessionID_to_confsid.get(session_id)).update(status='completed')
    finally:
        print("Call ended")

    return HttpResponse('')



@csrf_exempt
def join_conference(request):
    # XXX first call this which creates an inbound call to source_number
    # print(request)
    source_number =  request.POST.get("source_number")
    dest_number = request.POST.get("dest_number")
    print("Call Request received! source_number:{0}, dest_number:{1}".format(source_number, dest_number))

    if not source_number or not dest_number:
        msg = "Missing phone number value. Expected params source_number and dest_number"
        return JsonResponse({'error': msg})


    try:
        twilio_client = get_client()
        session_id = get_session_id(source_number, dest_number)

        call = twilio_client.calls.create(record=True,
                                          from_=settings.TWILIO['TWILIO_NUMBER'],
                                          to='+' + source_number,
                                          url='http://3.137.150.83:8001/voip/api_voip/voip_callback/' + str(session_id),
                                          status_callback_event=['completed'],
                                          status_callback='http://3.137.150.83:8001/voip/api_voip/complete_call/' + str(session_id)
                                          )
        sessionID_to_callsid[session_id] = call.sid
        sessionID_to_destNo[session_id] = '+' + dest_number
        print("Initiated a Source number Call, session_id:", session_id)
    except Exception as e:
        message = e.msg if hasattr(e, 'msg') else str(e)
        return JsonResponse({'error': message})
    return JsonResponse({'message': 'Success!'})

