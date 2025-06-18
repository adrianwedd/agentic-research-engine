const { useState, useEffect, useRef } = React;

function Dashboard() {
  const graphRef = useRef(null);
  const [graphData, setGraphData] = useState({nodes: [], edges: []});
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    fetch('/graph').then(r => r.json()).then(data => {
      window.__GRAPH_DATA = data;
      setGraphData(data);
    });
    const source = new EventSource('/events');
    source.onmessage = ev => {
      const span = JSON.parse(ev.data);
      if (span.name.startsWith('node:')) {
        const id = span.name.split(':')[1];
        setGraphData(g => {
          if (!g.nodes.find(n => n.id === id)) {
            const node = {id, start: span.start, end: span.end};
            const nodes = g.nodes.concat(node);
            window.__GRAPH_DATA = {...g, nodes};
            return {...g, nodes};
          }
          return g;
        });
      } else if (span.name === 'edge') {
        setGraphData(g => {
          const edge = {from: span.attributes.from, to: span.attributes.to, timestamp: span.start};
          const edges = g.edges.concat(edge);
          window.__GRAPH_DATA = {...g, edges};
          return {...g, edges};
        });
      }
    };
    return () => source.close();
  }, []);

  useEffect(() => {
    const nodesById = Object.fromEntries(graphData.nodes.map(n => [n.id, n]));
    const fg = ForceGraph()(graphRef.current)
      .graphData({nodes: graphData.nodes, links: graphData.edges})
      .nodeId('id')
      .linkSource('from')
      .linkTarget('to')
      .nodeColor(n => {
        if (typeof n.confidence === 'number') {
          const g = Math.floor(n.confidence * 255);
          const r = 255 - g;
          return `rgb(${r},${g},100)`;
        }
        return '#1f77b4';
      })
      .linkColor(l => nodesById[l.from]?.intent === l.to ? '#2ca02c' : '#999');
    fg.onNodeClick(node => {
      fetch(`/belief/${node.id}/confidence`).then(r => r.json()).then(data => {
        alert(JSON.stringify(data, null, 2));
      });
    });
    fg.onLinkClick(link => {
      fetch(`/belief/${link.from}/intent`).then(r => r.json()).then(data => {
        alert(JSON.stringify(data, null, 2));
      });
    });
    return () => fg && fg._destructor && fg._destructor();
  }, [graphData]);

  const runSimulation = () => {
    fetch('/simulate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})})
      .then(() => fetch('/compare/simulation'))
      .then(r => r.json())
      .then(setComparison);
  };

  return React.createElement('div', null,
    React.createElement('button', {onClick: runSimulation}, 'Run Simulation'),
    React.createElement('div', {id: 'graph', ref: graphRef}),
    React.createElement('div', {id: 'gantt'}, 'Gantt view TBD'),
    comparison && React.createElement('pre', null, JSON.stringify(comparison, null, 2))
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Dashboard));
