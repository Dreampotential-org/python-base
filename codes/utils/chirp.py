import logging as CHIRP

# THANK YOU Meylor for this :)
CHIRP.basicConfig(
    level=CHIRP.DEBUG,
    format='[%(filename)s:%(funcName)s():line %(lineno)s] %(levelname)s: %(message)s')

CHIRP.getLogger('boto').setLevel(CHIRP.CRITICAL)
CHIRP.getLogger('boto3').setLevel(CHIRP.CRITICAL)
CHIRP.getLogger('botocore').setLevel(CHIRP.CRITICAL)
CHIRP.getLogger('s3transfer').setLevel(CHIRP.CRITICAL)
CHIRP.getLogger("googleapiclient.discovery").setLevel(CHIRP.WARNING)
CHIRP.getLogger("requests").setLevel(CHIRP.WARNING)
CHIRP.getLogger("selenium.webdriver.remote.remote_connection").setLevel(
    CHIRP.WARNING)
CHIRP.getLogger("urllib3").setLevel(CHIRP.WARNING)
