from rest_framework_mongoengine import serializers

from wonderland_backend.models import Reservation, Timetable


class ReservationSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

class TimetableSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Timetable
        fields = '__all__'