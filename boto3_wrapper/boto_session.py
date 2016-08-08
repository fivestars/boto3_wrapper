#!/usr/bin/env python2.7
from __future__ import unicode_literals, print_function
import six

import functools
import logging
from pprint import pprint
# wrapp boto session into an easier usable function
import boto3
import time
from botocore.exceptions import ClientError

import boto3.helper

"""
Better boto wrapper that makes coffee
"""


class SessionWrapper(object):
    NAME_ASSO = {
        'cf': 'cloudformation',
        'r53': 'route53',
        'ec': 'elasticache',
        'cw': 'cloudwatch',
        'asg': 'autoscaling',
    }

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], boto3.Session):
            self._session = args[0]

        if kwargs.get('profile_name', None) == 'default':
            del kwargs['profile_name']

        self._session = boto3.Session(*args, **kwargs)

    def client(self, service_name, *args, **kwargs):
        service_name = self.NAME_ASSO.get(service_name, service_name)
        cli_res = self._session.client(service_name, *args, **kwargs)
        return ClientWrapper(cli_res)

    def resource(self, service_name, *args, **kwargs):
        service_name = self.NAME_ASSO.get(service_name, service_name)
        resource_res = self._session.resource(service_name, *args, **kwargs)
        return resource_res

    def res(self, service_name, *args, **kwargs):
        return self.resource(service_name, *args, **kwargs)

    def __getattr__(self, item):
        if hasattr(self._session, item):
            return getattr(self._session, item)

        if item.endswith('_res'):
            return self.res(item[:-4])
        return self.client(item)

    @property
    def helper(self):
        return boto3.helper.Helper(self)


def wrap_handle_nextToken(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        # It's not a dict, we don't know what's happens
        if not isinstance(res, six.DictType):
            return res

        res.pop('ResponseMetadata', None)

        next_token = res.pop('NextToken', None)
        keys = list(res.keys())
        only_one_key = len(list(res.keys())) == 1

        if only_one_key:
            value = res[keys[0]]
            if next_token:
                kwargs['NextToken'] = next_token
                return value + func(*args, **kwargs)
            return value
        else:
            if next_token:
                pprint(res)
                raise ValueError('Not expecting next token when muliples keys')
            return res

    return wrapper


def filter_dict(filter_dict_input):
    """
    transform a dictionnary into filters
    each values should be a list of values (even if there is only one of them
    """

    def to_list(elem):
        if isinstance(elem, list):
            return elem
        if isinstance(elem, tuple):
            return list(elem)
        return [elem]

    res = []
    for name, values in filter_dict_input.items():
        res.extend(filters(name, *to_list(values)))
    return res


def wrap_call_trottle(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for retries in range(100):
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                if e.response['Error']['Code'] != 'Throttling':
                    raise
                wait_time = (2 ** retries) * 0.1
                log = logging.getLogger(__name__)
                log.info('Trottling experienced, trying again in %s' % repr(wait_time))
                time.sleep(wait_time)
        return func(*args, **kwargs)

    return wrapper


def wrap_better_filters(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # process the Filters
        if 'Filters' in kwargs and isinstance(kwargs['Filters'], dict):
            kwargs['Filters'] = filter_dict(kwargs['Filters'])

        return func(*args, **kwargs)

    return wrapper


class ClientWrapper(object):
    def __init__(self, client):
        self._client = client

    def __getattr__(self, item):
        func = getattr(self._client, item)
        # Please keep this order
        func = wrap_call_trottle(func)
        func = wrap_handle_nextToken(func)
        func = wrap_better_filters(func)
        return func


def normalize_value(v):
    if v is False or v is True:
        return str(v).lower()
    return v


def filters(name, *values):
    return [{
        'Name': name,
        'Values': list(map(normalize_value, values)),
    }]


def to_tags(from_dict):
    """Transform tags dictionnary into whatever aws want to have"""
    return [{'Key': k, 'Value': v} for k, v in from_dict.items()]


def from_tags(tags):
    """Transform the boto way of having tags into a dictionnary"""
    return {e['Key']: e['Value'] for e in tags}
