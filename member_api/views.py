import hashlib
from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from member_api.serializers import MemberSerializer,  MemMemberSerializer, AdminMemberSerializer
from wonderland_backend.models import Member
from utils.jsonview import json_view


@json_view
@api_view(['GET'])
def member(request):
    if request.method == 'GET':
        return get_all_member(request)

def get_all_member(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        skip = request.GET.get('skip', '0')
        limit = request.GET.get('limit', '20')
        skip = int(skip) if str(skip).isnumeric() else 0
        limit = int(limit) if str(limit).isnumeric() else 20
        user_info = Member.objects.all().skip(skip).limit(limit)

        try:
            user_info_serializer = AdminMemberSerializer(
                user_info, many=True)
            return JsonResponse(
                user_info_serializer.data, safe=False
            )
        except:
            return JsonResponse({"message": "User Data In Database Is Invalid."}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return JsonResponse(
            {'message': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )


@json_view
@api_view(['POST'])
def register(request):
    
    username = request.POST.get('username', None)
    real_name = request.POST.get('real_name', None)
    password = request.POST.get('password', None)
    gender = request.POST.get('gender', None)
    cellphone = request.POST.get('cellphone', None)
    email = request.POST.get('email',None)

    if username is None:
        msg = {'message': 'body parameter "username" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif real_name is None:
        msg = {'message': 'body parameter "real_name" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif password is None:
        msg = {'message': 'body parameter "password" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif gender is None:
        msg = {'message': 'body parameter "gender" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif cellphone is None:
        msg = {'message': 'body parameter "cellphone" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif email is None:
        msg = {'message': 'body parameter "email" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    

    if len(password) >= 8:
        password_md5 = hashlib.md5()
        password_md5.update(
            password.encode(encoding='utf-8'))
        password_md5 = password_md5.hexdigest()
        del password
    else:
        return JsonResponse({"message": "password unqualified"},
                            status=status.HTTP_400_BAD_REQUEST)

    if len(cellphone) > 10:
        return JsonResponse(
            {'message': 'Cellphone has no more than 10 characters.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    

    serializer = MemberSerializer(data={
        'username': username,
        'real_name':real_name,
        'password_md5':password_md5,
        'gender':gender,
        'cellphone':cellphone,
        'email':email
    })
    if serializer.is_valid():
        try:
            Member.objects.get(username=username)
        except Member.DoesNotExist:
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse({"message": "user already exists."}, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@json_view
@api_view(['GET', 'PUT', 'DELETE'])
def member_id(request, user_id):
    
    if request.method == 'GET':
        return get_member(request, user_id)
    
    elif request.method == 'PUT':
        return update_member(request,user_id)

    elif request.method == 'DELETE':
        return delete_member(request,user_id)




@ json_view
@ api_view(['POST'])
def login(request):
    username = request.POST.get('username', None)
    password = request.POST.get('password',None)

    if username is None:
        msg = {'message': 'body parameter "username" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif password is None:
        msg = {'message': 'body parameter "password" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Member.objects.get(username=username)
    except Member.DoesNotExist:
        return JsonResponse(
            {'message': 'Username or password is wrong.'},
            status=status.HTTP_404_NOT_FOUND
        )

    md5_encrypt = hashlib.md5()
    md5_encrypt.update(password.encode("utf-8"))
    compare_password = md5_encrypt.hexdigest()

    if user.password_md5 == compare_password:

        get_user_data_serializer = AdminMemberSerializer(user)
        return JsonResponse({"user": get_user_data_serializer.data, "token": user.token})

    return JsonResponse(
        {'message': 'Username or password is wrong.'},
        status=status.HTTP_404_NOT_FOUND
    )

def get_member(request,user_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    if token_payload.get('admin') or token_payload.get('id'):
        try:
            user = Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError:
            return JsonResponse(
                {'message': 'Invaildated ID.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if token_payload.get('id'):
            member = Member.objects.get(id=token_payload.get('id'))
            if user.id != member.id:
                return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AdminMemberSerializer(user)
        return JsonResponse(
            serializer.data, safe=False
        )

    else:
        return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)

def update_member(request,user_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin') or token_payload.get('id'):
        new_user_data = JSONParser().parse(request)

        try:
            user = Member.objects.get(id=user_id)
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The user does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        if token_payload.get('id'):
            member = Member.objects.get(id=token_payload.get('id'))
            if user.id != member.id:
                return JsonResponse({"message": "Permission Denied."}, status=status.HTTP_400_BAD_REQUEST)
                
        if 'password' in new_user_data:
            if len(new_user_data["password"]) >= 8:
                password_md5 = hashlib.md5()
                password_md5.update(
                    new_user_data['password'].encode(encoding='utf-8'))
                new_user_data["password_md5"] = password_md5.hexdigest()
                del new_user_data['password']
            else:
                return JsonResponse({"message": "password unqualified"},
                                    status=status.HTTP_400_BAD_REQUEST)

        if 'cellphone' in new_user_data:
            if len(new_user_data['cellphone']) > 10:
                return JsonResponse(
                    {'message': 'Cellphone has no more than 10 characters.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if token_payload.get('admin'):
            serializer = MemberSerializer(user, data=new_user_data)
        else:
            serializer = MemMemberSerializer(user, data=new_user_data)

        if serializer.is_valid():
            serializer.save()

            return JsonResponse(serializer.data, safe=False, status=status.HTTP_201_CREATED, json_dumps_params={'ensure_ascii': False})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse(
        {'message': 'Permission denied'},
        status=status.HTTP_403_FORBIDDEN
    )

def delete_member(request,user_id):
    try:
        user = Member.objects.get(id=user_id)
    except Member.DoesNotExist:
        return JsonResponse(
            {'message': 'The user does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    user.delete()
    return JsonResponse(
        {'message': 'The user was deleted successfully!'}, status=status.HTTP_200_OK
    )