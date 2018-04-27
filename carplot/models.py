# -*- coding: utf-8 -*-
__author__ = 'Roddy Mbogning'

from django.db import models
from datetime import datetime
import datetime
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ikwen.foundation.accesscontrol.models import Member
from ikwen.foundation.core.models import AbstractConfig, Model
from ikwen.foundation.core.utils import to_dict
from ikwen.foundation.core.context_processors import project_settings


GTS = 'opengts'
IS_IKWEN = getattr(settings, 'IS_IKWEN', False)


class OperatorProfile(AbstractConfig):
    sms_limit = models.IntegerField(blank=True, null=True,
        help_text="Max sms command remaining in customer account. eg: 500")
    cost_per_vehicle = models.IntegerField(blank=True, null=True,
        help_text="Amount to be paid per device unit. eg: 2000")
    active_vehicle_count = models.IntegerField(blank=True, null=True,
        help_text="Number of devices that are currently under the track app. eg: 200")
    maximum_latency = models.IntegerField(blank=True, null=True,default=20000,
        help_text="time in millisecond after which the device is consider as non-functional. eg: 10000 for ten second")

    class Meta:
        verbose_name = "Operator"
        verbose_name_plural = "Operators"


class CustomerProfile(models.Model):
    customer = models.OneToOneField(Member)
    max_sms_limit = models.IntegerField()


class DeviceType(models.Model):
    name = models.CharField(max_length=240)
    description = models.CharField(max_length=240, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def to_dict(self):
        var = to_dict(self)
        return var


class SMSCommand(models.Model):
    action = models.CharField(max_length=50, help_text=_("Action to be fired when sending th command"))
    sms_content = models.CharField(max_length=260, help_text=_("Content of the sms to send to the device"))
    device_type = models.ForeignKey(DeviceType, help_text=_("Type of the device that can receive the command"))

    def __unicode__(self):
        return self.action

    def to_dict(self):
        device_type = self.device_type.to_dict()
        var = to_dict(self)
        var['device_type'] = device_type
        return var


class Device(models.Model):
    #The accountId need to be created from Ikwen. and be generated as foreignkey
    accountID = models.CharField(max_length=240,  help_text=
                    _('It can be the email, the login or even the primary key of the member to who belong the device'))
    deviceID = models.CharField(max_length=240, blank=True)
    serialNumber = models.CharField(max_length=240, blank=True, editable=False)
    simPhoneNumber = models.CharField(_('SIM Phone'), max_length=240, blank=True, help_text=
                    _('Phone number of the current SIM to know where to send the commands eg: 237670000000'))
    smsEmail = models.CharField(max_length=240, blank=True, editable=False)
    imeiNumber = models.CharField(_('IMEI'), max_length=240, unique=True, help_text=
                    _('Device EMEI; it is suppose to be unique'))
    displayName = models.CharField(max_length=240, help_text=
                    _('A simple name to recognize the device you are installing'))
    description = models.CharField(max_length=240, blank=True)
    vehicleID = models.CharField(max_length=240, blank=True, editable=False)
    uniqueID = models.CharField(max_length=240, blank=True, editable=False)
    isActive = models.BooleanField(default=True)
    lastValidLatitude = models.FloatField(blank=True, null=True, default=0.0)
    lastValidLongitude = models.FloatField(blank=True, null=True, default=0.0)
    device_type = models.ForeignKey(DeviceType, null=True, blank=True, help_text=
                    _('Type of device'))

    class Meta:
        db_table = 'Device'
        unique_together = (("accountID", "deviceID"),)

    def _get_member(self):
        return Member.objects.get(email=self.accountID)
    member = property(_get_member)

    def __unicode__(self):
        return self.displayName

    def to_dict(self):
        var = to_dict(self)
        # var['created_on'] = self.view_when
        # del(var['creationTime'])
        return var


class VehicleType(models.Model):
    name = models.CharField(max_length=240)
    description = models.CharField(max_length=240, blank=True, null=True)
    active_icon_img_north = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at Northen position"))
    active_icon_img_east = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at Eastern position"))
    active_icon_img_south = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at Southhen position"))
    active_icon_img_west = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at Western position"))
    active_icon_img_north_east = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at North-East position"))
    active_icon_img_north_west = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at North-West position"))
    active_icon_img_south_west = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at South-West position"))
    active_icon_img_south_east = models.ImageField(blank=True, null=True, upload_to='device_img',help_text=_("icon corresponding to the vehicle move at South-East position"))
    static_icon_img = models.ImageField(blank=True, null=True, upload_to='device_img')

    def __unicode__(self):
        return self.name


class Vehicle(models.Model):
    BLOCK = 'Block'
    ACTIVE = 'Active'
    STATUS_CHOICES = (
        (BLOCK, _('Block')),
        (ACTIVE, _('Active')),
    )
    name = models.CharField(max_length=240, help_text= _('Vehicle brand or mark'))
    photo = models.ImageField(blank=True, null=True, upload_to='device_img')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=ACTIVE,
                                     help_text=_("Vevhile current status"))
    type = models.ForeignKey(VehicleType)
    description = models.CharField(max_length=240,blank=True, null=True,  help_text= _('Vehicle specific description'))
    device = models.OneToOneField(Device, help_text=_('Device installed on the vehicle'))
    owner = models.ForeignKey(Member, help_text= _('The customer must be an IKWEN user; because he will need to connect to his plateform using Ikwen access control'))

    def __unicode__(self):
        return "%s / %s" % (self.name, self.device.displayName)

    def to_dict(self):
        var = to_dict(self)
        var['device'] = self.device.to_dict()
        return var


class EventData(models.Model):
    accountID = models.CharField(max_length=240)
    deviceID = models.CharField(max_length=240)
    timestamp = models.IntegerField(blank=True)
    statusCode = models.IntegerField(blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    gpsAge = models.IntegerField(blank=True)
    speedKPH = models.FloatField(blank=True)
    heading = models.FloatField(blank=True)
    altitude = models.FloatField(blank=True)
    transportID = models.CharField(max_length=240, blank=True)
    inputMask = models.IntegerField(blank=True)
    outputMask = models.IntegerField(blank=True)
    seatbeltMask = models.IntegerField(blank=True)
    address = models.TextField(blank=True)
    dataSource = models.TextField(blank=True)
    rawData = models.TextField(blank=True)
    distanceKM = models.FloatField(blank=True)
    odometerKM = models.FloatField(blank=True)
    odometerOffsetKM = models.FloatField(blank=True)
    geozoneIndex = models.IntegerField(blank=True)
    geozoneID = models.IntegerField(blank=True)
    creationTime = models.IntegerField(blank=True)

    class Meta:
        db_table = 'EventData'
        unique_together = (("accountID", "deviceID", "timestamp", "statusCode"),)

    def _get_when(self):
        created_on = datetime.datetime.fromtimestamp(self.creationTime)
        return '%02d/%02d/%d %02d:%02d:%02d' % (created_on.day, created_on.month, created_on.year,
                                                created_on.hour, created_on.minute, created_on.second)
    view_when = property(_get_when)

    def to_dict(self):
        var = to_dict(self)
        var['created_on'] = self.view_when
        # del(var['creationTime'])
        # del(var['timestamp'])
        del(var['dataSource'])
        # del(var['statusCode'])
        del(var['outputMask'])
        # del(var['inputMask'])
        del(var['gpsAge'])
        del(var['transportID'])
        del(var['inputMask'])
        del(var['seatbeltMask'])
        del(var['address'])
        del(var['rawData'])
        del(var['odometerKM'])
        del(var['odometerOffsetKM'])
        del(var['geozoneIndex'])
        del(var['geozoneID'])
        del(var['creationTime'])
        return var


class Geozone(models.Model):
    accountID = models.CharField(max_length=240)
    geozoneID = models.CharField(max_length=240)
    sortID = models.IntegerField(blank=True)
    minLatitude = models.IntegerField(blank=True)
    maxLatitude = models.FloatField(blank=True)
    minLongitude = models.FloatField(blank=True)
    maxLongitude = models.FloatField(blank=True)
    zonePurposeID = models.CharField(max_length=240, blank=True)
    reverseGeocode = models.IntegerField(blank=True)
    arrivalZone = models.IntegerField(blank=True)
    departureZone = models.IntegerField(blank=True)
    autoNotify = models.IntegerField(blank=True)
    zoomRegion = models.IntegerField(blank=True)
    shapeColor = models.CharField(max_length=240, blank=True)
    zoneType = models.IntegerField(blank=True)
    radius = models.IntegerField(blank=True)
    vertices = models.TextField(blank=True)
    latitude1 = models.FloatField(blank=True)
    longitude1 = models.FloatField(blank=True)
    latitude2 = models.FloatField(blank=True)
    longitude2 = models.FloatField(blank=True)
    latitude3 = models.FloatField(blank=True)
    longitude3 = models.FloatField(blank=True)
    latitude4 = models.FloatField(blank=True)
    longitude4 = models.FloatField(blank=True)
    latitude5 = models.FloatField(blank=True)
    longitude5 = models.FloatField(blank=True)
    latitude6 = models.FloatField(blank=True)
    longitude6 = models.FloatField(blank=True)
    latitude7 = models.FloatField(blank=True)
    longitude7 = models.FloatField(blank=True)
    latitude8 = models.FloatField(blank=True)
    longitude8 = models.FloatField(blank=True)
    latitude9 = models.FloatField(blank=True)
    longitude9 = models.FloatField(blank=True)
    latitude10 = models.FloatField(blank=True)
    longitude10 = models.FloatField(blank=True)
    clientUpload = models.TextField(blank=True)
    clientID = models.CharField(max_length=240, blank=True)
    groupID = models.CharField(max_length=240, blank=True)
    streetAddress = models.CharField(max_length=240, blank=True)
    city = models.CharField(max_length=240, blank=True)
    stateProvince = models.CharField(max_length=240, blank=True)
    postalCode = models.CharField(max_length=240, blank=True)
    country = models.CharField(max_length=240, blank=True)
    subdivision = models.CharField(max_length=240, blank=True)
    contactPhone = models.CharField(max_length=240, blank=True)
    isActive = models.BooleanField(default=True)
    displayName = models.CharField(max_length=240, blank=True)
    description = models.CharField(max_length=240, blank=True)
    lastUpdateTime = models.IntegerField(blank=True)
    creationTime = models.IntegerField(blank=True)

    class Meta:
        db_table = 'Geozone'