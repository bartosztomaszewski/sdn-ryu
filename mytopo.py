import pdb
from mininet.topo import Topo

class Project(Topo):
        def __init__(self):

                Topo.__init__(self)

                switch = self.addSwitch('s1')
        
                for h in range(4):
                        host = self.addHost('h%s' % (h + 1))
                        self.addLink(host, switch)

topos = { 'project': (lambda: Project() ) }

