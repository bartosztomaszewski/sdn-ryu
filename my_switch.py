from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
import json

class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        #Check if ICMP
        pkt = packet.Packet(msg.data)
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        
        if icmp_pkt:
            
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            recevier_ipv4 = ipv4_pkt.dst
            is_blocked = False
            
            try:
                with open ("data.json", "r") as f:
                    data = json.loads(f.read())
                    
                    for ip in data.values():
                        if ip == recevier_ipv4:
                            is_blocked = True                
            except IOError:
                pass
            
            if is_blocked == True and icmp_pkt.type == icmp.ICMP_ECHO_REQUEST: #ICMP_ECHO_REQUEST or 8
                
                #self.logger.info("This host is prohibited")
                pkt_data = self.create_icmp_unrachalbe_packet(pkt, ipv4_pkt)
                             
                self.send_packet(ofp_parser, ofp.OFPP_FLOOD, dp, ofp.OFP_NO_BUFFER, ofp.OFPP_CONTROLLER, pkt_data)
                return
                
            #else:
                #self.logger.info("---Accepted ICMP packet---")
        
        
        self.send_packet(ofp_parser, ofp.OFPP_FLOOD, dp, msg.buffer_id, msg.in_port, 0)
        
        
    def create_icmp_unrachalbe_packet(self, pkt, ipv4_pkt):
        
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(dst=eth_pkt.src, ethertype=eth_pkt.ethertype)) #src hardware addr is default = '00.00.00.00.00.00.00.00'
        pkt.add_protocol(ipv4.ipv4(src=ipv4_pkt.dst, dst=ipv4_pkt.src, proto=ipv4_pkt.proto))

        pkt_payload = icmp.dest_unreach()
        pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_DEST_UNREACH, code=icmp.ICMP_HOST_UNREACH_CODE, csum=0, data=pkt_payload))

        pkt.serialize()
        return pkt.data
    
    def send_packet(self, ofp_parser, port, dp, buffer_id, in_port, data):
        
        actions = [ofp_parser.OFPActionOutput(port)]
        if data==0:
            out = ofp_parser.OFPPacketOut(datapath=dp, buffer_id=buffer_id, in_port=in_port, actions=actions)
        else:
            out = ofp_parser.OFPPacketOut(datapath=dp, buffer_id=buffer_id, in_port=in_port, actions=actions, data=data)
        dp.send_msg(out)
