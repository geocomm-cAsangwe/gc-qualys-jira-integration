# import boto3
# import json
import main
#from .logging import general_logger
import logging

#logger = general_logger(__name__)
#logger = boto3.logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def lambdaHandler(event, context):
    print('Starting lambdaHandler')
    print(event)
    print(context)
    main.process()

# un-comment this line to test locally.
# comment this line before deploying to AWS.
#lambdaHandler(f, None)