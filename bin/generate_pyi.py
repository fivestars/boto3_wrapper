#!/usr/bin/env python3
import shutil
import os
from os.path import dirname, join, realpath
import boto3.Session

PROJECT_ROOT = realpath(join(dirname(__file__), '..', 'boto3_wrapper'))

def generate_all_pyi():


    pass



def clean_existing_pyi():
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if not file.endswith('.pyi'):
                continue
            file_path = join(root, file)
            print('removing %s ' % file_path)
            os.remove(file_path)

def generate_session_pyi():
    dir(boto3.Session)

    import botocore.client


def generate_resource_pyi():
    pass


def generate_client_pyi():
    pass



if __name__ == '__main__':
    generate_all_pyi()
