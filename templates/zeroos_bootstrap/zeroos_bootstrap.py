from gevent import sleep

from js9 import j
from zerorobot.template.base import TemplateBase

NODE_TEMPLATE_UID = "github.com/jumpscale/0-robot/node/0.0.1"


class ZeroosBootstrap(TemplateBase):

    version = '0.0.1'
    template_name = "zeroos_bootstrap"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['zerotierInstance']:
            raise RuntimeError("no zerotier instance specified")

        self.zt = j.clients.zerotier.get(self.data['zerotierInstance'])
        # start recurring action
        self.recurring_action('bootstrap', 10)

    def bootstrap(self):

        # make sure we can find a robot that can create the node service
        try:
            self.api.get_robot(NODE_TEMPLATE_UID)
        except KeyError:
            self.logger.error("can't find a robot that can create node service. node discovery can't proceed")
            return

        netid = self.data['zerotierNetID']

        resp = self.zt.client.network.listMembers(netid)
        members = resp.json()

        for member in members:
            try:
                self._add_node(member)
            except Exception as err:
                self.logger.error(str(err))
                self._unauthorize_member(member)

    def _authorize_member(self, member):
        self.logger.info("authorize new member %s", member['nodeId'])
        netid = self.data['zerotierNetID']
        member['config']['authorized'] = True
        self.zt.client.network.updateMember(member, member['nodeId'], netid)

    def _unauthorize_member(self, member):
        self.logger.info("unauthorize new member %s", member['nodeId'])
        netid = self.data['zerotierNetID']
        member['config']['authorized'] = False
        self.zt.client.network.updateMember(member, member['nodeId'], netid)

    def _wait_member_ip(self, member):
        self.logger.info("wait ip for member %s", member['nodeId'])
        netid = self.data['zerotierNetID']

        resp = self.zt.client.network.getMember(member['nodeId'], netid)
        member = resp.json()
        while len(member['config']['ipAssignments']) <= 0:
            sleep(1)
            resp = self.zt.client.network.getMember(member['nodeId'], netid)
            member = resp.json()
        zerotier_ip = member['config']['ipAssignments'][0]
        return zerotier_ip

    def _get_node_sal(self, ip):
        if 'bootstrap' in j.clients.zero_os.items:
            del j.clients.zero_os.items['bootstrap']

        data = {
            'host': ip,
            'port': 6379,
            'password_': "",
            'db': 0,
            'ssl': True,
            'timeout': 120,
        }
        # ensure client config
        cl = j.clients.zero_os.get(
            instance="bootstrap",
            data=data,
            create=True,
            die=True)
        cl.config._data.update(data)
        cl.config.save()
        # get a node object from the zero-os SAL
        node = j.clients.zero_os.sal.node_get("bootstrap")
        return node

    def _add_node(self, member):
        if not member['online'] or member['config']['authorized']:
            return

        netid = self.data['zerotierNetID']

        # authorized new member
        self._authorize_member(member)

        # get assigned ip of this member
        zerotier_ip = self._wait_member_ip(member)

        # do hardwarechecks -  NOT IMPLEMENTED YET
        # for prod in service.producers.get('hardwarecheck', []):
        #     prod.executeAction('check', args={'ipaddr': zerotier_ip,
        #                                       'node_id': member['nodeId'],
        #                                       'jwt': get_jwt_token(service.aysrepo)})

        # create client configuration for that node
        node = self._get_node_sal(zerotier_ip)

        # test if we can connect to the new member
        # node_client = j.clients.zero_os._get_manual(host=zerotier_ip, timeout=30, testConnectionAttempts=0)  # , password=get_jwt_token(service.aysrepo))
        for _ in range(5):
            try:
                self.logger.info("connection to g8os with IP: %s", zerotier_ip)
                node.client.ping()
                break
            except:
                continue
        else:
            raise RuntimeError("can't connect, unauthorize member IP: {}".format(zerotier_ip))

        # connection succeeded, set the hostname of the node to zerotier member
        name = node.name
        member['name'] = name
        member['description'] = node.client.info.os().get('hostname', '')
        member['config']['authorized'] = True  # make sure we don't unauthorize
        self.zt.client.network.updateMember(member, member['nodeId'], netid)

        # TODO: this should be configurable
        results = self.api.services.find(template_name='node', name=name)
        if len(results) > 0:
            # the node already exists
            self.logger.info("service for node %s already exists, updating model", name)
            node = self.api.services.names[name]
            node.schedule_action('update_data', args={'d': {'redisAddr': zerotier_ip}})
            return

        # create and install the node.zero-os service
        if self.data['wipedisks']:
            self.logger.info("wipe disk")
            node.wipedisks()

        # NETWORK NOT IMPLEMENTED YET
        # networks = [n.name for n in service.producers.get('network', [])]

        hostname = node.client.info.os()['hostname']
        if hostname == 'zero-os':
            hostname = 'zero-os-%s' % name

        data = {
            'id': name,
            'status': 'running',
            # 'networks': networks,
            'hostname': hostname,
            'redisAddr': zerotier_ip,
        }
        self.logger.info("create node.zero-os service {}".format(name))
        node_service = self.api.services.create(NODE_TEMPLATE_UID, name, data=data)
        task_install = node_service.schedule_action('install')

        # TODO: improve this flow
        def cleanup():
            # node_service.schedule_action('delete').wait(60)
            node_service.delete()

        try:
            task_install.wait(60)
        except TimeoutError as err:
            self.logger.error("node %s took too long to install", name)
            cleanup()
            raise err
        if task_install.state == 'error':
            cleanup()
            raise RuntimeError("unexpected error during installation of node %s: %s" % (name, task_install.eco.errormessage))

            # do ERP registrations - NOT IMPLEMENTED YET
            # for prod in service.producers.get('erp_registration', []):
            #     prod.executeAction('register', args={'node_id': name, 'zerotier_address': member['nodeId']})

    def delete_node(self, redis_addr):
        """
        this method will be called from the node.zero-os to remove the node from zerotier
        """
        netid = self.data['zerotierNetID']
        resp = self.zt.client.network.listMembers(netid)
        members = resp.json()

        for member in members:
            if redis_addr in member['config']['ipAssignments']:
                self._unauthorize_member(member)
