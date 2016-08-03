#modify the flooding group of vid=1 to replace vm3 with vm2
curl -X POST -d '{
    "dpid": 3,
    "group_id": 0
 }' http://localhost:8080/stats/groupentry/delete

curl -X POST -d '
{
    "dpid" : 3,
    "type" : "ALL",
    "group_id" : 0,
    "buckets" : [
	{
	  "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "POP_VLAN"
		}, 
		{
		    "type" : "OUTPUT",
                    "port" : 3
                }
	    ]
	},
        {
	  "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "OUTPUT",
                    "port" : 1
                }
	    ]
	},
        {
	   "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "OUTPUT",
                    "port" : "OFPP_CONTROLLER"
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/groupentry/add

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 1,
    "priority" : 0,
    "match" : {"dl_vlan": "0x1001"},
    "instructions" : [
	{
	     "type" : "APPLY_ACTIONS",
	    "actions" : [
                {
	            "type" : "GROUP",
	            "group_id" : 0
                }
            ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

#add the tagging flow for vm2
curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 1,
    "match" : {"in_port" : 3},
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
    "priority" : 15,
    "match" : {"in_port" : 4}
}
' http://localhost:8080/stats/flowentry/add
