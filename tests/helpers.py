from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
import mininet.clean

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

class TestNetwork():
    def __init__(self, controller_ip):
        # Create an instance of our topology
        topo = RingTopo()

        # Create a network based on the topology using OVS and controlled by
        # a remote controller.
        self.net = Mininet(
            topo=topo,
            controller=lambda name: RemoteController(
                                        name, ip=controller_ip, port=6653),
            switch=OVSSwitch,
            autoSetMacs=True )

    def start(self):
        self.net.start()

    def stop(self):
        self.net.stop()
        mininet.clean.cleanup()
