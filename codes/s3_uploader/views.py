from django.shortcuts import redirect, HttpResponseRedirect
import logging
import mimetypes
import os
import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ChangePasswordSerializer
from .serializers import UserSerializer, RegisterSerializer, RoomInfoSerializer, RoomVisitorsSerializer, RoomInfoVisitorsSerializer, RoomRecordingSerializer
from vconf.models import RoomInfo, RoomVisitors, RoomRecording, Brand, Visitor, Recording

@method_decorator(csrf_exempt, name='dispatch')
class Home(View):
    def get(self, request, *args, **kwargs):
        return render(request, "s3_uploader/upload.html")


@method_decorator(csrf_exempt, name='dispatch')
class RoomInfoView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "s3_uploader/upload_room_logo.html")

from rest_framework import mixins

class BrandInfo(generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Brand.objects.all()
    serializer_class = RoomInfoSerializer

    def get(self, request, pk, *args, **kwargs):
        try:
            room_info = Brand.objects.get(
                        room_name=pk)
            serializer = self.get_serializer(room_info)
            return Response(serializer.data)
        except Exception as ex:
            return Response({
                "error": str(ex)
            }, status=400)
    

import redis
@method_decorator(csrf_exempt, name='dispatch')
class ChannelList(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        channel_list = []
        redisconn = redis.StrictRedis(
            host='redis', port=6379, db=0, decode_responses=True)
        room_list = redisconn.smembers('room_names')
        room_list = list(room_list)
        for room in room_list:
            live_users = redisconn.hvals(room+'@live')
            room_dict = {'room_name': room.split("_")[1],
                        'members': len(live_users), 'live_users':live_users}
            channel_list.append(room_dict)
        return Response({'channel_list': sorted(channel_list, key = lambda i: i['members'],reverse=True)})

@method_decorator(csrf_exempt, name='dispatch')
class UploadRoomLogo(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = RoomInfoSerializer

    def upload_brand_video(self, brand_video):
        file_name = brand_video.name
        file_name_uuid = uuid_file_path(file_name)
        s3_key = 'Test/upload/{0}'.format(file_name_uuid)

        content_type, file_url = upload_to_s3(s3_key, brand_video)
        return file_url

    def post(self, request, *args, **kwargs):
        try:
            try:
                room_info = Brand.objects.get(
                    room_name=request.data['room_name'])
                return Response({"error": "Brand Already Exists!"}, status=400)
            except Brand.DoesNotExist:
                video_url = self.upload_brand_video(
                    request.FILES.get('video_url'))
            tempData = request.data.dict()
            tempData['video_url'] = video_url
            serializer = self.get_serializer(data=tempData)
            serializer.is_valid(raise_exception=True)
            room = serializer.save()
            return Response({
                "room": RoomInfoSerializer(room, context=self.get_serializer_context()).data
            })
        except Exception as ex:
            return Response({
                "error": str(ex)
            }, status=400)

class EditRoomLogo(APIView):

    def put(self,request,*args,**kwargs):
        try:
            room_ = Brand.objects.get(id=request.POST['room_id'])
            room_logo = request.FILES.get("room_logo", None)
            room_video = request.FILES.get("video_url", None)

            video_url = None
            room_logo_url = None
            upload = UploadRoomLogo()
            if room_video:
                video_url = upload.upload_brand_video(room_video)

            if room_logo:
                file_name = room_logo.name
                file_name_uuid = uuid_file_path(file_name)
                s3_key = 'Test/upload/{0}'.format(file_name_uuid)

                content_type, room_logo_url = upload_to_s3(s3_key, room_logo)
            room_.room_name = request.POST['room_name']
            room_.slack_channel = request.POST['slack_channel']

            if video_url:
                room_.video_url = video_url
            if room_logo_url:
                room_.logo_url = room_logo_url

            room_.save()
            return JsonResponse({"message":"Success!"},status=200)
        except:
            return JsonResponse({"message":"Error!"},status=404)

    def delete(self,request,*args,**kwargs):
        try:
            room_ = Brand.objects.get(id=request.POST['room_id'])
            room_.delete()
            return JsonResponse({"message":"Successfully Deleted!"}, status=200)
        except Brand.DoesNotExist:
            return JsonResponse({"message":"Error!"}, status=404)



class RoomVisitor(generics.ListCreateAPIView):
    queryset = Visitor.objects.select_related('room')
    serializer_class = RoomInfoVisitorsSerializer

    def get_serializer_class(self, *args, **kwargs):
        if(self.request.method == 'GET'):
            return RoomInfoVisitorsSerializer
        elif(self.request.method == 'POST'):
            return RoomVisitorsSerializer

    def post(self, request, *args, **kwargs):
        try:
            room_info = Brand.objects.filter(
                room_name=request.data['room_name'])
        except Brand.DoesNotExist:
            raise

        tempData = request.data.copy()
        tempData.__setitem__('room', room_info[0].id)
        serializer = self.get_serializer(data=tempData)
        serializer.is_valid(raise_exception=True)
        room_visitor = serializer.save()
        # print(room)
        return Response({
            "room_visitor": RoomVisitorsSerializer(room_visitor, context=self.get_serializer_context()).data
        })


class RecordingUpload(generics.GenericAPIView):
    queryset = Recording.objects.all()
    serializer_class = RoomRecordingSerializer

    def send_recording_url_to_slack(self, room, video_url):
        import requests
        import json
        # url = 'https://hooks.slack.com/services/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'
        url = room.slack_channel
        # send_message(text="Hi, I'm a test message.")
        slack_message = "Recording video url: " + video_url
        body = {"text": "%s" % slack_message,
                'username': room.room_name}
        requests.post(url, data=json.dumps(body))

    def post(self, request, *args, **kwargs):
        print("Uploading", request.FILES, request.POST)

        # TODO: Implement auth here
        member = 1
        if not member:
            return JsonResponse({'message': 'not logged in'})

        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        room_name = uploaded_file.name.split("_")
        try:
            room_info = Brand.objects.get(
                room_name=room_name[0])
        except Brand.DoesNotExist:
            raise

        if uploaded_file:
            # Get unique filename using UUID
            file_name = uploaded_file.name
            file_name_uuid = uuid_file_path(file_name)
            s3_key = 'Test/upload/{0}'.format(file_name_uuid)

            content_type, file_url = upload_to_s3(s3_key, uploaded_file)
            room_recording = {'recording_link': file_url, 'room': room_info.id}
            serializer = self.get_serializer(data=room_recording)
            serializer.is_valid(raise_exception=True)
            room = serializer.save()
            self.send_recording_url_to_slack(room_info, file_url)
            return Response({
                "room": RoomRecordingSerializer(room, context=self.get_serializer_context()).data
            })
            # print(f"Saving file to s3. member: {member}, s3_key: {s3_key}")

            # return JsonResponse({'message': 'Success!', 'file_url': file_url, 'content_type': content_type})
        else:
            return JsonResponse({'message': 'No file provided!'})


# Register User
class UserRegister(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def get(self, request, *args, **kwargs):
        return render(request, "s3_uploader/register.html")

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": AuthToken.objects.create(user)[1]
            })
        except:
            return Response({"msg":f"This email address is already registered with us"},status=status.HTTP_409_CONFLICT)

# Login User -> Returns a token to make requests
class UserLogin(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        data = request.data
        # Allow login using username/email both
        try:
            data['username'] = data['email']
        except:
            pass

        serializer = AuthTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(UserLogin, self).post(request, format=None)


# Password reset
class PasswordReset(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# '''
# S3 Upload end-points
# '''

class S3SignedUrl(generics.GenericAPIView):
    serializer_class = None
    def get_serializer_class(self, request, *args, **kwargs):
        if(self.request.method == 'POST'):
            # os.environ['S3_USE_SIGV4'] = 'True'

            # TODO: Implement auth here
            member = 1
            if not member:
                return JsonResponse({'message': 'not logged in'})

            # Get form fields
            seconds_per_day = 24 * 60 * 60

            # Get unique filename using UUID
            file_name = request.POST.get('file_name')
            file_name_uuid = uuid_file_path(file_name)
            final_file_name = 'uploads/{0}'.format(file_name_uuid)

            # Get pre-signed post url and fields
            resp = get_presigned_s3_url(
                object_name=final_file_name, expiration=seconds_per_day)

            # del os.environ['S3_USE_SIGV4']

            print(resp)
            return JsonResponse(resp)
    # def post(self, request, *args, **kwargs):
        # # os.environ['S3_USE_SIGV4'] = 'True'

        # # TODO: Implement auth here
        # member = 1
        # if not member:
        #     return JsonResponse({'message': 'not logged in'})

        # # Get form fields
        # seconds_per_day = 24 * 60 * 60

        # # Get unique filename using UUID
        # file_name = request.POST.get('file_name')
        # file_name_uuid = uuid_file_path(file_name)
        # final_file_name = 'uploads/{0}'.format(file_name_uuid)

        # # Get pre-signed post url and fields
        # resp = get_presigned_s3_url(
        #     object_name=final_file_name, expiration=seconds_per_day)

        # # del os.environ['S3_USE_SIGV4']

        # print(resp)
        # return JsonResponse(resp)


@method_decorator(csrf_exempt, name='dispatch')
class MakeS3FilePublic(generics.GenericAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    """
    Make s3 file public
    """

    def post(self, request, *args, **kwargs):
        print("Request Received")
        file_name = request.POST.get('file_name')
        if not file_name:
            return JsonResponse({"Message": "File name required!"})

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

        s3 = boto3.resource('s3', aws_access_key_id=key,
                            aws_secret_access_key=secret)
        object = s3.Bucket(bucket_name).Object(file_name)
        object.Acl().put(ACL='public-read')

        print("Done")

        return JsonResponse({"Message": "Success"})


@method_decorator(csrf_exempt, name='dispatch')
class S3Upload(generics.ListCreateAPIView, generics.GenericAPIView):

    permission_classes = (permissions.AllowAny,)
    # serializer_class = None

    def post(self, request, *args, **kwargs):
        print("Uploading", request.FILES, request.POST)

        # # TODO: Implement auth here
        # member = 1
        # if not member:
        #     return JsonResponse({'message': 'not logged in'})

        # # Get uploaded file
        print(request.FILES.get('file'))
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Get unique filename using UUID
            file_name = uploaded_file.name
            file_name_uuid = uuid_file_path(file_name)
            s3_key = 'Test/upload/{0}'.format(file_name_uuid)

            content_type, file_url = upload_to_s3(s3_key, uploaded_file)
            print(f"Saving file to s3. member: {file_url}")

            return JsonResponse({'message': 'Success!',
                                 'file_url': file_url,
                                 'content_type': content_type})
        else:
            return JsonResponse({'message': 'No file provided!'})


def upload_to_s3(s3_key, uploaded_file):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    if not key or not secret:
        print("No key or secret found")
        s3_client = boto3.client('s3')
    else:
        print("Use host. key or secret found")
        s3_client = boto3.client(
            's3', aws_access_key_id=key, aws_secret_access_key=secret)

    content_type, _ = mimetypes.guess_type(s3_key)
    s3_client.upload_fileobj(uploaded_file, bucket_name, s3_key,
                            ExtraArgs={'ACL': 'public-read', 'ContentType': content_type})

    return content_type, f'https://s3.amazonaws.com/{bucket_name}/{s3_key}'


def get_presigned_s3_url(object_name, expiration=3600):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    if not key or not secret:
        print("No Access Key and Secret Found")
        s3_client = boto3.client('s3')
    else:
        print("Access Key and Secret Found")
        s3_client = boto3.client(
            's3', aws_access_key_id=key, aws_secret_access_key=secret)

    # Get content type
    content_type, _ = mimetypes.guess_type(object_name)

    # Generate a presigned S3 POST URL
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                        object_name,
                                                        Fields={"Content-Type": content_type,
                                                                "acl": "public-read"},
                                                        Conditions=[
                                                            {"Content-Type": content_type},
                                                            {"acl": "public-read"},
                                                        ],
                                                        ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    response['content_type'] = content_type
    return response


def uuid_file_path(filename):
    if filename:
        ext = filename.split('.')[-1]
    else:
        ext = "png"

    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(filename)


# '''
# Test endpoints
# '''

# Test endpoint - No auth endpoint
class AllCourses(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        return JsonResponse({'messages': 'Get all courses, no auth required'}, safe=False)


# Test endpoint - Auth endpoint with TokenAuthentication
class UserCourses(generics.GenericAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'messages': 'Get user courses, auth token required'}, safe=False)


# Test endpoint - No auth endpoint
@csrf_exempt
def list_courses(request):
    return JsonResponse({'messages': 'Get all courses, no auth required'}, safe=False)


# Test endpoint - Auth endpoint with TokenAuthentication
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_courses_auth(request):
    return JsonResponse({'messages': 'list_courses_protected, auth required'}, safe=False)
