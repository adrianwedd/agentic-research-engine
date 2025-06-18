# Documentation

This site contains design docs, research papers, and project reports for the Agentic Research Engine.

## Guides

- [Semantic Memory with Neo4j](semantic_memory_neo4j.md)
- [Concurrency Testing Approach](concurrency_testing.md)

## Research

- [An Internal Economy for Computational Resource Allocation in Multi-Agent Systems](research/2025-computational-economy-for-multi-agents.md) - *future development*

## Epics

- [Interactive Agent Cockpit](epics/interactive_agent_cockpit_epic.md)
- [Research-Driven System Enhancements](epics/research_driven_system_enhancements_epic.md)

## Suggested Tasks

<ul id="suggested-tasks"></ul>

<script>
async function loadTasks() {
  try {
    const resp = await fetch('/suggested_tasks');
    if (!resp.ok) return;
    const data = await resp.json();
    const list = document.getElementById('suggested-tasks');
    data.forEach(t => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = 'https://chatgpt.com/codex/tasks/' + t.id;
      a.textContent = `${t.id}: ${t.title}`;
      li.appendChild(a);
      list.appendChild(li);
    });
  } catch (e) {
    console.error(e);
  }
}
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', loadTasks);
}
</script>
