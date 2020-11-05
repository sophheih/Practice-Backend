from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from wonderland_backend.models import Service, Member
from service_api.serializers import ServiceSerializer
from utils.jsonview import json_view


@json_view
@api_view(['GET', 'POST'])
def service_handler(request):
    if request.method == 'GET':
        return service_get_all(request)
    elif request.method == 'POST':
        return service_create(request)


@json_view
@api_view(['GET', 'DELETE', 'PUT'])
def service_id_handler(request, service_id):
    if request.method == 'GET':
        return service_get(request, service_id)
    elif request.method == 'DELETE':
        return service_delete(request, service_id)
    elif request.method == 'PUT':
        return service_update(request, service_id)


def service_get_all(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)

        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20
    services = Service.objects.all().skip(skip).limit(limit)
    service_serializer = ServiceSerializer(services, many=True)
    return JsonResponse(service_serializer.data, safe=False, status=status.HTTP_200_OK)


def service_get(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return JsonResponse(
            {'message': 'The service does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValidationError:
        return JsonResponse(
            {'message': 'The service does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
        
    if token_payload.get('admin'):
        pass
    elif token_payload.get('id'):
        try:
            user_id = token_payload.get('id')
            user = Member.objects.get(id=user_id)
        
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        if service.id != user.id :
            return JsonResponse({'message': 'Permission Denied'},status=status.HTTP_403_FORBIDDEN)

    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    

    
    
    service_serializer = ServiceSerializer(service)
    return JsonResponse(service_serializer.data, safe=False, status=status.HTTP_200_OK)


def service_create(request):
    title = request.POST.get('title', None)
    short_description = request.POST.get('short_description', None)
    long_description = request.POST.get('long_description', None)
    duration = request.POST.get('duration', None)
    price = request.POST.get('price', None)

    if title is None:
        msg = {'message': 'body parameter "title" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif short_description is None:
        msg = {'message': 'body parameter "short_description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif long_description is None:
        msg = {'message': 'body parameter "long_description" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif duration is None:
        msg = {'message': 'body parameter "duration" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    elif price is None:
        msg = {'message': 'body parameter "price" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    
    service = ServiceSerializer(data={
        'title': title,
        'short_description': short_description,
        'long_description': long_description,
        'duration': duration,
        'price': price,
    })
    if service.is_valid():
        service.save()
        return JsonResponse(service.data,status=status.HTTP_201_CREATED)
    return JsonResponse(service.errors, status=status.HTTP_400_BAD_REQUEST)


def service_update(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({"message": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

    title = request.POST.get('title', None)
    short_description = request.POST.get('short_description', None)
    long_description = request.POST.get('long_description', None)
    duration = request.POST.get('duration', None)
    price = request.POST.get('price', None)

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        msg = {'message': 'The service id is invalid'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)

    if not title is None:
        service.title = title
    if not short_description is None:
        service.short_description = short_description
    if not long_description is None:
        service.long_description = long_description
    if not duration is None:
        service.duration = duration
    if not price is None:
        service.price = price
    
    service.save()
    return JsonResponse(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


def service_delete(request, service_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        msg = {'message': 'The service does not exist'}
        return JsonResponse(msg, status=status.HTTP_404_NOT_FOUND)
    service.delete()
    msg = {'message': 'The service was deleted successfully!'}
    return JsonResponse(msg, status=status.HTTP_200_OK)
