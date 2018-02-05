#!/usr/bin/env python3.6
import logging
logging.basicConfig(level=logging.INFO)
import csv
import networkx as nx
import re
import sys

def checkcmdln():
  logging.debug("Run checkcmdln")
  if len(sys.argv) == 1:
    logging.critical("No files found")
    print(f'Usage: {sys.argv[0]} mycsvfile1.csv mycsvfile2.csv ...')
    exit(0) 

def readmycsv(file):
  logging.debug("Run readmycsv")
  logging.info("Reading files " + ",".join(file))
  for f in file:
    reader = {}
    try:
      reader = csv.DictReader(open(f, 'r'))
    except:
      logging.error("ERROR: opening file " + f)
      continue  
    flow_list = []
    for flow in reader:
      logging.debug(flow)
      flow_list.append(flow)
  try:
    return flow_list
  except:
    logging.critical("No flows found!!")
    exit(0)  

def build_network(flow_list):
  logging.debug("Run build_network")
  G = nx.Graph()
  for flow in flow_list:
    logging.debug(flow)
    # Clean up the data.
    if flow['LocalAddress'] == "": flow['LocalAddress'] = flow['IPAddress']
    if flow['ForeignAddress'] == "127.0.0.1": flow['ForeignAddress'] = flow['IPAddress']
    # Add hostname as node.
    G.add_node(str(flow['ComputerName']), type_='host')
    # Add local ip and port as node.
    localport = f'{flow["ConnectionType"]}_{flow["LocalAddress"]}_{flow["LocalPort"]}'
    G.add_node(localport, type_='port', port_="local", data=flow)
    # Add remote ip and port as node.
    remoteport = f'{flow["ConnectionType"]}_{flow["ForeignAddress"]}_{flow["ForeignPort"]}'
    G.add_node(remoteport, type_='port', port_="remote", data=flow)
    # Add local and remote as edge connection.
    if flow['State'] == "LISTEN": 
      continue
    else:
      G.add_edge(localport, remoteport, type_='flow', data=flow)
  logging.info(nx.info(G))  
  return G  

def build_subgraphs(gdb):
  logging.debug("Run build_subgraphs")
  g = ""
  for node, val in gdb.nodes.items():
    inv = ""
    if val['type_'] == 'host':
      g += f'subgraph "cluster_{node}" {{style=filled; color=lightgrey; node [style=filled,color=white]; label = "{node}"; \n'
      # Adding FAKENODE to ensure ports don't end up with the invis style.
      g += '"FAKENODE" [style=invis]\n'
      for port, val2 in gdb.nodes.items():
        if (val2['type_'] == 'port' and val2['port_'] == "remote"): continue
        if (val2['type_'] == 'port' and val2['port_'] == "local" and val2['data']['ComputerName'] == node):
          if val2['data']['State'] == "LISTEN":
            g += f'"{port}" [label="{val2["data"]["LocalPort"]}_{val2["data"]["Process"]}", color=blue]\n'
          else:  
            g += f'"{port}" [label="{val2["data"]["LocalPort"]}_{val2["data"]["Process"]}"]\n'
          inv += f'"{port}" -> '
      g += re.sub(r'-> $', '-> "FAKENODE" [style=invis];', inv)
      g += "}\n"
  return g

def build_edges(gdb):
  logging.debug("Run build_edges")
  g = ""
  for edge, val in gdb.edges.items():
    g += f'"{edge[0]}" -> "{edge[1]}"\n'
  return g  

def getconns():
  logging.debug("Run getconns")
  checkcmdln()
  fl = readmycsv(sys.argv[1:])
  gdb = build_network(fl)
  g = ""
  g += build_subgraphs(gdb)
  g += build_edges(gdb)
  return g

logging.debug("--Starting Main Program--")
###########################################
# Below this point is the HTML formatting #
###########################################
output_top = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Netstat Viz</title>
  </head>
  <body>
    
    <script src="./viz.js"></script>
    <script>
    var src = `
    digraph { 

"""

conns = getconns()

output_bottom = """
}
`;
    document.body.innerHTML += Viz(src, options={ format: "svg", engine: "dot", scale: 1, totalMemory: 33554432 });
    
    </script>
    
  </body>
</html>
"""

print(output_top + conns + output_bottom)
logging.debug("--End Main Program--")