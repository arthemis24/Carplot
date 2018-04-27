# -*- coding: utf-8 -*-
__author__ = 'Roddy Mbogning'

import time
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from ikwen.core.views import BaseView
from ikwen.core.utils import get_service_instance
from conf import settings
from carplot.models import EventData, Device, SMSCommand, Vehicle, OperatorProfile

import requests

GTS = 'opengts'
# 2368541 1462407550


class IframeAdmin(TemplateView):
    template_name = 'iframe_admin.html'

    def get_context_data(self, **kwargs):
        context = super(IframeAdmin, self).get_context_data(**kwargs)
        model_name = kwargs['model_name']
        iframe_url = reverse('admin:carplot_' + model_name + '_changelist')
        context['model_name'] = model_name
        context['iframe_url'] = iframe_url
        return context


class Home(BaseView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        user = self.request.user
        vehicles = Vehicle.objects.filter(status=Vehicle.ACTIVE, owner=user)
        update_vehicles_last_position(vehicles)
        markers = [
            {
                'name': vehicle.name,
                'description': vehicle.description,
                'vehicle_img': vehicle.photo.url,
                'latitude': vehicle.device.lastValidLatitude,
                'longitude': vehicle.device.lastValidLongitude,
                'displayName': vehicle.device.displayName,
                'icon': vehicle.type.static_icon_img.url,
                'photo': vehicle.photo.url,
            }
            for vehicle in vehicles if
            vehicle.device.lastValidLatitude != 0.0 and vehicle.device.lastValidLatitude != 0.0]
        context['markers'] = json.dumps(markers)
        context['vehicles'] = Vehicle.objects.filter(status=Vehicle.ACTIVE, owner=user)
        return context


class AdminHome(BaseView):
    template_name = 'admin_home.html'

    def get_context_data(self, **kwargs):
        context = super(AdminHome, self).get_context_data(**kwargs)
        iframe_url = reverse('admin:index')
        context['iframe_url'] = iframe_url
        return context


@login_required
def get_sms_command(request, *args, **kwargs):
    device_id = request.GET.get('device_id')
    device = Device.objects.get(id=device_id)
    sms_commands = SMSCommand.objects.filter(device_type=device.device_type)
    response = [sms_command.to_dict() for sms_command in sms_commands]
    return HttpResponse(json.dumps({'sms_command': response}), 'content-type: text/json', **kwargs)


@login_required
def get_device_event_data(request, *args, **kwargs):
    """
    Get a list of event data according to the request and the argument giving.

    @param member: Member object to whom vehicule belongs to or the owner
    @param device_id: Id of the vehicle object in the database
    @param string_date: string format date sent from the client eg: 01/05/2016 12:00 - 07/05/2016 11:00
    @param string_start_date: building from the string format date
    @param string_end_date: building from the string format date
    @param positions: queryset of even data happened during the period choosen by the client
    @param data_count: number of data event of the current user; this is use during the live dislay to know if the device sent a new event data or not
    this function return a JSON objet of: event data and data count
    """
    member = request.user
    device_id = request.GET.get('device_id')
    string_date = request.GET.get('string_date')
    string_start_date = None
    string_end_date = None
    device = Device.objects.get(pk=device_id)
    if string_date:
        dates_list = retrieve_dates_from_interval(string_date)
        string_start_date = dates_list[0]
        string_end_date = dates_list[1]
    vehicle = Vehicle.objects.get(device=device)
    positions = EventData.objects.using('opengts').filter(deviceID=device_id)
    # positions = EventData.objects.using('opengts')
    data_count = positions.count()
    start_date, end_date = None, None
    if string_start_date is not None:
        start_date = int(time.mktime(datetime.strptime(string_start_date, '%d-%m-%Y %H:%M').timetuple()))
    if string_end_date is not None:
        end_date = int(time.mktime(datetime.strptime(string_end_date, '%d-%m-%Y %H:%M').timetuple()))

    if start_date and end_date:
        positions = positions.filter(Q(creationTime__gte=start_date) & Q(creationTime__lt=end_date))
    elif start_date and not end_date:
        now = datetime.now()
        end_date = time.mktime(now.timetuple())
        positions = positions.filter(Q(creationTime__gte=start_date) & Q(creationTime__lt=end_date))
    elif end_date and not start_date:
        end_date_dtime = datetime.strptime(string_end_date, '%d-%m-%Y %H:%M')
        end_date_dt = datetime(end_date_dtime.year, end_date_dtime.month, end_date_dtime.day, 0)
        start_date = int(time.mktime(end_date_dt.timetuple()))
        positions = positions.filter(Q(creationTime__gte=start_date) & Q(creationTime__lt=end_date))
    if not start_date and not end_date and len(positions)>0:
        positions = [positions.order_by('-creationTime')[0]]
    else:
        # Order by -creationTime and grab the first 1000,
        # that is equivalent to grab the 1000 latest eventData
        positions = list(positions.order_by('-creationTime')[:1000])
        positions = reversed(positions)
    event_data = []

    late_lat = 0.0
    late_lng = 0.0
    for position in positions:
        if position.speedKPH > 0:
            icon_url = get_the_right_icon(position, device)
        else:
            icon_url = vehicle.type.static_icon_img.url
        if late_lat != position.latitude and late_lng != position.longitude:
            if position.latitude != 0.0 and position.longitude != 0.0:
                pos = {
                    'latitude': position.latitude,
                    'longitude': position.longitude,
                    'displayName': device.displayName,
                    'dateTime': change_date_to_string(datetime.fromtimestamp(position.creationTime)),
                    'speed': position.speedKPH,
                    'heading': position.heading,
                    'address': position.address,
                    'description': vehicle.name + " / " + device.displayName,
                    'icon': icon_url
                }
                event_data.append(pos)
        late_lat = position.latitude
        late_lng = position.longitude
    return HttpResponse(json.dumps({'event_data': event_data, 'data_count': data_count}), 'content-type: text/json', **kwargs)


def change_date_to_string(date_to_stringify):
    changed_date = '%02d/%02d/%d  %02d:%02d:%02d' % (
        date_to_stringify.year, date_to_stringify.month, date_to_stringify.day, date_to_stringify.hour,
        date_to_stringify.minute, date_to_stringify.second)
    return changed_date


def retrieve_dates_from_interval(string_date):
    date_array = string_date.replace(' - ', '-')
    date_array = string_date.split('-')
    dates = []
    for d in date_array:
        d = d.replace('/', '-')
        dates.append(d.strip())
    return dates


@login_required
def search(request, *args, **kwargs):
    keyword = request.GET.get('query')
    user = request.user
    vehicles = Vehicle.objects.filter(name__icontains=keyword, owner=user)
    response = [device.to_dict() for device in vehicles]
    return HttpResponse(json.dumps({'response': response}), 'content-type: text/json', **kwargs)


@login_required
def send_smsCommand(request, *args, **kwargs):
    service = get_service_instance()
    config = service.config
    if config.sms_limit > 0:
        device_id = request.GET.get('device_id')
        sms_id = request.GET.get('sms_id')
        device = Device.objects.get(id=device_id)
        sms_command = SMSCommand.objects.get(id=sms_id)
        phone = device.simPhoneNumber
        message = sms_command.sms_content
        url = construct_sms_sending_url(phone, message)
        requests.get(url)
        config.sms_limit -= 1
        config.save()
        return HttpResponse(json.dumps({'success': True}), 'content-type: text/json', **kwargs)
    else:
        return HttpResponse(json.dumps({'No_SMS': True}), 'content-type: text/json', **kwargs)


def construct_sms_sending_url(recipient, text):
    service = get_service_instance()
    config = service.config
    url = config.sms_api_script_url
    username = config.sms_api_username
    password = config.sms_api_password
    sender = config.company_name
    url = url.replace('$username', username)
    url = url.replace('$password', password)
    url = url.replace('$sender', sender)
    url = url.replace('$recipient', recipient)
    url = url.replace('$text', text)
    return url


def get_the_right_icon(event, device):
    icon_url = ""
    vehicle = Vehicle.objects.get(device=device)
    if event.heading == 0 :
        icon_url = vehicle.type.active_icon_img_north.url
    elif event.heading > 0 and event.heading < 90:
        icon_url = vehicle.type.active_icon_img_north_east.url
    elif event.heading == 90:
        icon_url = vehicle.type.active_icon_img_east.url
    elif event.heading > 90 and event.heading < 180:
        icon_url = vehicle.type.active_icon_img_south_east.url
    elif event.heading == 180:
        icon_url = vehicle.type.active_icon_img_south.url
    elif event.heading > 180 and event.heading < 270:
        icon_url = vehicle.type.active_icon_img_south_west.url
    elif (event.heading == 270):
        icon_url = vehicle.type.active_icon_img_west.url
    elif event.heading > 270 and event.heading < 379:
        icon_url = vehicle.type.active_icon_img_north_west.url
    return icon_url


def update_vehicles_last_position(vehicles):
    for vehicle in vehicles:
        gts_device = Device.objects.using('opengts').get(deviceID=vehicle.device.id)
        mongo_device = vehicle.device
        if gts_device.lastValidLatitude != mongo_device.lastValidLatitude or gts_device.lastValidLongitude != mongo_device.lastValidLongitude:
            mongo_device.lastValidLatitude = gts_device.lastValidLatitude
            mongo_device.lastValidLongitude = gts_device.lastValidLongitude
            mongo_device.save()