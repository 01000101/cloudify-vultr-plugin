'''These are the core lifecycle events that control
   how Vultr servers are started, configured, and terminated'''

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation
from vultr import Vultr, VultrError

def _helper_get_vultr_api_key():
    '''Gets the Vultr API key for use in all Vultr API calls'''
    return 'db.6Dw14R0lz1duhD79.o.'

def _helper_get_vultr_client():
    '''Returns a connected Vultr API client'''
    try:
        return Vultr(_helper_get_vultr_api_key())
    except VultrError:
        raise NonRecoverableError(
            'Connection to Vultr API failed. '
            'Incorrect / Invalid API key provided.')

def _helper_get_existing_server(client, resource_id):
    '''Returns a JSON object for an existing server'''
    if (not client) or (not resource_id):
        return None

    return client.server_list(resource_id)


def provision_server(client, opts):
    '''Provisions a new server on the provider'''
    _err = False

    if not opts.get('vps_plan_id'):
        _err = True
        ctx.logger.error('Missing VPSPLANID (Subscription Plan) '
                         'from the node properties')
    if not opts.get('os_id'):
        _err = True
        ctx.logger.error('Missing OSID (Image) from the node properties')
    if not opts.get('dc_id'):
        _err = True
        ctx.logger.error('Missing DCID (Location) from the node properties')

    if _err:
        NonRecoverableError('Missing required node properties')

    ctx.logger.info('\nProvisioning new server with properties:\n'
                    '{0}' . format(opts))

    try:
        result = client.server_create(
            opts.get('dc_id'),
            opts.get('vps_plan_id'),
            opts.get('os_id'),
            label=opts.get('label'),
            sshkeyid=opts.get('ssh_key_id')
        )
    except VultrError, ex:
        ctx.logger.error('Exception: {0}' . format(ex))
        RecoverableError('Could not create the server')

    return result.get('SUBID')


def server_is_active(client, sub_id):
    '''Checks if a Vultr server is active or not'''
    instance = _helper_get_existing_server(client, sub_id)

    if instance:
        if instance.get('status', '') == 'active':
            if instance.get('server_state', '') == 'ok':
                return True
    return False


@operation
def run_instances(**_):
    '''This actually creates the Vultr server'''
    client = _helper_get_vultr_client()

    cfy_agent = ctx.node.properties.get('cloudify_agent', dict())
    bs_cfy_agent = ctx.bootstrap_context.cloudify_agent
    cfy_user = cfy_agent.get('user', bs_cfy_agent.user)
    cfy_key = cfy_agent.get('key', bs_cfy_agent.agent_key_path)
    ctx.logger.info('BootstrapContext.cloudify_agent: {0}'
                    . format(vars(bs_cfy_agent)))
    ctx.logger.info('SSH User: {0}, Key: {1}'
                    . format(cfy_user, cfy_key))

    # Get the Vultr SUBID (indicating that we're using an existing resource)
    sub_id = ctx.node.properties.get('SUBID')
    if sub_id:
        ctx.logger.info('Using SUBID: {0}' . format(sub_id))

    # Get the server information (if it exists)
    server = _helper_get_existing_server(client, sub_id)
    if server:
        ctx.logger.info('Vultr server: {0}' . format(server))

    # External resource doesn't exist when it's supposed to
    if sub_id and not server:
        raise NonRecoverableError(
            'External resource, but the supplied '
            'server SUBID is not in the account.')

    # External resource exists when it's not supposed to
    if not sub_id and server:
        raise NonRecoverableError(
            'Not external resource, but the supplied '
            'but the server already exists.')

    # External resource information dump
    if sub_id:
        ctx.logger.info(
            '\nExternal resource:\n'
            ' Label:    {0}\n'
            ' SUBID:    {1}\n'
            ' OS:       {2}\n'
            ' vCPUs:    {3}\n'
            ' RAM:      {4}\n'
            ' DISK:     {5}\n'
            ' Location: {6}\n'
            ' IP:       {7}'
            . format(
                server['label'],
                server['SUBID'],
                server['os'],
                server['vcpu_count'],
                server['ram'],
                server['disk'],
                server['location'],
                server['main_ip']
            )
        )

        ctx.instance.runtime_properties['ip'] = server['main_ip']
        return
    else:
        if ctx.operation.retry_number == 0:
            extra_opts = ctx.node.properties.get('CONFIG', dict())
            # Actually request the server be created
            sub_id = provision_server(
                client,
                {
                    'vps_plan_id': ctx.node.properties.get('VPSPLANID'),
                    'os_id': ctx.node.properties.get('OSID'),
                    'dc_id': ctx.node.properties.get('DCID'),
                    'label': extra_opts.get('label'),
                    'ssh_key_id': extra_opts.get('SSHKEYID')
                }
            )

            if not sub_id:
                NonRecoverableError(
                    'Unable to provision a new server. '
                    'Provider did not issue a SUBID.'
                )

            ctx.instance.runtime_properties['SUBID'] = sub_id
        else:
            sub_id = ctx.instance.runtime_properties.get('SUBID')
            if server_is_active(client, sub_id):
                ctx.logger.info('Server has been provisioned '
                                'with SUBID {0}' . format(sub_id))

                server = _helper_get_existing_server(client, sub_id)
                ctx.instance.runtime_properties['ip'] = \
                    server.get('main_ip')

                ctx.logger.info('Server Information:\n{0}' . format(server))
                ctx.logger.info('Runtime properties:\n{0}'
                                . format(ctx.instance.runtime_properties))
                ctx.logger.info('Properties:\n{0}'
                                . format(ctx.node.properties))
                return

        return ctx.operation.retry(
            message='Waiting for server {0} to be '
            'added to your account.' . format(sub_id))


@operation
def stop(**_):
    '''Terminates all existing Vultr servers'''
    client = _helper_get_vultr_client()

    sub_id = ctx.instance.runtime_properties.get('SUBID')
    if not sub_id:
        return

    ctx.logger.info('Attempting to destroy server SUBID={0}'
                    . format(sub_id))

    try:
        res = client.server_destroy(sub_id)
        ctx.logger.info('Result: {0}' . format(res))
    except VultrError, ex:
        ctx.logger.error('Exception: {0}' . format(ex))

        return ctx.operation.retry(
            message='Waiting to destroy server {0}. '
            '(note: you cannot destroy Vultr servers within '
            '5 minutes of creation)'
            . format(sub_id))
