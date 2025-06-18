const { useState, useEffect, useRef } = React;

function Dashboard() {
  const graphRef = useRef(null);
  const [graphData, setGraphData] = useState({nodes: [], edges: []});

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
    const fg = ForceGraph()(graphRef.current)
      .graphData({nodes: graphData.nodes, links: graphData.edges})
      .nodeId('id')
      .linkSource('from')
      .linkTarget('to');
    return () => fg && fg._destructor && fg._destructor();
  }, [graphData]);

  return React.createElement('div', null,
    React.createElement('div', {id: 'graph', ref: graphRef}),
    React.createElement('div', {id: 'gantt'}, 'Gantt view TBD')
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Dashboard));
