#multicast the flow go through s3 to 10.0.0.7
curl -X POST -d '
{
    "dpid" : 3,
    "type" : "ALL",
    "group_id" : 2,
    "buckets" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_dst",
                    "value" : "00:00:00:00:00:07"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_dst",
                    "value" : "10.0.0.7"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 6
                }
	    ]
	},
        {
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "OUTPUT",
                    "port" : 2
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/groupentry/add

curl -X POST -d '
{
    "dpid" : 3,
    "type" : "ALL",
    "group_id" : 3,
    "buckets" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_dst",
                    "value" : "00:00:00:00:00:07"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_dst",
                    "value" : "10.0.0.7"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 6
                }
	    ]
	},
        {
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "SET_FIELD",
                    "field" : "eth_dst",
                    "value" : "00:00:00:00:00:06"
                },
		{
		    "type" : "SET_FIELD",
                    "field" : "ipv4_dst",
                    "value" : "10.0.0.6"
                },
		{
		    "type" : "OUTPUT",
                    "port" : 5
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/groupentry/add

#use the flow table to match group table
curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 20,
    "match" : {"in_port" : 5},
    "instructions" : [
	{
            "type" : "APPLY_ACTIONS",
	    "actions" : [
                {
	            "type" : "GROUP",
	            "group_id" : 2
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
    "priority" : 20,
    "match" : {"in_port" : 2},
    "instructions" : [
	{
            "type" : "APPLY_ACTIONS",
	    "actions" : [
                {
	            "type" : "GROUP",
	            "group_id" : 3
                }
            ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

curl -X POST -d '
{
    "dpid" : 4,
    "table_id" : 0,
    "priority" : 20,
    "match" : {"in_port" : 2},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
                {
		    "type" : "OUTPUT",
                    "port" : 3
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

curl -X POST -d '
{
    "dpid" : 4,
    "table_id" : 0,
    "priority" : 20,
    "match" : {"in_port" : 3},
    "instructions" : [
	{
	    "type" : "APPLY_ACTIONS",
	    "actions" : [
		{
		    "type" : "OUTPUT",
                    "port" : 2
                }
	    ]
	}
    ]
}
' http://localhost:8080/stats/flowentry/add

#install flows to prevent 10.0.0.7 from sending extra packets to the controller,
#thus prventing it from being detected by the topology module

curl -X POST -d '
{
    "dpid" : 3,
    "table_id" : 0,
    "priority" : 15,
    "match" : {"in_port" : 6}
}
' http://localhost:8080/stats/flowentry/add
