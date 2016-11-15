#__BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

from django import forms
from django.forms import ModelForm
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import DateTimeField
from django.utils.functional import lazy

from dal import autocomplete
from geocamUtil.extFileField import ExtFileField
from geocamUtil.loader import LazyGetModelByName
from geocamUtil.forms.AbstractImportForm import getTimezoneChoices
from geocamTrack.forms import SearchTrackForm

from basaltApp.models import *
from xgds_instrument.forms import ImportInstrumentDataForm, InstrumentModelChoiceField, SearchInstrumentDataForm
from xgds_instrument.models import ScienceInstrument
from xgds_sample.forms import SearchSampleForm
from xgds_image.forms import SearchImageSetForm
from xgds_notes2.forms import SearchNoteForm
from xgds_planner2.models import Vehicle
from xgds_core.models import XgdsUser

from models import EV, PxrfDataProduct, AsdDataProduct, FtirDataProduct

from basaltApp.instrumentDataImporters import pxrfLoadPortableSampleData, pxrfParseElementResults

GROUP_FLIGHT_MODEL = LazyGetModelByName(settings.XGDS_PLANNER2_GROUP_FLIGHT_MODEL)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    comments = forms.CharField(required=False, label="Introduce yourself", widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Hack to modify the sequence in which the fields are rendered
        self.fields.keyOrder = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'comments']

    def clean_email(self):
        "Ensure that email addresses are unique for new users."
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email address already exists.")
        return email
    
    class Meta:
        model = User
        fields = ("username",'first_name', 'last_name', 'email', 'password1', 'password2', 'comments')


class EmailFeedbackForm(forms.Form):
    reply_to = forms.EmailField(required=False, label="Your email address")
    email_content = forms.CharField(widget=forms.Textarea, label="Message")


class EVForm(ModelForm):
    user = forms.ModelChoiceField(XgdsUser.objects.all(), 
                                  widget=autocomplete.ModelSelect2(url='select2_model_user'))
    class Meta:
        model = EV
        fields = ['mass', 'user',]


class BasaltInstrumentDataForm(ImportInstrumentDataForm):
    INSTRUMENT_MODEL = LazyGetModelByName(settings.XGDS_INSTRUMENT_INSTRUMENT_MODEL)
    instrument = InstrumentModelChoiceField(INSTRUMENT_MODEL.get().objects.all(), widget = forms.HiddenInput())
    name = forms.CharField(required=False, label="Name")
    description = forms.CharField(widget=forms.Textarea, label="Description", required=False)
    minerals = forms.CharField(widget=forms.Textarea, label="Minerals", required=False)

class PxrfInstrumentDataForm(BasaltInstrumentDataForm):
    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M'
        ]
    minerals = forms.CharField(widget=forms.Textarea, label="Elements", required=False)
    portableDataFile = ExtFileField(ext_whitelist=(".csv",),
                                    required=False,
                                    label="Portable Data File")
    elementResultsCsvFile = ExtFileField(ext_whitelist=(".csv",),
                                         required=True,
                                         label="Results Csv File")
    dataCollectionTime = DateTimeField(label="Collection Time",
                                       input_formats=date_formats,
                                       required=False,
                                       )
    field_order = ['timezone', 'resource', 'dataCollectionTime', 'portableDataFile', 'manufacturerDataFile', 'elementResultsCsvFile',
                   'lat', 'lon', 'alt', 'name', 'description', 'minerals']
    
    def editingSetup(self, dataProduct):
        self.fields['portableDataFile'].initial = dataProduct.portable_data_file
        self.fields['manufacturerDataFile'].initial = dataProduct.manufacturer_data_file
        self.fields['elementResultsCsvFile'].initial = dataProduct.elementResultsCsvFile
    
    def handleFileUpdate(self, dataProduct, key):
        if key == 'portableDataFile':
            pxrfLoadPortableSampleData(self.cleaned_data[key], dataProduct)
        elif key == 'elementResultsCsvFile':
            pxrfParseElementResults(self.cleaned_data[key], dataProduct)

class SearchPXRFDataForm(SearchInstrumentDataForm):
     
    field_order = PxrfDataProduct.getSearchFieldOrder()
 
    class Meta:
        model = PxrfDataProduct
        fields = PxrfDataProduct.getSearchFormFields()
        
class SearchASDDataForm(SearchInstrumentDataForm):
    
    field_order = AsdDataProduct.getSearchFieldOrder()

    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        if fieldname == 'minerals':
            return self.buildContainsQuery(fieldname, field, value)
        return super(SearchInstrumentDataForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)

    class Meta:
        model = AsdDataProduct
        fields = AsdDataProduct.getSearchFormFields()


class SearchFTIRDataForm(SearchInstrumentDataForm):
    minerals = forms.CharField(widget=forms.Textarea, label="Minerals")
    
    field_order = FtirDataProduct.getSearchFieldOrder()

    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        if fieldname == 'minerals':
            return self.buildContainsQuery(fieldname, field, value)
        return super(SearchInstrumentDataForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)
    
    class Meta:
        model = FtirDataProduct
        fields = FtirDataProduct.getSearchFormFields()


class SearchBasaltImageSetForm(SearchImageSetForm):
    flight__group = forms.ModelChoiceField(GROUP_FLIGHT_MODEL.get().objects.all(), 
                                           label=settings.XGDS_PLANNER2_FLIGHT_MONIKER, 
                                           required=False,
                                           widget=autocomplete.ModelSelect2(url='/xgds_core/complete/basaltApp.BasaltGroupFlight.json/'))


class SearchBasaltNoteForm(SearchNoteForm):
    flight__group = forms.ModelChoiceField(GROUP_FLIGHT_MODEL.get().objects.all(), 
                                           label=settings.XGDS_PLANNER2_FLIGHT_MONIKER, 
                                           required=False,
                                           widget=autocomplete.ModelSelect2(url='/xgds_core/complete/basaltApp.BasaltGroupFlight.json/'))
    flight__vehicle = forms.ModelChoiceField(Vehicle.objects.all(), label='Resource', required=False)
    
    
class SearchBasaltSampleForm(SearchSampleForm):
    number = forms.IntegerField(required=False)
    year = forms.IntegerField(required=False, initial=None)
    

class SearchBasaltTrackForm(SearchTrackForm):
    timezone = forms.ChoiceField(required=False, choices=lazy(getTimezoneChoices, list)(empty=True), 
                                label='Time Zone', help_text='Required for Min/Max Time')
