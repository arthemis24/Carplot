# -*- coding: utf-8 -*-
__author__ = 'Roddy Mbogning'
from django.conf import settings
from django.contrib.auth.models import Permission, Group
from djangotoolbox.admin import admin
import MySQLdb
from django.utils.translation import gettext_lazy as _
from ikwen.core.utils import get_service_instance, add_database_to_settings

from ikwen.accesscontrol.models import Member
from ikwen.billing.models import Invoice, Payment, Product, InvoicingConfig
from ikwen.core.models import Application, Service, Config
from carplot.models import Vehicle,Device, SMSCommand, DeviceType, OperatorProfile, IS_IKWEN, VehicleType, \
    CustomerProfile

GTS_HOST = "localhost"
GTS_USER = "root"
GTS_PWD = "admin"
GTS_DB = "gts"


class CarplotAdmin(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("ikwen/font-awesome/css/font-awesome.min.css", "ikwen/css/flatly.bootstrap.min.css",
                    "ikwen/css/grids.css", "ikwen/billing/admin/css/custom.css", )
        }
        js = ("ikwen/js/jquery-1.12.4.min.js", "ikwen/js/jquery.autocomplete.min.js", "ikwen/billing/admin/js/custom.js", )


if getattr(settings, 'IS_IKWEN', False):
    _fieldsets = [
        # (_('Business'), {'fields': ('ikwen_share', 'payment_delay', 'cash_out_min', 'is_certified', )}),
        (_('SMS'), {'fields': ('sms_api_script_url', 'sms_api_username', 'sms_api_password', )}),
        (_('Pricing'), {'fields': ('sms_limit', 'cost_per_vehicle', 'active_vehicle_count', )}),
        (_('Mailing'), {'fields': ('welcome_message', 'signature',)})
    ]
else:
    _fieldsets = [
        (_('SMS'), {'fields': ('sms_api_script_url', 'sms_api_username', 'sms_api_password',)}),
        (_('Company'), {'fields': ('company_name', 'short_description', 'slogan', 'description')}),
        (_('Website'), {'fields': ('currency', )}),
        (_('Address & Contact'), {'fields': ('contact_email', 'contact_phone', 'address', 'country', 'city')}),
        (_('Social'), {'fields': ('facebook_link', 'twitter_link', 'google_plus_link', 'instagram_link', 'linkedin_link', )}),
        # (_('SMS'), {'fields': ('sms_sending_method', 'sms_api_script_url', 'sms_api_username', 'sms_api_password', )}),
        (_('Mailing'), {'fields': ('welcome_message', 'signature', )}),
    ]

    if getattr(settings, 'IS_PRO_VERSION'):
        _fieldsets.extend([
            (_('PayPal'), {'fields': ('paypal_user', 'paypal_password', 'paypal_api_signature', )}),
            (_('Scripts'), {'fields': ('google_analytics', )}),
        ])


class VehicleInline(admin.StackedInline):
    list_display = ('name', 'device', 'owner')
    search_fields = ('name', 'owner')
    readonly_fields = ('owner',)
    model = Vehicle

    def save_model(self, request, obj, form, change):
        super(VehicleInline, self).save_model(request, obj, form, change)
        service = get_service_instance()
        config = service.config
        config.active_vehicle_count += 1
        config.save()


class DeviceAdmin(CarplotAdmin):
    list_display = ('displayName','simPhoneNumber', 'device_type', 'imeiNumber', 'isActive')
    search_fields = ('displayName', 'deviceID', 'serialNumber', 'imeiNumber')
    readonly_fields = ('accountID', 'deviceID')
    fieldsets = (
        (None, {
            'fields': ('imeiNumber', 'simPhoneNumber', 'device_type', 'displayName')
        }),
    )
    inlines = [
        VehicleInline,
    ]

    def save_model(self, request, obj, form, change):

        super(DeviceAdmin, self).save_model(request, obj, form, change)
        obj.uniqueID = 'tk_%s' % obj.imeiNumber
        obj.vehicleID = 'tk_%s' % obj.imeiNumber
        obj.deviceID = obj.id
        obj.save()
        try:
            Device.objects.using('opengts').get(vehicleID=obj.vehicleID, imeiNumber=obj.imeiNumber, deviceID=obj.deviceID)
        except Device.DoesNotExist:
            obj.id = None
            # I set a default integer value (5) to the field "device_type_id" because mysql data bases do not allow varchars as keys
            obj.device_type_id = 5
            obj.accountID = request.user.username
            obj.save(using='opengts')
        else:
            with MySQLdb.connect(GTS_HOST, GTS_USER, GTS_PWD, GTS_DB) as cursor:
                cursor.execute("UPDATE Device SET vehicleID = %s, description = %s, displayName =  %s, imeiNumber =  %s,"
                               " simPhoneNumber =  %s WHERE deviceID = %s", [obj.vehicleID, obj.description,
                                                                             obj.displayName, obj.imeiNumber,
                                                                             obj.simPhoneNumber, obj.deviceID])


class SMSCommandAdmin(CarplotAdmin):
    list_display = ('action', 'sms_content', 'device_type')
    search_fields = ('action',)
    ordering = ('-id', )


class OperatorProfileAdmin(CarplotAdmin):
    list_display = ('project_name', 'company_name', 'operator_name', 'cost_per_vehicle', 'active_vehicle_count')
    fieldsets = _fieldsets

    def project_name(self, obj):
        return obj.service.project_name

    def operator_name(self, obj):
        return obj.service.member.full_name


class DeviceTypeAdmin(CarplotAdmin):
    list_display = ('name', )
    search_fields = ('name',)


class VehicleTypeAdmin(CarplotAdmin):
    list_display = ('name', )
    search_fields = ('name',)

    # def save_model(self, request, obj, form, change):
    #     app = Application.object.get(slug='carplot')
    #     services = Service.objects.filter(app=app)
    #     for service in services:
    #         add_database_to_settings(service.database)
    #         obj.save.using(service.database)


class CustomerProfileAdmin(CarplotAdmin):
    list_display = ('customer', 'max_sms_limit')


if IS_IKWEN:
    admin.site.register(VehicleType, VehicleTypeAdmin)
    admin.site.register(OperatorProfile, OperatorProfileAdmin)
else:
    admin.site.register(VehicleType, VehicleTypeAdmin)
    admin.site.register(Device, DeviceAdmin)
    admin.site.register(SMSCommand, SMSCommandAdmin)
    admin.site.register(DeviceType, DeviceTypeAdmin)
    admin.site.register(CustomerProfile, CustomerProfileAdmin)
    admin.site.register(OperatorProfile, OperatorProfileAdmin)
# admin.site.unregister(Member)
# admin.site.unregister(Product)
# admin.site.unregister(Payment)
# admin.site.unregister(Invoice)
# admin.site.unregister(InvoicingConfig)
# admin.site.unregister(Application)
# admin.site.unregister(Service)
# admin.site.unregister(Config)
# admin.site.unregister(Permission)
# admin.site.unregister(Group)
    # admin.site.unregister(Device)
