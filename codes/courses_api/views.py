from pickletools import int4
from django.db.models import OuterRef, Subquery
from django.core.files import File
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import Http404, HttpResponseBadRequest
from django.http import JsonResponse
from .serializers import LessonSerializer
from .serializers import FlashCardSerializer,LessonEmailNotifySerializer
from .serializers import UserSessionEventSerializer,UserSessionSerializer
from .serializers import FlashcardResponseSerializer,StudentLessonSerializer,StudentLessonProgressSerializer
from .models import Lesson
from lesson_notifications.models import LessonEmailNotify
from .models import FlashCard
from .models import UserSessionEvent
from .models import FlashCardResponse
from store.models import BrainTreeConfig, item, StripeProductPrice as StripeItem
from .models import FlashCard
from .models import UserSession
from .models import Invite
from .models import InviteResponse
import json
import uuid
import datetime
from datetime import time
from sfapp2.utils.twilio import send_confirmation_code, send_sms
from form_lead.utils.email_util import send_raw_email
from classroom.models import Student, Class, ClassEnrolled
from django.contrib.auth.models import User
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from knox.auth import get_user_model, AuthToken
from .models import MemberSession, MemberGpsEntry
from knox.views import user_logged_in
from knox.serializers import UserSerializer
from django.template.loader import render_to_string
from sfapp.views import get_member_from_headers
import qrcode
from io import BytesIO
import base64
from math import sin, cos, sqrt, atan2, radians
from django.template.loader import render_to_string
from .utils.email_util import send_email, send_email_code
# from codes.vconf.views import upload_to_s3, uuid_file_path
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

@api_view(['GET'])
def apiOverview(request):
    return Response("Hey There")

# Lesson API Start

@api_view(['POST'])
def lesson_create(request):
    les_ = Lesson()
    les_.lesson_name = request.data["lesson_name"]
    les_.meta_attributes = request.data["meta_attributes"]
    les_.user = request.user
    les_.lesson_is_public = request.data["lesson_is_public"]
    les_.save()
    for flashcard in request.data["flashcards"]:
        question=""
        options=[]
        answer=""
        image=""
        braintree_merchant_ID=""
        braintree_public_key=""
        braintree_private_key=""
        braintree_item_name=""
        braintree_item_price=""
        stripe_product_price=0

        lesson_type = flashcard["lesson_type"]
        position =flashcard["position"]

        if "question" in flashcard:
            question = flashcard["question"]

        if "options" in flashcard:
            if not isinstance(flashcard["options"],list):
                return HttpResponseBadRequest(content='options must be a list')
            options = flashcard["options"]

        if "answer" in flashcard:
            answer = flashcard["answer"]

        if "image" in flashcard:
            image = flashcard["image"]

        if "braintree_merchant_ID" in flashcard:
            braintree_merchant_ID = flashcard["braintree_merchant_ID"]

        if "braintree_public_key" in flashcard:
            braintree_public_key = flashcard["braintree_public_key"]

        if "braintree_private_key" in flashcard:
            braintree_private_key = flashcard["braintree_private_key"]

        if "braintree_item_name" in flashcard:
            braintree_item_name = flashcard["braintree_item_name"]

        if "braintree_item_price" in flashcard:
            braintree_item_price = flashcard["braintree_item_price"]

        lesson = les_
        if(braintree_item_name != '' and braintree_item_price != ''):
            item_obj = item(
                        title=braintree_item_name,
                        price=int(braintree_item_price)
                        )
            item_obj.save()
        if(braintree_merchant_ID != '' and braintree_public_key != '' and braintree_private_key != ''):
            BrainTreeConfig_obj = BrainTreeConfig(
                        braintree_merchant_ID=braintree_merchant_ID,
                        braintree_public_key=braintree_public_key,
                        braintree_private_key=braintree_private_key,
                        )
            BrainTreeConfig_obj.save()

        if 'stripe_product_price' in flashcard:
            stripe_product_price = flashcard['stripe_product_price']

        stripe_recurring_price = False;
        if 'stripe_recurring_price' in flashcard:
            print('stripe_recurring_price--setting')
            stripe_recurring_price = flashcard['stripe_recurring_price']

        if(braintree_item_name != '' and braintree_item_price != '' and braintree_merchant_ID != '' 
            and braintree_public_key != '' and braintree_private_key != ''):
            f=FlashCard(lesson=lesson,
                        lesson_type=lesson_type,
                        question=question,
                        options=options,
                        answer=answer,
                        image=image,
                        position=position,
                        braintree_config=BrainTreeConfig.objects.get(id=BrainTreeConfig_obj.id),
                        item_store=item.objects.get(id=item_obj.id),
                        is_required=flashcard.get('is_required'),
                        )
            f.save()
        elif stripe_product_price != 0:
            p = stripe.Product.create(name=f'product__{stripe_product_price}__{uuid.uuid4()}')
            if not stripe_recurring_price:
                print('no_recurring_price')
                price = stripe.Price.create(
                    unit_amount=int(stripe_product_price)*100,
                    currency='usd',
                    product=p.id,
                )
            else: 
                print('creating_recurring_price')
                price = stripe.Price.create(
                    unit_amount=int(stripe_product_price)*100,
                    currency='usd',
                    product=p.id,
                    recurring={
                        'interval': 'month',
                    },
                )
            stripe_item = StripeItem()
            stripe_item.stripe_price_id = price.id
            stripe_item.stripe_product_id = p.id
            stripe_item.stripe_recurring_price = stripe_recurring_price
            stripe_item.price = stripe_product_price
            stripe_item.save()

            f = FlashCard(
                lesson=lesson,
                lesson_type=lesson_type,
                question=question,
                options=options,
                answer=answer,
                image=image,
                position=position,
                stripe_item=stripe_item,
                is_required=flashcard.get('is_required', False)
                )
            f.save()
        else:
            f=FlashCard(lesson=lesson,
                        lesson_type=lesson_type,
                        question=question,
                        options=options,
                        answer=answer,
                        image=image,
                        position=position,
                        is_required=flashcard.get('is_required'),
                        )
            f.save()
    return Response(LessonSerializer(les_).data)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def lesson_read(request, pk):
    data = {}
    try:
        user = request.user
        les_= Lesson.objects.get(user=user, id=pk)
        if not les_:
            return JsonResponse({'message': 'Unauthorized'})
        less_serialized = LessonSerializer(les_)
        data = less_serialized.data
        for card in data["flashcards"]:
            if (card['lesson_type'] == "braintree_Config"):
                if card['braintree_config']:
                    obj_braintree_config = BrainTreeConfig.objects.get(
                        id=card['braintree_config'])
                    card['braintree_merchant_ID'] = obj_braintree_config.braintree_merchant_ID
                    card['braintree_public_key'] = obj_braintree_config.braintree_public_key
                    card['braintree_private_key'] = obj_braintree_config.braintree_private_key

                if card['item_store']:
                    obj_item = item.objects.get(id=card['item_store'])
                    card['braintree_item_name'] = obj_item.title
                    card['braintree_item_price'] = obj_item.price
        return Response(data)
    except:
        les_= Lesson.objects.get(id=pk)
        less_serialized = LessonSerializer(les_)
        data = less_serialized.data
        if data['lesson_is_public'] == True:
            for card in data["flashcards"]:
                if (card['lesson_type'] == "braintree_Config"):
                    if card['braintree_config']:
                        obj_braintree_config = BrainTreeConfig.objects.get(id=card['braintree_config'])
                        card['braintree_merchant_ID'] = obj_braintree_config.braintree_merchant_ID
                        card['braintree_public_key'] = obj_braintree_config.braintree_public_key
                        card['braintree_private_key'] = obj_braintree_config.braintree_private_key

                    if card['item_store']:
                        obj_item = item.objects.get(id=card['item_store'])
                        card['braintree_item_name'] = obj_item.title
                        card['braintree_item_price'] = obj_item.price
            return Response(data)
        else:
            return Response({'msg':"you do not has access to view this lesson"},status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_to_class(request):
    class_id = request.POST.get('class_id')
    lesson_id = request.POST.get('lesson_id')
    if class_id and class_id.isnumeric() and lesson_id and lesson_id.isnumeric():
        valid_cls = Class.objects.filter(user=request.user, id=class_id).first()
        if valid_cls:
            valid_less = Lesson.objects.filter(id=lesson_id, user=request.user)
            if valid_less:
                valid_less.update(_class=valid_cls)
                return JsonResponse({'msg': 'Lesson updated Successfully', 'status':True})
            else:
                return JsonResponse({'msg': 'Lesson not found'}, status=400)
        else:
            return JsonResponse({'msg': 'Class not found'}, status=400)
    else:
        return JsonResponse({'msg': 'invalid Parameters'}, status=400)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def lessons_in_class(request):
    class_id = request.GET.get('class_id')
    if class_id and class_id is not None and class_id.isnumeric():
        lessonsResponse = []
        # lessons = LessonSerializer(Lesson.objects.filter(_class=class_id), many=True)
        lessons = Lesson.objects.filter(_class=class_id)
        FCTYPES = ['datepicker', 'user_gps', 'name_type', 'signature', 'title_textarea',
                   'title_input','user_image_upload','question_choices', 'user_video_upload','question_checkboxes']
        for lessn in lessons:
            singleLesson = {}
            singleLesson['name'] = lessn.lesson_name
            singleLesson['id'] = lessn.id
            singleLesson['isPublic'] = lessn.lesson_is_public
            singleLesson['fc_count'] = FlashCard.objects.filter(lesson=lessn, lesson_type__in=FCTYPES).count()
            # student__email=request.user.email
            # add this filter
            singleLesson['classInfo'] = {'id':lessn._class.id, 'class_name': lessn._class.class_name}
            singleLesson['fcr_count'] = FlashCardResponse.objects.filter(lesson=lessn).distinct('flashcard__id').count()#.prefetch_related('flashcard').values('flashcard')
            if singleLesson['fcr_count'] == singleLesson['fc_count']:
                singleLesson['percent_completed'] = 100
            else:
                singleLesson['percent_completed'] = "{0:.2f}".format((singleLesson['fcr_count']/(singleLesson['fc_count'] if singleLesson['fc_count'] > 0 else 1))*100)
            lessonsResponse.append(singleLesson)
        return JsonResponse(lessonsResponse, safe=False)
    classes = ClassEnrolled.objects.filter(student__in=Student.objects.filter(email=request.user.email)).values('class_enrolled')
    # lessons = LessonSerializer(Lesson.objects.filter(_class__in=classes).all(), many=True)
    lessons = Lesson.objects.filter(_class__in=classes).select_related('_class').all()
    FCTYPES = ['datepicker','user_gps','name_type','signature','title_textarea','title_input','user_image_upload','question_choices', 'user_video_upload','question_checkboxes']
    lessonsResponse = []
    for lessn in lessons:
        singleLesson = {}
        singleLesson['name'] = lessn.lesson_name
        singleLesson['id'] = lessn.id
        singleLesson['isPublic'] = lessn.lesson_is_public
        singleLesson['fc_count'] = FlashCard.objects.filter(lesson=lessn, lesson_type__in=FCTYPES).count()
        # student__email=request.user.email
        # add this filter
        singleLesson['classInfo'] = {'id':lessn._class.id, 'class_name': lessn._class.class_name}
        singleLesson['fcr_count'] = FlashCardResponse.objects.filter(lesson=lessn).distinct('flashcard__id').count()#.prefetch_related('flashcard').values('flashcard')
        if singleLesson['fcr_count'] == singleLesson['fc_count']:
            singleLesson['percent_completed'] = 100
        else:
            singleLesson['percent_completed'] = (singleLesson['fcr_count']/(singleLesson['fc_count'] if singleLesson['fc_count'] > 0 else 1))*100
        lessonsResponse.append(singleLesson)
    return JsonResponse(lessonsResponse, safe=False)
    # return JsonResponse(lessons.data,safe=False)


@api_view(['GET','POST','PUT','DELETE'])
@csrf_exempt
def lesson_all(request):
    print("HERELERERER %s" % request.user)
    if request.method == 'GET':
            # les_= Lesson.objects.filter(user=token.user_id)
            # less_serialized = LessonSerializer(les_,many=True)
        if not request.user:
            return JsonResponse({"message":"Unauthorized"})

        less_serialized = LessonSerializer(
            Lesson.objects.filter(user=request.user), many=True)
        return JsonResponse(less_serialized.data, safe=False)
    if request.method == 'PUT':
        try:
            lesson = Lesson.objects.get(id=request.data.get('lesson_id'))
            lesson.lesson_name = request.data.get('lesson_name')
            lesson.save()
            return JsonResponse({"success":True},status=status.HTTP_202_ACCEPTED)

        except:
            return JsonResponse({"success":False},status=status.HTTP_204_NO_CONTENT)

    if request.method == 'DELETE':
        try:
            # XXX NEED to check if person owns lesson in order to delete it.
            lesson = Lesson.objects.get(id=request.GET['lesson_id'])
            lesson.delete()
            return JsonResponse({"success":True},status=status.HTTP_200_OK)

        except:
            return JsonResponse({"success":False},
                                status=status.HTTP_204_NO_CONTENT)

from termcolor import cprint

@api_view(['POST'])
def lesson_update(request, pk):
    try:
        user = request.user
        lesson = Lesson.objects.get(user=user, id=pk)
        lesson_name = request.data['lesson_name']
        lesson_is_public = request.data['lesson_is_public']
        meta_attributes = request.data['meta_attributes']
        Lesson.objects.filter(user=user, id=pk).update(lesson_name=lesson_name)
        Lesson.objects.filter(user=user, id=pk).update(meta_attributes=meta_attributes)
        Lesson.objects.filter(user=user, id=pk).update(lesson_is_public=lesson_is_public)
        for fc in FlashCard.objects.filter(lesson=lesson):
            toDelete = True
            for flashcard in request.data["flashcards"]:
                if "id" in flashcard:
                    if fc.id == flashcard["id"]:
                        toDelete = False
                        break
                    else:
                        toDelete=True
                        continue
            if toDelete:
                fc.delete()
        for flashcard in request.data["flashcards"]:
            question=""
            options=[]
            answer=""
            image=""
            braintree_merchant_ID=""
            braintree_public_key=""
            braintree_private_key=""
            braintree_item_name=""
            braintree_item_price=""
            position =flashcard["position"]
            stripe_product_price=0
            stripe_recurring_price = False
            id_ = None
            if "id" in flashcard:
                id_ = flashcard["id"]

            if "question" in flashcard:
                question = flashcard["question"]

            if "options" in flashcard:
                if not isinstance(flashcard["options"], list):
                    return HttpResponseBadRequest(content='Flashcard options must be a list')
                options = flashcard["options"]

            if "answer" in flashcard:
                answer = flashcard["answer"]

            if "image" in flashcard:
                image = flashcard["image"]

            if "braintree_merchant_ID" in flashcard:
                braintree_merchant_ID = flashcard["braintree_merchant_ID"]

            if "braintree_public_key" in flashcard:
                braintree_public_key = flashcard["braintree_public_key"]

            if "braintree_private_key" in flashcard:
                braintree_private_key = flashcard["braintree_private_key"]

            if "braintree_item_name" in flashcard:
                braintree_item_name = flashcard["braintree_item_name"]

            if "braintree_item_price" in flashcard:
                braintree_item_price = flashcard["braintree_item_price"]

            if 'stripe_product_price' in flashcard:
                stripe_product_price = flashcard['stripe_product_price']

            if 'stripe_recurring_price' in flashcard:
                stripe_recurring_price = flashcard['stripe_recurring_price']

            if "id" in flashcard:
                if(braintree_item_name != '' or braintree_item_price != ''):
                    obj_item = FlashCard.objects.get(id=id_)
                    item_obj = item.objects.filter(id=obj_item.item_store).update(
                                title=braintree_item_name,
                                price=braintree_item_price
                                ) 
                    # item_obj.save()
                if(braintree_merchant_ID != '' or braintree_public_key != '' or braintree_private_key != ''):
                    obj_config = FlashCard.objects.get(id=id_)
                    BrainTreeConfig_obj = BrainTreeConfig.objects.filter(id=obj_config.braintree_config).update(
                                braintree_merchant_ID=braintree_merchant_ID,
                                braintree_public_key=braintree_public_key,
                                braintree_private_key=braintree_private_key,
                                )
                    # BrainTreeConfig_obj.save()

                if(stripe_product_price != 0):
                    print('stripe_product_price', stripe_product_price)
                    obj_item = flashcard.objects.filter(id=id).first()
                    p = stripe.Product.create(name=f'product__{stripe_product_price}__{uuid.uuid4()}')
                    price = stripe.Price.create(
                        unit_amount=int(stripe_product_price)*100,
                        currency='usd',
                        product=p.id,
                    )
                    stripe_item = obj_item.stripe_item
                    stripe_item.stripe_price_id = price.id
                    stripe_item.stripe_product_id = p.id
                    stripe_item.price = stripe_product_price
                    stripe_item.save()
                    
                f=FlashCard.objects.filter(id=id_).update(question=question,options=options,answer=answer,
                                                        image=image,position=position)
                
            else:
                lesson_type = flashcard["lesson_type"]
                if(braintree_item_name != '' and braintree_item_price != ''):
                    item_obj = item(
                                title=braintree_item_name,
                                price=braintree_item_price
                                ) 
                    item_obj.save()
                if(braintree_merchant_ID != '' and braintree_public_key != '' and braintree_private_key != ''):
                    BrainTreeConfig_obj = BrainTreeConfig(
                                braintree_merchant_ID=braintree_merchant_ID,
                                braintree_public_key=braintree_public_key,
                                braintree_private_key=braintree_private_key,
                                )
                    BrainTreeConfig_obj.save()
                
                if(braintree_item_name != '' and braintree_item_price != '' and braintree_merchant_ID != '' 
                    and braintree_public_key != '' and braintree_private_key != ''):
                    f=FlashCard(lesson=lesson,
                                lesson_type=lesson_type,
                                question=question,
                                options=options,
                                answer=answer,
                                image=image,
                                position=position,
                                braintree_config=BrainTreeConfig.objects.get(id=BrainTreeConfig_obj.id),
                                item_store=item.objects.get(id=item_obj.id),
                                is_required=flashcard.get('is_required'),
                                )
                    f.save()
                elif stripe_product_price:
                    lesson_type = flashcard["lesson_type"]
                    p = stripe.Product.create(name=f'product__{stripe_product_price}__{uuid.uuid4()}')
                    if(stripe_recurring_price):
                        price = stripe.Price.create(
                            unit_amount=int(stripe_product_price)*100,
                            currency='usd',
                            product=p.id,
                            recurring={
                                'interval': 'month',
                            },
                        )
                    else:
                        price = stripe.Price.create(
                            unit_amount=int(stripe_product_price)*100,
                            currency='usd',
                            product=p.id,
                        )
                    stripe_item = StripeItem()
                    stripe_item.stripe_price_id = price.id
                    stripe_item.stripe_product_id = p.id
                    stripe_item.price = stripe_product_price
                    stripe_item.stripe_recurring_price = stripe_recurring_price
                    stripe_item.save()

                    f = FlashCard(
                        lesson=lesson, 
                        lesson_type=lesson_type,
                        question=question,
                        options=options,
                        answer=answer,
                        image=image,
                        position=position,
                        stripe_item=stripe_item,
                        is_required=flashcard.get('is_required', False)
                        )
                    f.save()
                else:
                    f=FlashCard(lesson=lesson,
                                lesson_type=lesson_type,
                                question=question,
                                options=options,
                                answer=answer,
                                image=image,
                                position=position,
                                is_required=flashcard.get('is_required'),
                                )
                    f.save()
        return Response(LessonSerializer(lesson).data)
    except Exception as e:
        print("🚀 ~ file: views.py ~ line 374 ~ e", e)
        return Response({"msg":"you cannot update this lesson"},status=status.HTTP_401_UNAUTHORIZED)

@api_view(['DELETE'])
def lesson_delete(request, pk):
    try:
        user = request.user
        lesson = Lesson.objects.filter(user=user,id=pk)
        lesson.delete()
        return Response("deleted")
    except:
        return Response({"msg":"you cannot update this lesson"},status=status.HTTP_401_UNAUTHORIZED)
#Slide Api Start

@api_view(["GET"])
def slide_read(request, pk):
    les_= Lesson.objects.get(id=pk)
    less_serialized = LessonSerializer(les_)
    data = less_serialized.data
    for card in data["flashcards"]:
        if (card['lesson_type'] == "braintree_Config"):
            if card['braintree_config']:
                obj_braintree_config = BrainTreeConfig.objects.get(id=card['braintree_config'])
                card['braintree_merchant_ID'] = obj_braintree_config.braintree_merchant_ID
                card['braintree_public_key'] = obj_braintree_config.braintree_public_key
                card['braintree_private_key'] = obj_braintree_config.braintree_private_key

            if card['item_store']:
                obj_item = item.objects.get(id=card['item_store'])
                card['braintree_item_name'] = obj_item.title
                card['braintree_item_price'] = obj_item.price
                card['braintree_item_id'] = obj_item.id
    return Response(data)
   

# Flashcard API Start

@api_view(['POST'])
def flashcard_create(request,lessonId):
    question=""
    options=[]
    answer=""
    image=""
    lesson_type = request.data["lesson_type"]
    position =request.data["position"]
    if "question" in request.data:
        question = request.data["question"]

    if "options" in request.data:
        if not isinstance(request.data["options"], list):
            return HttpResponseBadRequest(content='options must be a list')
        options = request.data["options"]

    if "answer" in request.data:
        answer = request.data["answer"]

    if "image" in request.data:
        image = request.data["image"]
    lesson = Lesson.objects.filter(id=lessonId).get()

    f=FlashCard(lesson=lesson,lesson_type=lesson_type,question=question,options=options,answer=answer,
                                image=image,position=position)
    f.save()
    return Response("FlashCard Created!")

@api_view(['GET'])
def flashcard_read(request,pk):
    usersessionevent = {}
    fc= FlashCard.objects.get(id=pk)
    fc_serialized = FlashCardSerializer(fc)
    return Response(fc_serialized.data)

@api_view(['POST'])
def flashcard_update(request,pk):
    f = FlashCard.objects.filter(id=pk).get()
    question=f.question
    options=f.options
    answer=f.answer
    image=f.image
    position=f.position
   
    if "question" in request.data:
        question = request.data["question"]

    if "options" in request.data:
        if not isinstance(request.data["options"],list):
            return HttpResponseBadRequest(content='options must be a list')
        options = request.data["options"]

    if "answer" in request.data:
        answer = request.data["answer"]

    if "image" in request.data:
        image = request.data["image"]
    
    if "position" in request.data:
        position = request.data["position"]

    FlashCard.objects.filter(id=pk).update(question=question,options=options,answer=answer,image=image,position=position)
    return Response("updated")

@api_view(['DELETE'])
def flashcard_delete(request, pk):
    FlashCard.objects.filter(id=pk).delete()
    return Response("deleted")


@api_view(['POST'])
def session_create(request, flashcardId):
    ip_address = ""
    user_device = ""
    if "ip_address" in request.data:
        ip_address = request.data['ip_address']
    if "user_device" in request.data:
        user_device = request.data['user_device']
    flashcard = FlashCard.objects.filter(id=flashcardId).get()
    use=UserSessionEvent(ip_address=ip_address, user_device=user_device, \
        flash_card=flashcard)
    use.save()
    return Response("Session user add")


@api_view(['GET'])
def session_list(request):
    ses = UserSessionEvent.objects.all()
    serializer = UserSessionEventSerializer(ses, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
def session_update(request, flashcardId, pk):
    flashcard = FlashCard.objects.filter(id=flashcardId).get()
    sess = UserSessionEvent.objects.filter(flash_card=flashcardId).get(id=pk)
    start = sess.start_time
    cur_s = start.strftime('%s')
    now = datetime.datetime.now()
    cur_n = now.strftime('%s')
    durate = int(cur_n) - int(cur_s)
    UserSessionEvent.objects.filter(id=pk).update(end_time=now, view_duration=durate)
    return Response("Move slide")


@api_view(['POST'])
def flashcard_response(request):
    flashcard_id = request.data['flashcard']
    session_id = request.data['session_id']
    answer = request.data['answer']
    params = request.data.get('params',None)
    if 'latitude' in request.data:
        latitude = request.data['latitude']
    else:
        latitude = 0
    if 'longitude' in request.data:
        longitude = request.data['longitude']
    else:
        longitude = 0
    student = ''
    if params:
        student = Student.objects.get(id=Invite.objects.get(params=params).student_id)
    flashcard = FlashCard.objects.get(id=flashcard_id)

    user_session = UserSession.objects.get(session_id=session_id)
    print("%s %s %s" % (user_session, flashcard, answer))

    # first check if we have FlashCardResponse
    flashcard_response = FlashCardResponse.objects.filter(
        user_session=user_session,
        lesson=flashcard.lesson,
        flashcard=flashcard).first()

    if flashcard_response:
        # update answer...
        flashcard_response.answer = answer
    else:
        if student:
            flashcard_response = FlashCardResponse(
                user_session=user_session,
                lesson=flashcard.lesson,
                flashcard=flashcard,
                answer=answer,
                student= student,
                latitude=latitude,
                longitude=longitude)
        else:
            flashcard_response = FlashCardResponse(
                user_session=user_session,
                lesson=flashcard.lesson,
                flashcard=flashcard,
                answer=answer,
                latitude=latitude,
                longitude=longitude)
    flashcard_response.save()
    return Response("Response Recorded",status=200)

@api_view(['GET'])
def lesson_flashcard_responses(request,lesson_id,session_id):
    user_session = UserSession.objects.get(session_id=session_id)
    lesson = Lesson.objects.get(id=lesson_id)
    flashcard_responses = FlashCardResponse.objects.filter(
        user_session=user_session,lesson=lesson)
    return Response(FlashcardResponseSerializer(flashcard_responses,many=True).data)

@api_view(['GET'])
def overall_flashcard_responses(request,lesson_id):
    try:
        flash_obj = FlashCardResponse.objects.filter(lesson=lesson_id)
        data = FlashcardResponseSerializer(flash_obj,many=True)
        return Response(data.data)
    except Exception as e:
        return Response("error")


@api_view(['GET'])
def overall_flashcard_response_results(request, lesson_id):

    flash_cards = FlashCard.objects.filter(lesson=lesson_id).order_by('position').values()

    user_sessions = FlashCardResponse.objects.filter(lesson=lesson_id).order_by().values('user_session').distinct()

    user_responses = []
    for user_session in user_sessions:
        flash_card_responses = []
        for flashcard in flash_cards:

            if flashcard['lesson_type'] in ['question_choices', 'question_checkboxes',
                                            'title_input', 'signature', 'email_verify', 
                                            'verify_phone', 'datepicker']:
                
                flash_card_response = FlashCardResponse.objects.filter(
                    user_session=user_session['user_session'],
                    lesson=flashcard['lesson_id'],
                    flashcard=flashcard['id']
                ).values('flashcard_id', 'answer')
                
                flash_card_responses.append(list(flash_card_response))
                
        user_responses.append(flash_card_responses)

    return JsonResponse({
        'flash_cards': list(flash_cards),
        'user_responses': list(user_responses),
    })


@api_view(['GET'])
def email_responses(request,lessonId):
    try:
        notify = LessonEmailNotify.objects.get(lesson=lessonId)
        print("🚀 ~ file: views.py ~ line 551 ~ notify", notify)
        flash_obj = FlashCardResponse.objects.filter(lesson=notify.lesson.id)
        print("🚀 ~ file: views.py ~ line 553 ~ flash_obj", flash_obj)
        
        subject = f'User Response'
        body = ''
        html_message = render_to_string(
            'email.html', {"data": flash_obj})

        send_raw_email(to_email=[notify.email],reply_to=None,
                            subject=subject,
                            message_text=body,
                            message_html=html_message)
        return Response({"sucess":True},status=200)
    except Exception as e:
        print("🚀 ~ file: views.py ~ line 568 ~ e", e)
        return Response("error")


@api_view(['GET'])
def user_responses(request,lesson_id):
    try:
        flash_obj = FlashCardResponse.objects.filter(lesson=lesson_id)
        serializer = FlashcardResponseSerializer(flash_obj,many=True)
        return Response(serializer.data)
    except:
        return Response("error")

@api_view(['POST'])
def lesson_email_notify(request,lessonId):
    try:
        lesson = Lesson.objects.get(id=lessonId)
        print("🚀 ~ file: views.py ~ line 584 ~ lesson", lesson)
        email = request.POST.get('email')
        print("🚀 ~ file: views.py ~ line 586 ~ email", email)
        data = LessonEmailNotify(lesson_notify=lesson,email=email)
        data.save()
        return Response("Email Recorded",status=201)
    except Exception as e:
        print("🚀 ~ file: views.py ~ line 591 ~ e", e)
        return Response("error")

@api_view(['DELETE'])
def lesson_email_notify_delete(request,lessonId):
    try:
        LessonEmailNotify.objects.filter(lesson=lessonId).delete()
        return Response("deleted",status=200)
    except:
        return Response("error")

@api_view(['GET'])
def logged_user(request):
    print("reuest token")


@api_view(['GET'])
def get_user_session(request):
    user_session = UserSession()
    user_session.session_id = str(uuid.uuid4())
    user_session.save()

    return Response({'message': 'success',
    'session_id': user_session.session_id})


@api_view(['POST'])
def user_session_event(request,flashcard_id,session_id):
    created_at = UserSession.objects.get(session_id=session_id).created_at
    session_event_oject = UserSessionEvent(
                            flash_card = FlashCard.objects.get(pk=flashcard_id),
                            user_session = UserSession.objects.get(session_id=session_id),
                            ip_address = request.data['ip_address'],
                            user_device = request.data['user_device'],
                            create_at = created_at,
                            )
    session_event_oject.save()
    return Response({'message': 'success'})


@api_view(['POST'])
def confirm_phone_number(request):
    phone_number = request.data['phone_number']
    session_id = request.data['session_id']

    if not phone_number:
        raise HttpResponseBadRequest()
    if not session_id:
        raise HttpResponseBadRequest()

    session = UserSession.objects.filter(session_id=session_id)
    code_2fa = send_confirmation_code(phone_number)

    session.update(phone=phone_number, code_2fa=code_2fa)
    
    return Response({'message': 'pending 2fa'})

@api_view(['POST'])
def verify_2fa(request):
    code = request.data['code_2fa']
    session_id = request.data['session_id']
    phone = request.data['phone_number']
    member = UserSession.objects.filter(session_id=session_id).first()
    if phone == member.phone and code == member.code_2fa:
        member.has_verified_phone=True
        member.save()
        return Response({'message': 'success'})
    return Response({'message': 'error'},status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def confirm_email_address(request):
    email = request.data['email_address']
    session_id = request.data['session_id']

    if not email:
        raise HttpResponseBadRequest()
    if not session_id:
        raise HttpResponseBadRequest()

    session = UserSession.objects.filter(session_id=session_id)
    code_2fa = send_email_code()
    send_email(email)

    session.update(email=email, code_2fa=code_2fa)
    
    return Response({'message': 'pending 2fa'})

@api_view(['POST'])
def verify_email_2fa(request):
    code = request.data['code_2fa']
    session_id = request.data['session_id']
    member = UserSession.objects.filter(session_id=session_id).first()
    
    if session_id == member.session_id and code == member.code_2fa:
        member.has_verified_email=True
        member.save()
        return Response({'message': 'success'})
    
    return Response({'message': 'error'},status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def Phone_verification_check(request):
    session_id = request.data['session_id']
    member = UserSession.objects.filter(session_id=session_id)[0]
    if member.has_verified_phone:
        return Response({'message': 'success'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'error'},status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_2fa_code(request):
    if request.GET:
        phone_number = request.GET.get('phone_number')
        if not phone_number:
            return JsonResponse({'message': 'Phone number is required'})
        
        member = UserSession.objects.filter(phone=phone_number).first()
        if not member:
            return JsonResponse({"error":"Invalid Number"})
        if(member.code_2fa):
            return JsonResponse({'2fa-code':member.code_2fa})
        else:
            return JsonResponse({'error':"Phone number is does not have code sent."})


@api_view(['GET'])
def student_lesson_list(request,student_id):
    try:
        stulist = Invite.objects.filter(student=student_id)
        serializer = StudentLessonSerializer(stulist,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'error'},status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def invite_email(request):
    invite_type = 'email'
    body = request.data.get('body')
    lesson = Lesson.objects.get(id=request.data.get('lesson'))
    subject = f"Invitation to {lesson.lesson_name} (Lesson)"
    if request.data.get('student'):
        student = Student.objects.get(id=request.data.get('student'))
        unique_id = ''
        params = str(uuid.uuid4())

        invited = Invite.objects.filter(lesson_id =request.data.get('lesson'),student_id=request.data.get('student'),invite_type=invite_type)
        if invited:
            unique_id = invited.get().params
        else:
            invite = Invite(lesson=lesson,student=student,params=params,invite_type=invite_type)
            invite.save()
            unique_id = invite.params

        to_email = student.email
        send_raw_email(to_email=[to_email],reply_to=None,
                        subject=subject,
                        message_text=f"{body}&params={unique_id}",
                        message_html=None)

        return JsonResponse({"sucess":True},status=200)
    if request.data.get('class'):
        # emails = []
        _class = ClassEnrolled.objects.filter(class_enrolled_id=request.data.get('class'))
        if _class:
            for std in _class:
                # emails.append(std.student.email)
                student = Student.objects.get(id=std.student.id)
                unique_id = ''
                params = str(uuid.uuid4())

                invited = Invite.objects.filter(lesson_id =request.data.get('lesson'),student_id=std.student.id,invite_type=invite_type)
                if invited:
                    unique_id = invited.get().params
                else:
                    invite = Invite(lesson=lesson,student=student,params=params,invite_type=invite_type)
                    invite.save()
                    unique_id = invite.params

                send_raw_email(to_email=[std.student.email],reply_to=None,
                            subject=subject,
                            message_text=f"{body}&params={unique_id}",
                            message_html=None)
            return JsonResponse({"sucess":True},status=200)
        else:
            return JsonResponse({"sucess":False,"msg":f"Class {Class.objects.get(id=request.data.get('class')).class_name} doesn't have any enrolled student"},status=404)

@api_view(['POST'])
def invite_text(request):
    lesson = Lesson.objects.get(id=request.data.get('lesson'))
    subject = f"Invitation to {lesson.lesson_name} (Lesson)"
    invite_type = 'text'
    body = request.data.get('body')
    if request.data.get('student'):
        student = Student.objects.get(id=request.data.get('student'))
        unique_id = ''
        params = str(uuid.uuid4())

        invited = Invite.objects.filter(lesson_id =request.data.get('lesson'),student_id=request.data.get('student'),invite_type=invite_type)
        if invited:
            unique_id = invited.get().params
        else:
            invite = Invite(lesson=lesson,student=student,params=params,invite_type=invite_type)
            invite.save()
            unique_id = invite.params
        send_sms(to_number=student.phone,body=subject +"\n\n"+ f"{body}&params={unique_id}")
        return JsonResponse({"sucess":True},status=200)

    if request.data.get('class'):
        _class = ClassEnrolled.objects.filter(class_enrolled_id=request.data.get('class'))
        if _class:
            for std in _class:
                student = Student.objects.get(id=std.student.id)
                unique_id = ''
                params = str(uuid.uuid4())

                invited = Invite.objects.filter(lesson_id =request.data.get('lesson'),student_id=std.student.id,invite_type=invite_type)
                if invited:
                    unique_id = invited.get().params
                else:
                    invite = Invite(lesson=lesson,student=student,params=params,invite_type=invite_type)
                    invite.save()
                    unique_id = invite.params
                send_sms(to_number=std.student.phone,body=subject +"\n\n"+ f"{body}&params={unique_id}")
            return JsonResponse({"success":True},status=200)
        else:
            return JsonResponse({
                "success":False,"msg":f"Class {Class.objects.get(id=request.data.get('class')).class_name} doesn't have any enrolled student"},status=404)

    return JsonResponse({"success": True}, status=200)

@api_view(['POST'])
def invite_response(request):
    lesson_type = request.data['lesson_type']
    lesson_id = request.data['lesson_id']
    lesson = Lesson.objects.get(id = lesson_id)
    params = request.data['params']
    flashcard = FlashCard.objects.filter(lesson_type = lesson_type).first()
    answer = request.data['answer']
    student = Student.objects.get(
        id=Invite.objects.get(params=params).student_id)
    invite_response = InviteResponse(
        lesson=lesson,
        student=student,
        flashcard=flashcard,
        answer=answer,
    )

    invite_response.save()
    return Response("invite Response Recorded", status=200)

@api_view(['POST'])
def qr_code_response(request):

    URL = request.scheme + "://" + request.get_host() + "/courses_api/QRcodeData=" + request.data

    qr = qrcode.QRCode(version=10, box_size=10, border=5)
    qr.add_data(URL)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return Response(img_str, status=200)


@api_view(['GET'])
def qr_code_data(request, lesson_id):

    les_ = Lesson.objects.get(id=lesson_id)
    fashcards = FlashCard.objects.filter(lesson=les_)

    for fashcard in fashcards:
        if fashcard.lesson_type == "user_qr_data":
            dicti = fashcard.question
            dictionary = dict(subString.split(":")
                              for subString in dicti.split("\n"))
    return render(request, "QRcodeData.html", {'dictionary': dictionary})


def get_distance(lat1, lon1, lat2, lon2):
    R = 6373.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


@csrf_exempt
@api_view(['POST'])
def member_session_start(request):
    try:
        user = request.user
        session_create = MemberSession.objects.create(user=user)
        member_session_start.mge = MemberGpsEntry.objects.create(
            member_session=session_create,
            latitude=request.data.get("latitude", None),
            longitude=request.data.get("longitude", None))
        return JsonResponse({'status': 'okay'}, safe=False)
    except Exception as e:
        print("🚀 ~ file: views.py ~ line 929 ~ e", e)
        return JsonResponse({'status': 'error'}, safe=False)


@csrf_exempt
@api_view(['POST'])
def member_session_stop(request):
    try:
        user = request.user
        session_create = MemberSession.objects.filter(user=user).last()
        session_create.ended_at = datetime.datetime.now()
        session_create.save()
        mge = MemberGpsEntry.objects.create(
            member_session=session_create,
            latitude=request.data.get("latitude", None),
            longitude=request.data.get("longitude", None))

        distance = get_distance(member_session_start.mge.latitude,
                                member_session_start.mge.longitude,
                                mge.latitude, mge.longitude)
        total_time = (session_create.ended_at.replace(tzinfo=None) -
                      session_create.started_at.replace(tzinfo=None))
        avg_speed = (distance * 1000) / total_time.seconds

        data = {
            'distance': round(distance, 4),
            'avg_speed': round(avg_speed, 4),
            'total_time': total_time.seconds
        }
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'status': 'error'}, safe=False)


@api_view(['GET'])
def student_lesson_list_with_progress(request):
    try:
        invite = None
        if request.GET.get('params'):
            invite = Invite.objects.get(params=request.GET['params'])
        fc = FlashCard.objects.filter(lesson=OuterRef('lesson'))
        stulist = Invite.objects.filter(
            student_id=invite.student).distinct('lesson')
        serializer = StudentLessonProgressSerializer(stulist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'message': 'error'},
                        status=status.HTTP_404_NOT_FOUND)
