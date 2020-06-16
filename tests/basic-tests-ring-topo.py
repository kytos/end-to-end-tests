import sys
import pytest
import requests
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch

CONTROLLER = '127.0.0.1'
URL = 'http://%s:8181/api/kytos/mef_eline' % (CONTROLLER)

# pylint: disable=C0103
# Global Mininet variable. This is being used to keep the Mininet available on
# all test functions without declaring a test local variable.
global_net = None

def get_net():
    global global_net
    return global_net

class RingTopo( Topo ):
    "Ring topology with three switches and one host connected to each switch"

    def build( self ):
        # Create two hosts.
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )

        # Create the switches
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )

        # Add links between the switch and each host
        self.addLink( s1, h1 )
        self.addLink( s2, h2 )
        self.addLink( s3, h3 )

        # Add links between the switches
        self.addLink( s1, s2 )
        self.addLink( s2, s3 )
        self.addLink( s3, s1 )

def setup_module(mod):
    "Sets up the pytest environment"
    global global_net

    # Create an instance of our topology
    topo = RingTopo()

    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    global_net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip=CONTROLLER, port=6653),
        switch=OVSSwitch,
        autoSetMacs=True )

    # Actually start the network
    global_net.start()


def teardown_module(mod):
    "Teardown the pytest environment"
    net = get_net()

    # This function tears down the whole topology.
    net.stop()


def test_list_without_circuits(self):
    """Test if list circuits return 'no circuit stored.'."""
    api_url = URL+'/v2/evc/'
    response = requests.get(api_url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json(), {})
