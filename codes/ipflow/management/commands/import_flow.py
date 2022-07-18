import os
from django.core.management.base import BaseCommand
import pandas

from ipflow.models import FlowLog



class Command(BaseCommand):
    help = 'Import address extra'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("here is the start")

        # Setting path for laptop_iwlist_output file  start
        module_dir = os.path.dirname(__file__)
        # full path to laptop_iwlist_output.
        file_path = os.path.abspath(os.path.join(
            module_dir, '..', '..', 'data'))

        print(file_path)
        # here we need to read data file in this repo.
        # each line looks like this:

        # for line in file:
        #  create a new FlowLog.
        # XXX we need to make sure we do not save duplicate.
        # we need to integrate with s3 to get flow logs
        # first step is building parser for file...

        # now look up information for source_ip and store all
        # info in FlowLow