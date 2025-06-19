const { useState, useEffect, useRef } = React;

function Dashboard() {
  const graphRef = useRef(null);
  const [graphData, setGraphData] = useState({nodes: [], edges: []});
  const [comparison, setComparison] = useState(null);
  const [autonomy, setAutonomy] = useState('AUTONOMOUS');
  const [nodeMetrics, setNodeMetrics] = useState(null);

  useEffect(() => {
    fetch('/graph').then(r => r.json()).then(data => {
      window.__GRAPH_DATA = data;
      setGraphData(data);
    });
    fetch('/autonomy').then(r => r.json()).then(d => setAutonomy(d.level));
    const source = new EventSource('/events');
    source.onmessage = ev => {
      const span = JSON.parse(ev.data);
      if (span.name.startsWith('node:')) {
        const id = span.name.split(':')[1];
        const metrics = {};
        if (span.attributes && span.attributes.state_out) {
          try {
            const state = JSON.parse(span.attributes.state_out);
            metrics.confidence = state.scratchpad?.confidence;
            metrics.intent = state.scratchpad?.intent;
          } catch {}
        }
        setGraphData(g => {
          const existing = g.nodes.find(n => n.id === id);
          const node = {
            id,
            start: span.start,
            end: span.end,
            duration: span.end - span.start,
            ...metrics
          };
          let nodes;
          if (existing) {
            nodes = g.nodes.map(n => (n.id === id ? {...n, ...node} : n));
          } else {
            nodes = g.nodes.concat(node);
          }
          window.__GRAPH_DATA = {...g, nodes};
          return {...g, nodes};
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
      fetch(`/node/${node.id}/metrics`).then(r => r.json()).then(setNodeMetrics);
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

  const logPreference = preferred => {
    if (!comparison) return;
    const better = preferred === 'simulation' ? comparison.simulation : comparison.live;
    const worse = preferred === 'simulation' ? comparison.live : comparison.simulation;
    fetch('/preferences', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({better, worse})})
      .then(() => setComparison(null));
  };

  const updateAutonomy = e => {
    const level = e.target.value;
    fetch('/autonomy', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({level})})
      .then(() => setAutonomy(level));
  };

  const pause = () => fetch('/pause', {method: 'POST'});
  const resume = () => fetch('/resume', {method: 'POST'});

  return React.createElement('div', null,
    React.createElement('button', {onClick: runSimulation}, 'Run Simulation'),
    React.createElement('div', null,
      React.createElement('label', null, 'Autonomy:'),
      React.createElement('select', {value: autonomy, onChange: updateAutonomy},
        React.createElement('option', {value: 'MANUAL'}, 'Manual'),
        React.createElement('option', {value: 'ASSISTIVE'}, 'Assistive'),
        React.createElement('option', {value: 'SUPERVISORY'}, 'Supervisory'),
        React.createElement('option', {value: 'AUTONOMOUS'}, 'Autonomous')
      ),
      React.createElement('button', {onClick: pause}, 'Pause'),
      React.createElement('button', {onClick: resume}, 'Resume')
    ),
    React.createElement('div', {id: 'graph', ref: graphRef}),
    React.createElement('div', {id: 'gantt'}, 'Gantt view TBD'),
    comparison && React.createElement(
      React.Fragment,
      null,
      React.createElement('pre', null, JSON.stringify(comparison, null, 2)),
      React.createElement('button', {onClick: () => logPreference('live')}, 'Prefer Live'),
      React.createElement('button', {onClick: () => logPreference('simulation')}, 'Prefer Simulation')
    ),
    nodeMetrics && React.createElement(
      'pre',
      {id: 'metrics'},
      JSON.stringify(nodeMetrics, null, 2)
    )
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Dashboard));
