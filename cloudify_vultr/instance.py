from os import environ
from cloudify_vultr import constants
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation
from vultr import Vultr

@operation
def creation_validation(**_):
    API_KEY = environ.get(constants.VULTR_API_KEY_ENV_VAR)
    vultr = Vultr(API_KEY)
    
    instance = None
    
    # Get the Vultr SUBID
    if ctx.node.properties['resource_id']:
        instance = vultr.server_list(ctx.node.properties['resource_id'])

    # External resource doesn't exist when it's supposed to
    if ctx.node.properties['use_external_resource'] and not instance:
        raise NonRecoverableError(
            'External resource, but the supplied '
            'instance id is not in the account.')

    # External resource exists when it's not supposed to
    if not ctx.node.properties['use_external_resource'] and instance:
        raise NonRecoverableError(
            'Not external resource, but the supplied '
            'but the instance already exists.')
    
    # External resource information dump
    if ctx.node.properties['use_external_resource'] and instance:
        ctx.logger.info(
            'External resource:\n'
            ' Label:    {0}\n'
            ' SUBID:    {1}\n'
            ' OS:       {2}\n'
            ' vCPUs:    {3}\n'
            ' RAM:      {4}\n'
            ' DISK:     {5}\n'
            ' Location: {6}'
            . format(
                instance['label'],
                instance['SUBID'],
                instance['os'],
                instance['vcpu_count'],
                instance['ram'],
                instance['disk'],
                instance['location'],
            )
        )
    