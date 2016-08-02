#let the icmp pass through, so that ping acts normally
curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 17,
    "match" : {"in_port" : 5, "eth_type" : 2048, "ip_proto" : 1},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "PUSH_VLAN",
                    "ethertype" :  33024
		}, 
		{
		    "type" : "SET_FIELD",
                    "field" : "vlan_vid",
                    "value" : 4097
                }
	    ]
	},
	{
	    "type" : "GOTO_TABLE",
	    "table_id" : 1
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 17,
    "match" : {"in_port" : 6, "eth_type" : 2048, "ip_proto" : 1},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "PUSH_VLAN",
                    "ethertype" :  33024
		}, 
		{
		    "type" : "SET_FIELD",
                    "field" : "vlan_vid",
                    "value" : 4097
                }
	    ]
	},
	{
	    "type" : "GOTO_TABLE",
	    "table_id" : 1
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

#direct the flow from 10.0.0.12 to 10.0.0.13 to 10.0.0.3 and vice versa
curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 16,
    "match" : {"in_port" : 5, "eth_type" : 2048, "ipv4_dst" : "10.0.0.13"},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_dst",
                    "value" : "00:00:00:00:00:03"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_dst",
                    "value" : "10.0.0.3"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 4
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 16,
    "match" : {"in_port" : 6, "eth_type" : 2048, "ipv4_dst" : "10.0.0.12"},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_dst",
                    "value" : "00:00:00:00:00:03"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_dst",
                    "value" : "10.0.0.3"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 4
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

#when 10.0.0.3 tries to send packets to 10.0.0.12,
#modify the header to fool 10.0.0.12 that they are from 10.0.0.13
#for packets to 10.0.0.13, the same

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 16,
    "match" : {"in_port" : 4, "eth_type" : 2048, "ipv4_dst" : "10.0.0.12"},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_src",
                    "value" : "00:00:00:00:01:03"
                },
		{
		    "type" : "SET_FIELD",
                    "field" :  "ipv4_src",
                    "value" : "10.0.0.13"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 5
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 16,
    "match" : {"in_port" : 4, "eth_type" : 2048, "ipv4_dst" : "10.0.0.13"},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_src",
                    "value" : "00:00:00:00:01:02"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_src",
                    "value" : "10.0.0.12"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 6
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add


#install flows to prevent 10.0.0.3 from sending extra packets to the controller,
#thus prventing it from being detected by the topology module

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 15,
    "match" : {"in_port" : 4}
}
' http://localhost:8080/stats/flowentry/add
