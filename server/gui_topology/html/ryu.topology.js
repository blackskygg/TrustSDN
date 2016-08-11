var CONF = {
    image: {
        width: 50,
        height: 40
    },
    force: {
        width: 960,
        height: 500,
        dist: 200,
        charge: -600
    }
};

function trim_zero(obj) {
    return String(obj).replace(/^0+/, "");
}

function dpid_to_int(dpid) {
    return Number("0x" + dpid);
}

var elem = {
    force: d3.layout.force()
        .size([CONF.force.width, CONF.force.height])
        .charge(CONF.force.charge)
        .linkDistance(CONF.force.dist)
        .on("tick", _tick),
    svg: d3.select("body").append("svg")
        .attr("id", "topology")
        .attr("width", CONF.force.width)
        .attr("height", CONF.force.height),
    console: d3.select("body").append("div")
        .attr("id", "console")
        .attr("width", CONF.force.width)
};
function _tick() {
    elem.link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    elem.node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    elem.port.attr("transform", function(d) {
        var p = topo.get_port_point(d);
        return "translate(" + p.x + "," + p.y + ")";
    });
}
elem.drag = elem.force.drag().on("dragstart", _dragstart);
function _dragstart(d) {
    var dpid = dpid_to_int(d.dpid)
    d3.json("/stats/flow/" + dpid, function(e, data) {
        flows = data[dpid];
        console.log(flows);
        elem.console.selectAll("ol").remove();
        li = elem.console.append("ol")
            .selectAll("li");
        li.data(flows).enter().append("li")
            .text(function (d) { return JSON.stringify(d, null, " "); });
    });
    d3.select(this).classed("fixed", d.fixed = true);
}
elem.node = elem.svg.selectAll(".node");
elem.hnode = elem.svg.selectAll(".hnode");
elem.link = elem.svg.selectAll(".link");
elem.port = elem.svg.selectAll(".port");
elem.update = function () {
    this.force
        .nodes(topo.nodes)
        .links(topo.links)
        .start();

    this.link = this.link.data(topo.links);
    this.link.exit().remove();
    this.link.enter().append("line")
        .attr("class", "link");

    this.node = this.node.data(topo.nodes);
    this.node.exit().remove();
    var nodeEnter = this.node.enter().append("g")
        .attr("class", "node")
        .on("dblclick", function(d) { d3.select(this).classed("fixed", d.fixed = false); })
        .call(this.drag);
    nodeEnter.append("image")
    //select corresponding pics according to node types
        .attr("xlink:href", function(d) {
	    if (d.dpid == "ffffffffffffffff")
		return "./vswitch.svg";
	    else if (d.type == 0)
		return "./router.svg";
	    else 
		return "./host.svg";
	})
        .attr("x", -CONF.image.width/2)
        .attr("y", -CONF.image.height/2)
        .attr("width", function(d) {
	    if (d.dpid == "ffffffffffffffff")
		return 60;
	    else 
		return CONF.image.width;
	})
        .attr("height", function(d) {
	    if (d.dpid == "ffffffffffffffff")
		return 40;
	    else 
		return CONF.image.height;
	});

    nodeEnter.append("text")
        .attr("dx", -CONF.image.width/2)
        .attr("dy", CONF.image.height-10)
        .text(function(d) {
	    if (d.type == 0)
		return "dpid: " + trim_zero(d.dpid);
	    else
		return "mac: " + d.mac;
	});
    

    var ports = topo.get_ports();
    this.port.remove();
    this.port = this.svg.selectAll(".port").data(ports);
    var portEnter = this.port.enter().append("g")
        .attr("class", "port");
    portEnter.append("circle")
        .attr("r", 8);
    portEnter.append("text")
        .attr("dx", -3)
        .attr("dy", 3)
        .text(function(d) { return trim_zero(d.port_no); });
};

function is_valid_link(link) {
    return (link.src.dpid < link.dst.dpid)
}

var topo = {
    nodes: [],
    links: [],
    node_index: {}, // dpid -> index of nodes array
    initialize: function (data) {
	this.nodes = [],
	this.links = [],
	this.node_index = {}, // dpid -> index of nodes array

        this.add_nodes(data.switches, data.hosts);
        this.forge_links(data.switches, data.hosts);
    },
    add_nodes: function (slist, hlist) {
	var i = 0, len = 0;

	//add switches(type = 0)
        for (i = 0; i < slist.length; i++) {
	    slist[i].type = 0;
            this.nodes.push(slist[i]);
        }
	//add hosts(type = 1)
	try {
	    for (i = 0; i < hlist.length ; ++i) {
		hlist[i].type = 1;
		this.nodes.push(hlist[i]);
	    }
	} catch(e) {
	}

	//contruct the virtual core switch
	this.vnode = {dpid : "ffffffffffffffff",
		      ports: [],
		      type: 0};
	this.nodes.push(this.vnode);
	this.refresh_node_index();

    },
    //because we don't have actual links replied from the server,
    //we have to forge these links(h<->s and s<->s)
    forge_links: function (slist, hlist) {
	var vnode_idx = this.nodes.length - 1;

	for (i = 0; i < slist.length; i++) {
	    var dst_port = {port_no: i + 1,
			    dpid: slist[i].dpid};
	    this.vnode.ports.push(dst_port);

	    var src_port;
	    for (var j = 0; j < slist[i].ports.length; ++j) {
		if(slist[i].ports[j].port_type == 1)
		    src_port = slist[i].ports[j];
	    }
	    var link = {
		source: i,
		target: vnode_idx,
		port: {
		    src: src_port,
		    dst: dst_port
		}
	    };
	    this.links.push(link);
	}

	hosts_offset = slist.length;
	for (i = 0; i < hlist.length; i++) {
	    var dp_port_no = hlist[i].port.port_no;
	    var dpid = hlist[i].port.dpid;
	    //while using dpid to identify a switch,
	    //we use dpid:port_no to identify a host
	    var dst_port = {port_no : 1,
			    dpid: dpid + ":" + dp_port_no};
	    var src_port;
	    var dp_node = this.nodes[this.node_index[dpid]];
	    for (var j = 0; j < dp_node.ports.length; ++j) {
		if(dp_node.ports[j].port_no == dp_port_no)
		    src_port = dp_node.ports[j];
	    }
	    
	    var link = {
		source: this.node_index[dpid],
		target: i + hosts_offset,
		port: {
		    src: src_port,
		    dst: dst_port
		}
	    };
	    this.links.push(link);

	    
	}
    },
    delete_nodes: function (nodes) {
        for (var i = 0; i < nodes.length; i++) {
            console.log("delete switch: " + JSON.stringify(nodes[i]));

            node_index = this.get_node_index(nodes[i]);
            this.nodes.splice(node_index, 1);
        }
        this.refresh_node_index();
    },
    delete_links: function (links) {
        for (var i = 0; i < links.length; i++) {
            if (!is_valid_link(links[i])) continue;
            console.log("delete link: " + JSON.stringify(links[i]));

            link_index = this.get_link_index(links[i]);
            this.links.splice(link_index, 1);
        }
    },
    get_node_index: function (node) {
        for (var i = 0; i < this.nodes.length; i++) {
            if (node.dpid == this.nodes[i].dpid) {
                return i;
            }
        }
        return null;
    },
    get_link_index: function (link) {
        for (var i = 0; i < this.links.length; i++) {
            if (link.src.dpid == this.links[i].port.src.dpid &&
                link.src.port_no == this.links[i].port.src.port_no &&
                link.dst.dpid == this.links[i].port.dst.dpid &&
                link.dst.port_no == this.links[i].port.dst.port_no) {
                return i;
            }
        }
        return null;
    },
    get_ports: function () {
        var ports = [];
        var pushed = {};
        for (var i = 0; i < this.links.length; i++) {
            function _push(p, dir) {
                key = p.dpid + ":" + p.port_no;
                if (key in pushed) {
                    return 0;
                }

                pushed[key] = true;
                p.link_idx = i;
                p.link_dir = dir;
                return ports.push(p);
            }
            _push(this.links[i].port.src, "source");
            _push(this.links[i].port.dst, "target");
        }

        return ports;
    },
    get_port_point: function (d) {
        var weight = 0.88;

        var link = this.links[d.link_idx];
        var x1 = link.source.x;
        var y1 = link.source.y;
        var x2 = link.target.x;
        var y2 = link.target.y;

        if (d.link_dir == "target") weight = 1.0 - weight;

        var x = x1 * weight + x2 * (1.0 - weight);
        var y = y1 * weight + y2 * (1.0 - weight);

        return {x: x, y: y};
    },
    refresh_node_index: function(){
        this.node_index = {};
        for (var i = 0; i < this.nodes.length; i++) {
	    if (this.nodes[i].type == 0) {
		this.node_index[this.nodes[i].dpid] = i;
	    } else {
		this.node_index[this.nodes[i].port.dpid+":"
				+this.nodes[i].port.port_no] = i;
	    }
        }
    },
}

function initialize_topology() {
    d3.json("/v1.0/topology/switches", function(error, switches) {
        d3.json("/v1.0/topology/hosts", function(error, hosts) {
            topo.initialize({switches: switches, hosts: hosts, links: []});
            elem.update();
        });
    });
}

function main() {
    initialize_topology();
}

function connect(switch1, port1 ,switch2, port2, func_no)
{
    
    var xmlhttp;
    if (window.XMLHttpRequest)
    {// code for IE7+, Firefox, Chrome, Opera, Safari
	xmlhttp=new XMLHttpRequest();
    }
    else
    {// code for IE6, IE5
	xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }

    func = ["connect", "disconnect"]
    
    var request = "/config/" + func[func_no] + "/" + switch1 + "/" + port1
	+ "/" + switch2 + "/" + port2
    
    //document.getElementById("myp").innerHTML = attact1;
    xmlhttp.open("GET",request,false);
    xmlhttp.send();

    return xmlhttp.responseText;
}
//document.getElementById("refresh").onclick=initialize_topology
main();
