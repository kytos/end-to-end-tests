from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
import mininet.clean
from mock import patch
import time
import os


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


# You can run any of the topologies above by doing:
# mn --custom tests/helpers.py --topo ring --controller=remote,ip=127.0.0.1
topos = {
    'ring': (lambda: RingTopo()),
    'ring4': (lambda: Ring4Topo()),
}


class NetworkTest:
    def __init__(self, controller_ip, topo_name='ring'):
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

    def start(self):
        self.net.start()
        self.start_controller(clean_config=True)

    def start_controller(self, clean_config=False, enable_all=False, del_flows=False):
        # Restart kytos and check if the napp is still disabled
        try:
            os.system('pkill kytosd')
            # with open('/var/run/kytos/kytosd.pid', "r") as f:
            #    pid = int(f.read())
            #    os.kill(pid, signal.SIGTERM)
            time.sleep(5)
        except Exception as e:
            print("FAIL restarting kytos -- %s" % e)

        if clean_config:
            # TODO: config is defined at NAPPS_DIR/kytos/storehouse/settings.py 
            # and NAPPS_DIR is defined at /etc/kytos/kytos.conf
            os.system('rm -rf /var/tmp/kytos/storehouse')

        if clean_config or del_flows:
            # Remove any installed flow
            for sw in self.net.switches:
                sw.dpctl('del-flows')

        daemon = 'kytosd'
        if enable_all:
            daemon += ' -E'
        os.system(daemon)

    def wait_switches_connect(self):
        max_wait = 0
        while any(not sw.connected() for sw in self.net.switches):
            time.sleep(1)
            max_wait += 1
            if max_wait > 30:
                raise Exception('Timeout: timed out waiting switches reconnect')

    def restart_kytos_clean(self):
        self.start_controller(clean_config=True, enable_all=True)
        self.wait_switches_connect()

    def stop(self):
        self.net.stop()
        mininet.clean.cleanup()
