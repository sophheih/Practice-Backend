from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework import status
from django.http.response import JsonResponse
from mongoengine.errors import ValidationError
from wonderland_backend.models import Reservation, Member, Service,Timetable
from reservation_api.serializers import ReservationSerializer, TimetableSerializer
from utils.jsonview import json_view
from datetime import datetime
from bson.objectid import ObjectId
import json


@json_view
@api_view(['GET'])
def reservation_handler(request):
    if request.method == 'GET':
        return get_filter_reservation(request)
def get_filter_reservation(request):
    reservation_filter = {}
    token_payload = request.META.get('TOKEN_PAYLOAD')
    member_id = request.GET.get('member_id', '')
    date = request.GET.get('date', '')

    skip = request.GET.get('skip', '0')
    limit = request.GET.get('limit', '20')
    skip = int(skip) if str(skip).isnumeric() else 0
    limit = int(limit) if str(limit).isnumeric() else 20

    if not (token_payload.get('admin')):
        if token_payload.get('id'):
            try:
                member = Member.objects.get(id=token_payload.get('id'))
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The member does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return JsonResponse(
                {'message': 'Permission Denied'},
                status=status.HTTP_403_FORBIDDEN
            )
    if member_id != '':

        if not (token_payload.get('admin')):
            if ObjectId(member_id) != member.id:
                return JsonResponse(
                    {'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
        try:
            member = Member.objects.get(id=member_id)
            reservation_filter['member_id'] = ObjectId(member_id)
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError:
            return JsonResponse(
                {'message': 'Invalid ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

    if date != '':
        time_end = datetime.fromtimestamp(int(date)+86400)
        time = datetime.fromtimestamp(int(date))
        reservation_filter['start_time'] = {'$gte': time}
        reservation_filter['end_time'] = {'$lte': time_end}
    if request.GET == {}:
        if not token_payload.get('admin'):
            return JsonResponse(
                {'message': 'Permission Denied'},
                status=status.HTTP_403_FORBIDDEN
            )
    if token_payload.get('id'):
        reservation_filter['member_id'] = member.id
    reservations = Reservation.objects(
        __raw__=reservation_filter).skip(skip).limit(limit)

    if token_payload.get('admin'):
        serializer = ReservationSerializer(reservations, many=True)
    else:
        serializer = ReservationSerializer(reservations, many=True)
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

@json_view
@api_view(['PUT', 'DELETE', 'GET'])
def reservation_withid(request, reservation_id):

    if request.method == 'GET':
        return get_reservation(request,reservation_id)
    elif request.method == 'PUT':
        return update_reservation(request,reservation_id)
    elif request.method == 'DELETE':
        return delete_reservation(request,reservation_id)
        

def get_reservation(request,reservation_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')

    if not (token_payload.get('admin')):
        if token_payload.get('id'):
            try:
                member = Member.objects.get(id=token_payload.get('id'))
            except Member.DoesNotExist:
                return JsonResponse(
                    {'message': 'The member does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return JsonResponse(
                {'message': 'Permission Denied'},
                status=status.HTTP_403_FORBIDDEN
            )
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse(
            {'message': 'The reservation does not exist'}, safe=False,
            status=status.HTTP_404_NOT_FOUND
        )
    if not (token_payload.get('admin')):
        if reservation.member_id != member.id:
            return JsonResponse(
                {'message': 'Permission Denied'},
                status=status.HTTP_403_FORBIDDEN
            )
    serializer = ReservationSerializer(reservation)
    return JsonResponse(
        serializer.data, safe=False
    )

def update_reservation(request,reservation_id):

    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    new_data = JSONParser().parse(request)
    duration_min = 0
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse(
            {'message': 'The reservation does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )

    if 'member_id' in new_data.keys():
        member_id = ObjectId(new_data['member_id'])
        reservation.member_id = member_id

    if 'services' in new_data.keys():
        total_price = 0
        service_detail = []
        for service_id in new_data["services"]:
            try :
                service = Service.objects.get(id = service_id).to_json()
                service = json.loads(service, encoding='utf-8')
                service['id'] = str(service['_id']['$oid'])
                service.pop('_id')
                service.pop('long_description')
                service_detail.append(service)

                duration_min += service['duration']
                total_price += service['price']
            except Service.DoesNotExist:
                return JsonResponse({'message':'Service does not exists'},status=status.HTTP_404_NOT_FOUND)
        reservation.total_price = total_price
        reservation.services = service_detail

    if 'start_time' in new_data.keys():
        start_time = int(new_data['start_time'])
        if duration_min == 0:
            for service in reservation.services:
                duration_min += service['duration']
            start_time = int(start_time)
            end_time = int(start_time)+int(duration_min)*60
        else:
            start_time = int(new_data['start_time'])
            end_time = start_time+int(duration_min)*60
        reservation.start_time = datetime.fromtimestamp(start_time)
        reservation.end_time = datetime.fromtimestamp(end_time)

    reservation.save()

    reservation_2 = {
        'id' :reservation_id,
        'member_id':str(reservation.member_id),
        'total_price':reservation.total_price,
        'start_time':int(datetime.timestamp(reservation.start_time)),
        'end_time':int(datetime.timestamp(reservation.end_time)),
        'services':reservation.services
    }
    return JsonResponse(reservation_2, status=status.HTTP_200_OK)

def delete_reservation(request,reservation_id):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if not token_payload.get('admin'):
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        reservation = Reservation.objects.get(
            id=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse(
            {'message': 'The reservation does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    start_time = int(datetime.timestamp(reservation.start_time))
    end_time = int(datetime.timestamp(reservation.end_time))
    time_date = start_time - (start_time+28800) % 86400

    timetables = Timetable.objects.get(date=time_date)
    time_interval = 1800

    n = ((end_time - start_time)//time_interval)

    for j in range(n):
        thirty = start_time + j*time_interval
        print(thirty)
        timetables.time[str(thirty)] -= 1
    timetables.save()
    
    

    return JsonResponse(
        {'message': 'The reservation has been deleted.'},
        status=status.HTTP_200_OK
    )



@json_view
@api_view(['POST', 'GET'])
def reservation_new(request):

    if request.method == 'GET':
        return get_time_avilable(request)

    elif request.method == 'POST':
        return create_reservation(request)

def create_reservation(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('id'):
        try:
            user = Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    reservation_data = JSONParser().parse(request)

    if reservation_data['start_time'] != '':
        start_time = reservation_data['start_time']
    else:
        msg = {'message': 'body parameter "start_time" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)
    if reservation_data['services'] !='':
        services = reservation_data['services']
    else: 
        msg = {'message': 'body parameter "services" should be given'}
        return JsonResponse(msg, status=status.HTTP_400_BAD_REQUEST)


    member_id = user.id
    total_price = 0
    duration_min = 0
    
    for service_id in services:
        try:
            service = Service.objects.get(id=service_id)

            total_price += service['price']
            duration_min += service['duration']

        except Service.DoesNotExist:
            return JsonResponse(
                {'message': 'The service does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    start_time = int(start_time)
    end_time = start_time+int(duration_min)*60

   
    time_date = start_time - (start_time+28800) % 86400
    time_interval = 1800
    try:
        timetables = Timetable.objects.get(date = time_date)
    except Timetable.DoesNotExist:  
        create_timetable(time_date)
        timetables = Timetable.objects.get(date = time_date)
    nn = (end_time-start_time)//time_interval-1
    c = 0
    for j in range(int(nn)):
        thirty = start_time + j*time_interval
        if timetables.time[str(thirty)] >= 3:
            break
        else:
            c += 1
    if c != nn:
        return JsonResponse({'message':'Sorry! The interval had been taken by others.'},status=status.HTTP_400_BAD_REQUEST)

    if user['balance'] >= total_price >= 0:
        user['balance'] -= total_price
        user.save()
        for j in range(nn+1):
            thirty = start_time + j*time_interval
            timetables.time[str(thirty)] += 1
        timetables.save()

    else:
        return JsonResponse(
            {'message': 'User balance not enough.'},
            status=status.HTTP_402_PAYMENT_REQUIRED
        )


    services_detail = []
    for service_id in services:
        try:
            service = Service.objects.get(
                id=ObjectId(str(service_id))).to_json()

            service = json.loads(service, encoding='utf-8')
            service['id'] = str(service['_id']['$oid'])
            service.pop('_id')
            service.pop('long_description')
            services_detail.append(service)
        except Service.DoesNotExist:
            return JsonResponse(
                {'message': 'Service does not exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    

    serializer_fordb = ReservationSerializer(data={
        'member_id': member_id,
        'start_time':datetime.fromtimestamp(start_time+3600*8),
        'end_time':datetime.fromtimestamp(end_time+3600*8),
        'services':services_detail,
        'total_price':total_price
    })

    data_forft = {
        'member_id': str(member_id),
        'start_time':start_time,
        'end_time':end_time,
        'services':services_detail,
        'total_price':total_price
    }

    if serializer_fordb.is_valid():
        serializer_fordb.save()



    return JsonResponse(
        data_forft,
        status=status.HTTP_200_OK
    )

def get_time_avilable(request):
    token_payload = request.META.get('TOKEN_PAYLOAD')
    if token_payload.get('id'):
        try:
            Member.objects.get(id=token_payload.get('id'))
        except Member.DoesNotExist:
            return JsonResponse(
                {'message': 'The member does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return JsonResponse({'message': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)

    duration = request.GET.get('duration', '')
    time = request.GET.get('time', '')
    if duration == '':
        return JsonResponse(
            {'message': 'duration must be given.'},
            status.HTTP_400_BAD_REQUEST
        )
    if time == '':
        return JsonResponse(
            {'message': 'time must be given.'},
            status.HTTP_400_BAD_REQUEST
        )

    time = int(time)
    time_interval = 1800
    time_near = time + (time_interval-time % time_interval)
    time_date = time - ((time+28800) % 86400)
    time_11am = time_date+3600*11
    end = time_11am+3600*9

    try:
        timetables = Timetable.objects.get(date=time_date)
    except Timetable.DoesNotExist:
        create_timetable(time_date)
        timetables = Timetable.objects.get(date=time_date)

    if time_11am >= time_near:
        n = (3600*9//time_interval)
    else:
        n = (time_11am+3600*9-time_near)//time_interval
    
    avliable_time = []
    for i in range(n+1):
        c = 0
        if time_11am > time_near:
            start = time_11am+(i)*time_interval
            over = start+int(duration)*60
        else:
            start = time_near+(i)*time_interval
            over = start+int(duration)*60
    
        if over > end:
            break
        
        nn = (over-start)//time_interval-1
        
        for j in range(nn):
            thirty = start + j*time_interval
            
            try:
                if timetables.time[str(thirty)] >= 3:
                    break
                else:
                    c += 1
            except:
                return JsonResponse({'message':'Some error with the time interval'},status=status.HTTP_404_NOT_FOUND)
        if c == nn:
            avliable_time.append(int(start))
                
    return JsonResponse(avliable_time, safe=False, status=status.HTTP_200_OK)

          
def create_timetable(date):
    time = {}
    for i in range((3600*9//1800)):
        time[int(date+3600*11)+i*1800] = 0
    timetable_serializer = TimetableSerializer(data={'date' : date, 'time':time})
    if timetable_serializer.is_valid():
        timetable_serializer.save()
