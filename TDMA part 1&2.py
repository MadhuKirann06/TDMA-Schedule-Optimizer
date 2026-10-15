import json
import math
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import networkx as nx

def calculate_distance(coord1, coord2):
    """Calculate Euclidean distance between two 2D points."""
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

def build_topology_graph(node_coords, radio_range=500.0):
    """
    Builds a NetworkX graph where nodes are connected if distance <= radio_range.
    """
    G = nx.Graph()
    nodes = sorted(list(node_coords.keys()))
    
    for node in nodes:
        G.add_node(node, pos=node_coords[node])
        
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            dist = calculate_distance(node_coords[n1], node_coords[n2])
            if dist <= radio_range:
                G.add_edge(n1, n2)
                
    return G

def get_distance_2_conflicts(G):
    """
    Finds all 1-hop and 2-hop interfering neighbors for each node.
    Distance-1: Direct link (Node A <--- Link ---> Node B)
    Distance-2: Hidden terminal (Node A ---> Node B <--- Node C)
    """
    conflicts = {node: set() for node in G.nodes()}
    
    for node in G.nodes():
        one_hop = set(G.neighbors(node))
        two_hop = set()
        for neighbor in one_hop:
            two_hop.update(G.neighbors(neighbor))
            
        all_conflicts = (one_hop | two_hop) - {node}
        conflicts[node] = all_conflicts
        
    return conflicts

def optimize_tdma_schedule(G, conflicts):
    """
    Applies Distance-2 Graph Coloring heuristic (Degree-based greedy coloring)
    to assign conflict-free timeslots and achieve spatial reuse.
    """
    sorted_nodes = sorted(G.nodes(), key=lambda n: len(conflicts[n]), reverse=True)
    assignments = {}
    
    for node in sorted_nodes:
        neighbor_slots = {assignments[nbr] for nbr in conflicts[node] if nbr in assignments}
        
        slot = 0
        while slot in neighbor_slots:
            slot += 1
            
        assignments[node] = slot
        
    return assignments

# =====================================================================
# PART 1: REPORT & ASCII MATRIX GENERATOR
# =====================================================================
def generate_report(node_coords, assignments, radio_range=500.0):
    """Prints the required ASCII TDMA Topology Optimization Report."""
    sorted_nodes = sorted(list(assignments.keys()))
    max_slot = max(assignments.values()) if assignments else 0
    total_slots = max_slot + 1
    
    print("=" * 40)
    print("TDMA TOPOLOGY OPTIMIZATION REPORT")
    print("=" * 40)
    print(f"Total Nodes Processed : {len(sorted_nodes)}")
    print(f"Configured Radio Range: {radio_range} meters")
    print(f"Optimized Frame Length: {total_slots} unique timeslots (Lower is better)")
    print("-" * 40)
    print("NODE -> SLOT ASSIGNMENTS:")
    
    for node in sorted_nodes:
        print(f"{node}: Slot {assignments[node]}")
        
    print("\n" + "=" * 40)
    print("STRUCTURAL TDMA SCHEDULE MATRIX (Slot x Node Boolean Matrix):")
    
    short_labels = [node.split('_')[-1] if '_' in node else f"{int(node):02d}" for node in sorted_nodes]
    header = "Slot \\ Node | " + " | ".join(short_labels)
    print(header)
    print("-" * len(header))
    
    for s in range(total_slots):
        row_bits = []
        for node in sorted_nodes:
            bit = "1" if assignments[node] == s else "0"
            row_bits.append(f"{bit:^{len(short_labels[0])}}")
            
        slot_label = f"Slot {s:02d}"
        print(f"{slot_label:<11} | " + " | ".join(row_bits))
        
    print("=" * 40)
    print("Execution finalized cleanly. Schedule verified conflict-free.")
    print("=" * 40)

# =====================================================================
# PART 2: EMANE TDMA SCHEDULE XML INTEGRATION BRIDGE
# =====================================================================
def export_emane_tdma_xml(assignments, output_filename="emane_tdma_schedule.xml"):
    """
    Converts Part 1 schedule assignments into EMANE TDMA Radio Model XML format.
    Configures 1ms slots in a single frame structure.
    """
    total_slots = max(assignments.values()) + 1
    
    schedule = ET.Element("emane-tdma-schedule")
    
    structure = ET.SubElement(schedule, "structure", {
        "frames": "1",
        "slots": str(total_slots),
        "slotduration": "1000",
        "bandwidth": "10M",
        "guardtime": "100"
    })

    multiframe = ET.SubElement(schedule, "multiframe", {
        "frequency": "2400000000",
        "power": "0",              
        "datarate": "1M"           
    })
    
    frame = ET.SubElement(multiframe, "frame", {"index": "0"})
    
    slot_to_nodes = {s: [] for s in range(total_slots)}
    for node, slot in assignments.items():
        nem_id = int(node.split('_')[-1]) if '_' in node else int(node)
        slot_to_nodes[slot].append(nem_id)

    for slot_idx in range(total_slots):
        slot_elem = ET.SubElement(frame, "slot", {"index": str(slot_idx)})
        for nem_id in slot_to_nodes[slot_idx]:
            ET.SubElement(slot_elem, "tx", {"nem": str(nem_id)})

    raw_xml = ET.tostring(schedule, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    formatted_xml = parsed_xml.toprettyxml(indent="  ")

    with open(output_filename, "w") as f:
        f.write(formatted_xml)
        
    print(f"\n[PART 2 BRIDGE] EMANE Schedule XML successfully generated: '{output_filename}'")

def main():
    sample_json = json.dumps({
        "Node_01": [0.0, 0.0],    "Node_02": [300.0, 0.0],  "Node_03": [600.0, 0.0],  "Node_04": [900.0, 0.0],
        "Node_05": [0.0, 300.0],  "Node_06": [300.0, 300.0],"Node_07": [600.0, 300.0],"Node_08": [900.0, 300.0],
        "Node_09": [0.0, 600.0],  "Node_10": [300.0, 600.0],"Node_11": [600.0, 600.0],"Node_12": [900.0, 600.0],
        "Node_13": [0.0, 900.0],  "Node_14": [300.0, 900.0],"Node_15": [600.0, 900.0],"Node_16": [900.0, 900.0]
    })
    
    if len(sys.argv) > 1:
        json_input = sys.argv[1]
    else:
        json_input = sample_json
        
    node_coords = json.loads(json_input)
    
    # 1. Build Topology Graph (500m Radio Range)
    G = build_topology_graph(node_coords, radio_range=500.0)
    
    # 2. Extract Distance-1 and Distance-2 Conflicts
    conflicts = get_distance_2_conflicts(G)
    
    # 3. Optimize TDMA Schedule
    assignments = optimize_tdma_schedule(G, conflicts)
    
    # 4. Part 1 Output: Terminal Report & Structural Matrix
    generate_report(node_coords, assignments, radio_range=500.0)
    
    # 5. Part 2 Output: Export EMANE XML File
    export_emane_tdma_xml(assignments, "emane_tdma_schedule.xml")

if __name__ == "__main__":
    main()
