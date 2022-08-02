from mininet.net import Mininet
from mininet.topo import Topo, LinearTopo
from mininet.node import RemoteController, OVSSwitch
import mininet.clean
from mock import patch
import time
import os
import requests

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


class AmlightTopo(Topo):
    """Amlight Topology."""
    def build(self):
        # Add switches
        Ampath1 = self.addSwitch('Ampath1', listenPort=6601, dpid='0000000000000011')
        Ampath2 = self.addSwitch('Ampath2', listenPort=6602, dpid='0000000000000012')
        SouthernLight2 = self.addSwitch('SoL2', listenPort=6603, dpid='0000000000000013')
        SanJuan = self.addSwitch('SanJuan', listenPort=6604, dpid='0000000000000014')
        AndesLight2 = self.addSwitch('AL2', listenPort=6605, dpid='0000000000000015')
        AndesLight3 = self.addSwitch('AL3', listenPort=6606, dpid='0000000000000016')
        Ampath3 = self.addSwitch('Ampath3', listenPort=6608, dpid='0000000000000017')
        Ampath4 = self.addSwitch('Ampath4', listenPort=6609, dpid='0000000000000018')
        Ampath5 = self.addSwitch('Ampath5', listenPort=6610, dpid='0000000000000019')
        Ampath7 = self.addSwitch('Ampath7', listenPort=6611, dpid='0000000000000020')
        JAX1 = self.addSwitch('JAX1', listenPort=6612, dpid='0000000000000021')
        JAX2 = self.addSwitch('JAX2', listenPort=6613, dpid='0000000000000022')
        # add hosts
        h1 = self.addHost('h1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', mac='00:00:00:00:00:06')
        h7 = self.addHost('h7', mac='00:00:00:00:00:07')
        h8 = self.addHost('h8', mac='00:00:00:00:00:08')
        h9 = self.addHost('h9', mac='00:00:00:00:00:09')
        h10 = self.addHost('h10', mac='00:00:00:00:00:0A')
        h11 = self.addHost('h11', mac='00:00:00:00:00:0B')
        h12 = self.addHost('h12', mac='00:00:00:00:00:0C')
        # Add links
        self.addLink(Ampath1, Ampath2, port1=1, port2=1)
        self.addLink(Ampath1, SouthernLight2, port1=2, port2=2)
        self.addLink(Ampath1, SouthernLight2, port1=3, port2=3)
        self.addLink(Ampath2, AndesLight2, port1=4, port2=4)
        self.addLink(SouthernLight2, AndesLight3, port1=5, port2=5)
        self.addLink(AndesLight3, AndesLight2, port1=6, port2=6)
        self.addLink(AndesLight2, SanJuan, port1=7, port2=7)
        self.addLink(SanJuan, Ampath2, port1=8, port2=8)
        self.addLink(Ampath1, Ampath3, port1=9, port2=9)
        self.addLink(Ampath2, Ampath3, port1=10, port2=10)
        self.addLink(Ampath1, Ampath4, port1=11, port2=11)
        self.addLink(Ampath2, Ampath5, port1=12, port2=12)
        self.addLink(Ampath4, Ampath5, port1=13, port2=13)
        self.addLink(Ampath4, JAX1, port1=14, port2=14)
        self.addLink(Ampath5, JAX2, port1=15, port2=15)
        self.addLink(Ampath4, Ampath7, port1=16, port2=16)
        self.addLink(Ampath7, SouthernLight2, port1=17, port2=17)
        self.addLink(JAX1, JAX2, port1=18, port2=18)
        self.addLink(h1, Ampath1, port1=1, port2=50)
        self.addLink(h2, Ampath2, port1=1, port2=51)
        self.addLink(h3, SouthernLight2, port1=1, port2=52)
        self.addLink(h4, SanJuan, port1=1, port2=53)
        self.addLink(h5, AndesLight2, port1=1, port2=54)
        self.addLink(h6, AndesLight3, port1=1, port2=55)
        self.addLink(h7, Ampath3, port1=1, port2=56)
        self.addLink(h8, Ampath4, port1=1, port2=57)
        self.addLink(h9, Ampath5, port1=1, port2=58)
        self.addLink(h10, Ampath7, port1=1, port2=59)
        self.addLink(h11, JAX1, port1=1, port2=60)
        self.addLink(h12, JAX2, port1=1, port2=61)

class RingTopo(Topo):
    """Ring topology with three switches
    and one host connected to each switch"""

    def build(self):
        # Create two hosts
        h11 = self.addHost('h11', ip='0.0.0.0')
        h12 = self.addHost('h12', ip='0.0.0.0')
        h2 = self.addHost('h2', ip='0.0.0.0')
        h3 = self.addHost('h3', ip='0.0.0.0')

        # Create the switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Add links between the switch and each host
        self.addLink(s1, h11)
        self.addLink(s1, h12)
        self.addLink(s2, h2)
        self.addLink(s3, h3)

        # Add links between the switches
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s1)


class Ring4Topo(Topo):
    """Create a network from semi-scratch with multiple controllers."""

    def build(self):
        # ("*** Creating switches\n")
        s1 = self.addSwitch('s1', listenPort=6601, dpid="1")
        s2 = self.addSwitch('s2', listenPort=6602, dpid="2")
        s3 = self.addSwitch('s3', listenPort=6603, dpid="3")
        s4 = self.addSwitch('s4', listenPort=6604, dpid="4")

        # ("*** Creating hosts\n")
        hosts1 = [self.addHost('h%d' % n) for n in (1, 2)]
        hosts2 = [self.addHost('h%d' % n) for n in (3, 4)]
        hosts3 = [self.addHost('h%d' % n) for n in (5, 6)]
        hosts4 = [self.addHost('h%d' % n) for n in (7, 8)]

        # ("*** Creating links\n")
        for h in hosts1:
            self.addLink(s1, h)
        for h in hosts2:
            self.addLink(s2, h)

        self.addLink(s1, s2)
        self.addLink(s2, s3)

        for h in hosts3:
            self.addLink(s3, h)
        for h in hosts4:
            self.addLink(s4, h)

        self.addLink(s3, s4)
        self.addLink(s4, s1)

class Looped(Topo):
    """ Network with two switches
    and a loop in one switch."""

    def build(self):
        "Create custom topo."

        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")

        self.addLink(s1, s1, port1=1, port2=2)
        self.addLink(s1, s1, port1=4, port2=5)
        self.addLink(s1, s2, port1=3, port2=1)

class MultiConnectedTopo(Topo):
    """Multiply connected network topology six
    and one host connected to each switch """
    def build(self):
        # Create hosts
        h1 = self.addHost('h1', ip='0.0.0.0')
        h2 = self.addHost('h2', ip='0.0.0.0')
        h3 = self.addHost('h3', ip='0.0.0.0')
        h4 = self.addHost('h4', ip='0.0.0.0')
        h5 = self.addHost('h5', ip='0.0.0.0')
        h6 = self.addHost('h6', ip='0.0.0.0')
        # Create the switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        # Add links between the switch and each host
        self.addLink(s1, h1)
        self.addLink(s2, h2)
        self.addLink(s3, h3)
        self.addLink(s4, h4)
        self.addLink(s5, h5)
        self.addLink(s6, h6)
        # Add links between the switches
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s4, s5)
        self.addLink(s5, s6)
        self.addLink(s1, s6)
        self.addLink(s2, s6)
        self.addLink(s3, s6)
        self.addLink(s4, s6)


# You can run any of the topologies above by doing:
# mn --custom tests/helpers.py --topo ring --controller=remote,ip=127.0.0.1
topos = {
    'ring': (lambda: RingTopo()),
    'ring4': (lambda: Ring4Topo()),
    'amlight': (lambda: AmlightTopo()),
    'linear10': (lambda: LinearTopo(10)),
    'multi': (lambda: MultiConnectedTopo()),
    'looped': (lambda: Looped()),
}


def mongo_client(
    host_seeds=os.environ.get("MONGO_HOST_SEEDS"),
    username=os.environ.get("MONGO_USERNAME"),
    password=os.environ.get("MONGO_PASSWORD"),
    database=os.environ.get("MONGO_DBNAME"),
    connect=False,
    retrywrites=True,
    retryreads=True,
    readpreference='primaryPreferred',
    maxpoolsize=int(os.environ.get("MONGO_MAX_POOLSIZE", 20)),
    minpoolsize=int(os.environ.get("MONGO_MIN_POOLSIZE", 10)),
    **kwargs,
) -> MongoClient:
    """mongo_client."""
    return MongoClient(
        host_seeds.split(","),
        username=username,
        password=password,
        connect=False,
        authsource=database,
        retrywrites=retrywrites,
        retryreads=retryreads,
        readpreference=readpreference,
        maxpoolsize=maxpoolsize,
        minpoolsize=minpoolsize,
        **kwargs,
    )


class NetworkTest:
    def __init__(
        self,
        controller_ip,
        topo_name="ring",
        db_client=mongo_client,
        db_client_options=None,
    ):
        # Create an instance of our topology
        mininet.clean.cleanup()

        # Create a network based on the topology using
        # OVS and controlled by a remote controller
        patch('mininet.util.fixLimits', side_effect=None)
        self.net = Mininet(
            topo=topos.get(topo_name, (lambda: RingTopo()))(),
            controller=lambda name: RemoteController(
                name, ip=controller_ip, port=6653),
            switch=OVSSwitch,
            autoSetMacs=True)
        db_client_kwargs = db_client_options or {}
        db_name = db_client_kwargs.get("database") or os.environ.get("MONGO_DBNAME")
        self.db_client = db_client(**db_client_kwargs)
        self.db_name = db_name
        self.db = self.db_client[self.db_name]

    def start(self):
        self.net.start()
        self.start_controller(clean_config=True)

    def drop_database(self):
        """Drop database."""
        self.db_client.drop_database(self.db_name)

    def start_controller(self, clean_config=False, enable_all=False,
                         del_flows=False, port=None, database='mongodb'):
        # Restart kytos and check if the napp is still disabled
        try:
            os.system('pkill kytosd')
            # with open('/var/run/kytos/kytosd.pid', "r") as f:
            #    pid = int(f.read())
            #    os.kill(pid, signal.SIGTERM)
            time.sleep(5)
            if os.path.exists('/var/run/kytos/kytosd.pid'):
                raise Exception("Kytos pid still exists.")
        except Exception as e:
            print("FAIL to stop kytos after 5 seconds -- %s. Force stop!" % e)
            os.system('pkill -9 kytosd')
            os.system('rm -f /var/run/kytos/kytosd.pid')

        if clean_config and database:
            try:
                self.drop_database()
            except ServerSelectionTimeoutError as exc:
                print(f"FAIL to drop database. {str(exc)}")

        if clean_config or del_flows:
            # Remove any installed flow
            for sw in self.net.switches:
                sw.dpctl('del-flows')

        daemon = 'kytosd'
        if database:
            daemon += f' --database {database}'
        if port:
            daemon += ' --port %s' % port
        if enable_all:
            daemon += ' -E'
        os.system(daemon)

        self.wait_controller_start()

    def wait_controller_start(self):
        """Wait until controller starts according to core/status API."""
        wait_count = 0
        while wait_count < 60:
            try:
                response = requests.get('http://127.0.0.1:8181/api/kytos/core/status/', timeout=1)
                assert response.json()['response'] == 'running'
                break
            except:
                time.sleep(0.5)
                wait_count += 0.5
        else:
            msg = 'Timeout while starting Kytos controller.'
            raise Exception(msg)

    def wait_switches_connect(self):
        max_wait = 0
        while any(not sw.connected() for sw in self.net.switches):
            time.sleep(1)
            max_wait += 1
            if max_wait > 30:
                status = [(sw.name, sw.connected()) for sw in self.net.switches]
                raise Exception('Timeout: timed out waiting switches reconnect. Status %s' % status)

    def restart_kytos_clean(self):
        self.start_controller(clean_config=True, enable_all=True)
        self.wait_switches_connect()

    def config_all_links_up(self):
        for link in self.net.links:
            self.net.configLinkStatus(
                link.intf1.node.name,
                link.intf2.node.name,
                "up"
            )

    def stop(self):
        self.net.stop()
        mininet.clean.cleanup()
