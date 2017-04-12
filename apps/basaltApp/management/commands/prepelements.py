# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
# __END_LICENSE__
import os
import traceback
from geocamUtil.management import commandUtil
from geocamUtil.management.commandUtil import getSiteDir, dosys
from basaltApp.models import Element

from adaptor.model import CsvDbModel

class ElementCsvModel(CsvDbModel):

    class Meta:
        dbModel = Element
        delimiter = "\t"

class Command(commandUtil.PathCommand):
    help = 'Load elements.csv into basaltApp_elements table'

    def handle(self, *args, **options):
        try:
            elementCount = Element.objects.count()
            if elementCount == 0:
                print "Loading elements.csv"
                siteDir = getSiteDir()
                elementsPath = os.path.join(siteDir, 'apps', 'basaltApp', 'fixtures', 'elements.csv')
                my_csv_list = ElementCsvModel.import_data(data = open(elementsPath))
                elementCount = Element.objects.count()
                print 'loaded %d elements ' % elementCount
            else:
                print 'elements already loaded'
                
#                 dosys('mysql -e \'load data infile "%s" into table basaltApp_element fields terminated by "\t";\'' % elementsPath)
        except:
            traceback.print_exc()
            pass
