#!/bin/bash

KYTOS_URL="http://127.0.0.1:8181/api"
TOPOLOGY_API="kytos/topology/v3"
LLDP_API="kytos/of_lldp/v1"

http_post() {
	URL_PATH="$1"
	BODY="$2"

	echo "--> POST $URL_PATH $BODY" 1>&2
	curl -H 'Content-Type: application/json' -X POST $KYTOS_URL/$URL_PATH -d "$BODY"
}

http_get() {
	URL_PATH="$1"
	echo "--> GET $URL_PATH" 1>&2
	curl -s $KYTOS_URL/$URL_PATH
}

set_switch_enable_metadata() {
	DPID="$1"
	DATA="$2"

	if [ $(echo -n $DPID | wc -c) -eq 2 ]; then
		DPID=00:00:00:00:00:00:00:$DPID
	fi

	http_post $TOPOLOGY_API/switches/$DPID/enable
	http_post $TOPOLOGY_API/switches/$DPID/metadata "$DATA"
}

disable_lldp_all_interfaces() {
	ALL_INTERFACES=$(http_get $LLDP_API/interfaces)

	http_post $LLDP_API/interfaces/disable "$ALL_INTERFACES"
}

set_interface_enable_metadata() {
	IFACEID="$1"
	DATA="$2"

	http_post $TOPOLOGY_API/interfaces/$IFACEID/enable
	http_post $TOPOLOGY_API/interfaces/$IFACEID/metadata "$DATA"
}

set_interface_enable_lldp_metadata() {
	IFACEID="$1"
	DATA="$2"

	http_post $TOPOLOGY_API/interfaces/$IFACEID/enable
	http_post $TOPOLOGY_API/interfaces/$IFACEID/metadata "$DATA"
	http_post $LLDP_API/interfaces/enable "{\"interfaces\": [\"$IFACEID\"]}"
}

set_link_enable_metadata() {
	LINKID="$1"
	DATA="$2"

	http_post $TOPOLOGY_API/links/$LINKID/enable
	http_post $TOPOLOGY_API/links/$LINKID/metadata "$DATA"
}

wait_on() {
	TYPE=$1
	NUMBER=$2

	i=0
	while [ $i -lt 300 ]; do
		if [ $(curl -s $KYTOS_URL/$TOPOLOGY_API/$TYPE | jq -r ".$TYPE[].id" | wc -l) -eq $NUMBER ]; then
			break
		fi
		sleep 1
		i=$(($i+1))
	done
	if [ $i -eq 300 ]; then
		echo "ERROR: missing $TYPE. Current $TYPE:"
		curl -s $KYTOS_URL/$TOPOLOGY_API/$TYPE | jq -r ".$TYPE[].id"
		exit 1
	fi
}

#############################
# Setup switches
#############################
wait_on switches 12
set_switch_enable_metadata 11 '{"node_name": "Ampath1",      "lat":  "26", "lng": "-70", "address": "Datacenter MI1",  "description": "MIA-MI1-SW01"}'
set_switch_enable_metadata 12 '{"node_name": "Ampath2",      "lat":  "26", "lng": "-90", "address": "Datacenter MI1",  "description": "MIA-MI1-SW02"}'
set_switch_enable_metadata 13 '{"node_name": "SoL2",         "lat": "-23", "lng": "-46", "address": "Datacenter SP4",  "description": "SAO-SP4-SW01"}'
set_switch_enable_metadata 14 '{"node_name": "SanJuan",      "lat":  "17", "lng": "-80", "address": "Datacenter H787", "description": "SJU-H787-SW01"}'
set_switch_enable_metadata 15 '{"node_name": "AL2",          "lat":  "33", "lng": "-75", "address": "Datacenter CLK",  "description": "SCL-CLK-SW01"}'
set_switch_enable_metadata 16 '{"node_name": "AL3",          "lat":  "33", "lng": "-68", "address": "Datacenter CLK",  "description": "SCL-CLK-SW02"}'
set_switch_enable_metadata 17 '{"node_name": "Ampath3",      "lat":  "30", "lng": "-81", "address": "Datacenter MI1",  "description": "MIA-MI1-SW04"}'
set_switch_enable_metadata 18 '{"node_name": "Ampath4",      "lat":  "35", "lng": "-90", "address": "Datacenter MI1",  "description": "MIA-MI1-SW04"}'
set_switch_enable_metadata 19 '{"node_name": "Ampath5",      "lat":  "35", "lng": "-70", "address": "Datacenter MI1",  "description": "MIA-MI1-SW05"}'
set_switch_enable_metadata 20 '{"node_name": "Ampath7",      "lat":  "30", "lng": "-60", "address": "Datacenter MI3",  "description": "BCT-MI3-SW02"}'
set_switch_enable_metadata 21 '{"node_name": "JAX1",         "lat":  "45", "lng": "-70", "address": "Datacenter CLK",  "description": "JAX-CLK-SW01"}'

#############################
# Setup interfaces
#############################
disable_lldp_all_interfaces
set_interface_enable_metadata 00:00:00:00:00:00:00:11:50 '{"mtu": 9000, "port_name": "h1-eth1:Ampath1-eth50"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:12:51 '{"mtu": 9000, "port_name": "h2-eth1:Ampath2-eth51"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:13:52 '{"mtu": 9000, "port_name": "h3-eth1:SoL2-eth52"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:14:53 '{"mtu": 9000, "port_name": "h4-eth1:SanJuan-eth53"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:15:54 '{"mtu": 9000, "port_name": "h5-eth1:AL2-eth54"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:16:55 '{"mtu": 9000, "port_name": "h6-eth1:AL3-eth55"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:17:56 '{"mtu": 9000, "port_name": "h7-eth1:Ampath3-eth56"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:18:57 '{"mtu": 9000, "port_name": "h8-eth1:Ampath4-eth57"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:19:58 '{"mtu": 9000, "port_name": "h9-eth1:Ampath5-eth58"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:20:59 '{"mtu": 9000, "port_name": "h10-eth1:Ampath7-eth59"}'
set_interface_enable_metadata 00:00:00:00:00:00:00:21:60 '{"mtu": 9000, "port_name": "h11-eth1:JAX1-eth60"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:11:1  '{"mtu": 9000, "port_name": "Interface-11:1"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:11:11 '{"mtu": 9000, "port_name": "Interface-11:11"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:11:2  '{"mtu": 9000, "port_name": "Interface-11:2"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:11:3  '{"mtu": 9000, "port_name": "Interface-11:3"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:11:9  '{"mtu": 9000, "port_name": "Interface-11:9"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:12:1  '{"mtu": 9000, "port_name": "Interface-12:1"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:12:10 '{"mtu": 9000, "port_name": "Interface-12:10"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:12:12 '{"mtu": 9000, "port_name": "Interface-12:12"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:12:4  '{"mtu": 9000, "port_name": "Interface-12:4"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:12:8  '{"mtu": 9000, "port_name": "Interface-12:8"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:13:17 '{"mtu": 9000, "port_name": "Interface-13:17"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:13:2  '{"mtu": 9000, "port_name": "Interface-13:2"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:13:3  '{"mtu": 9000, "port_name": "Interface-13:3"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:13:5  '{"mtu": 9000, "port_name": "Interface-13:5"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:14:7  '{"mtu": 9000, "port_name": "Interface-14:7"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:14:8  '{"mtu": 9000, "port_name": "Interface-14:8"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:15:4  '{"mtu": 9000, "port_name": "Interface-15:4"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:15:6  '{"mtu": 9000, "port_name": "Interface-15:6"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:15:7  '{"mtu": 9000, "port_name": "Interface-15:7"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:16:5  '{"mtu": 9000, "port_name": "Interface-16:5"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:16:6  '{"mtu": 9000, "port_name": "Interface-16:6"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:17:10 '{"mtu": 9000, "port_name": "Interface-17:10"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:17:9  '{"mtu": 9000, "port_name": "Interface-17:9"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:18:11 '{"mtu": 9000, "port_name": "Interface-18:11"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:18:13 '{"mtu": 9000, "port_name": "Interface-18:13"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:18:14 '{"mtu": 9000, "port_name": "Interface-18:14"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:18:16 '{"mtu": 9000, "port_name": "Interface-18:16"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:19:12 '{"mtu": 9000, "port_name": "Interface-19:12"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:19:13 '{"mtu": 9000, "port_name": "Interface-19:13"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:19:15 '{"mtu": 9000, "port_name": "Interface-19:15"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:20:16 '{"mtu": 9000, "port_name": "Interface-20:16"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:20:17 '{"mtu": 9000, "port_name": "Interface-20:17"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:21:14 '{"mtu": 9000, "port_name": "Interface-21:14"}'
set_interface_enable_lldp_metadata 00:00:00:00:00:00:00:21:18 '{"mtu": 9000, "port_name": "Interface-21:18"}'


#############################
# Setup links
#############################
# curl -s http://127.0.0.1:8181/api/kytos/topology/v3/links | jq -r '.links[] | .id + " \"" +(.endpoint_a.name|tostring) + "--" + (.endpoint_b.name|tostring) + "\""'
wait_on links 18
set_link_enable_metadata 1e7e531ae50f419b1d35d311a66351d997ea567348b691d8dccdc639e1f8340a '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath4-eth11--Ampath1-eth11"}'
set_link_enable_metadata 21c046f5eb9fbf577701974e207c2fd2ccd8cc4b91fae77ad396924b79c48483 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "AL2-eth6--AL3-eth6"}'
set_link_enable_metadata 26ba6acadb3e4f6b7a103fea28080d6c4d5ab0f78499d0d2f191b9fec5ac7d90 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath7-eth16--Ampath4-eth16"}'
set_link_enable_metadata 3052018bb173a90e792f59985eb821d4ef4ec9f45e6cc94f72bd854f9bba5fc9 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath4-eth13--Ampath5-eth13"}'
set_link_enable_metadata 3956ad11df6336618b11ba3da67c855f895310509d61d9f520b712e4b140320a '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "SoL2-eth3--Ampath1-eth3"}'
set_link_enable_metadata 4872a043a11743ce3a13f8f8c4b5db2fa0d347e499c436e2b2b473f076a00f62 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "SoL2-eth2--Ampath1-eth2"}'
set_link_enable_metadata 5910658b867277df667e61954542fed34f0d65fdb6ebb1ac0c5baee3f0c0e953 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath3-eth10--Ampath2-eth10"}'
set_link_enable_metadata 7e0ceba7204a82635ed2a7f806784723b19fb4d22427cfabc1e97a5ecc737f11 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "SanJuan-eth8--Ampath2-eth8"}'
set_link_enable_metadata 9112e5d39a11391a575d383386c2e22e31270d3f0cc8158582d45a8ae488666b '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath3-eth9--Ampath1-eth9"}'
set_link_enable_metadata a25df84d52f018a5ec3fd34a4e398cfbfea0ccd2dde50b2a22ab98164217f758 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "AL2-eth7--SanJuan-eth7"}'
set_link_enable_metadata 3d8cb9eb085cf90837f49de8cdb951487936fc4fdeb3699be017c9c2701d9d6a '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "JAX2-eth15--Ampath5-eth15"}'
set_link_enable_metadata b6dac3f36cb8e7dd72e3e49746b0ea19035fb9e7e57e117fe4bfbfb774851c4d '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath2-eth1--Ampath1-eth1"}'
set_link_enable_metadata c71214eb60bccd0bbf5d41a17d6d47163940f9684d304014b5490cdbee67e195 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath5-eth12--Ampath2-eth12"}'
set_link_enable_metadata cde2d7062eba7fd1c6b27efcb771b66b4f2bbac305d359367db65cb4870bd060 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath7-eth17--SoL2-eth17"}'
set_link_enable_metadata dc67cf09e596bd4ea2c5d576f044404a85ed2f58cee8da2cbb39ba952e76ac67 '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "Ampath4-eth14--JAX1-eth14"}'
set_link_enable_metadata e5a1b37be396f0149004a4c85342bc0b6f3d800222b94f2dc26fd0dfb95939cc '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "AL2-eth4--Ampath2-eth4"}'
set_link_enable_metadata f84da0639233fe9d44614e6060abfa41d997b28d9ad729e8882ba4ddc02c29ed '{"availability": 100.0, "delay": 1, "packet_loss": 0.0, "bandwidth": 100, "utilization": 0, "link_name": "SoL2-eth5--AL3-eth5"}'
