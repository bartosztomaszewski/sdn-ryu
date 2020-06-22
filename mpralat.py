import json
import socket
from typing import Any, Set

from ryu.app.wsgi import WSGIApplication, ControllerBase, route
from ryu.base import app_manager
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet, icmp, ipv4
from ryu.ofproto import ofproto_v1_0
from webob import Response

from ryu.controller import ofp_event

icmp_manager_app = 'icmp_manager_app'


class ICMPManager(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(ICMPManager, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(ICMPRestController,
                      {icmp_manager_app: self})
        self.blocked_host_ips = set()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        pkt = packet.Packet(msg.data)

        icmp_packet = pkt.get_protocol(icmp.icmp)
        if icmp_packet:
            print("ICMP packet received")
            dest_ip = pkt.get_protocol(ipv4.ipv4).dst
            if dest_ip in self.blocked_host_ips and icmp_packet.type == icmp.ICMP_ECHO_REQUEST:
                print("IP={} on blocked IPs list. DROP the packet".format(dest_ip))
                return

        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions)
        dp.send_msg(out)


main_url = "/icmp/hosts"


class ICMPRestController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(ICMPRestController, self).__init__(req, link, data, **config)
        self.icmp_app = data[icmp_manager_app]

    @route('apimanager', main_url, methods=['GET'])
    def list_blocked_hosts(self, req, **kwargs) -> Response:
        icmp_app: ICMPManager = self.icmp_app
        return Response(
            content_type='application/json',
            charset="utf-8",
            body=json.dumps({"blocked_ips": list(icmp_app.blocked_host_ips)}, ensure_ascii=False)
        )

    @route('apimanager', main_url, methods=['POST'])
    def add_blocked_host(self, req, **kwargs: Any) -> Response:
        icmp_app: ICMPManager = self.icmp_app
        ip_addrs = _parse_request(req)
        if not ip_addrs:
            return Response(status=400)

        icmp_app.blocked_host_ips.update(ip_addrs)
        return Response(
            status=201,
            content_type='application/json',
            charset="utf-8",
            body=json.dumps({"blocked_ips": list(icmp_app.blocked_host_ips)}, ensure_ascii=False)
        )

    @route('apimanager', main_url + "/{ip_addr}", methods=['DELETE'])
    def remove_blocked_host(self, req, **kwargs: Any) -> Response:
        ip_to_delete = str(kwargs['ip_addr'])
        if not _is_valid_ip_addr(ip_to_delete):
            return Response(
                status=422,
                content_type='application/json',
                charset="utf-8",
                body=json.dumps({"errors": "Not a valid IP address"})
            )
        icmp_app: ICMPManager = self.icmp_app
        if ip_to_delete not in icmp_app.blocked_host_ips:
            return Response(
                status=404,
                content_type='application/json',
                charset="utf-8",
                body=json.dumps({"errors": "No such IP on blocked IPs list"})
            )
        icmp_app.blocked_host_ips.remove(ip_to_delete)
        return Response(status=204)


def _parse_request(req) -> Set[str]:
    ip_addrs = set()
    request_body = req.json if req.body else {}
    if (type(request_body)) == list:
        for obj in request_body:
            ip_entry = obj.get("ip")
            if ip_entry and _is_valid_ip_addr(ip_entry):
                ip_addrs.add(ip_entry)
    else:
        ip_entry = request_body.get("ip")
        if ip_entry and _is_valid_ip_addr(ip_entry):
            ip_addrs.add(ip_entry)
    return ip_addrs


def _is_valid_ip_addr(addr):
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False
