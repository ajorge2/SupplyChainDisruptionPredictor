<script>
  // No chart imports needed

  // Mock data for testing
  const mockMaterials = [
    { id: 1, name: 'Aluminum' },
    { id: 2, name: 'Copper' },
    { id: 3, name: 'Steel' },
    { id: 4, name: 'Plastic' },
    { id: 5, name: 'Rubber' }
  ];

  let materials = mockMaterials;
  let selectedMaterial = null;
  let riskData = {};

  function handleKeydown(event, material) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectedMaterial = material;
    }
  }
</script>

<div class="dashboard">
  <header>
    <h1>Supply Chain Risk Dashboard</h1>
    <p class="status-message">⚠️ Using placeholder data - API integration pending</p>
  </header>

  <main>
    <aside class="materials-panel">
      <h2>Materials</h2>
      <ul>
        {#each materials as material}
          <button 
            class="material-item"
            class:selected={selectedMaterial?.id === material.id}
            on:click={() => selectedMaterial = material}
            on:keydown={(e) => handleKeydown(e, material)}
          >
            {material.name}
          </button>
        {/each}
      </ul>
    </aside>

    <section class="risk-panel">
      {#if selectedMaterial}
        <h2>Risk Analysis: {selectedMaterial.name}</h2>
        <div class="risk-metrics">
          <div class="metric-card">
            <h3>Weather Risks</h3>
            <p class="placeholder">0</p>
          </div>
          <div class="metric-card">
            <h3>News Risks</h3>
            <p class="placeholder">0</p>
          </div>
          <div class="metric-card">
            <h3>Social Media Risks</h3>
            <p class="placeholder">0</p>
          </div>
        </div>
      {:else}
        <p class="select-prompt">Select a material to view risk analysis</p>
      {/if}
    </section>
  </main>
</div>

<style>
  .dashboard {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    font-family: system-ui, -apple-system, sans-serif;
  }

  header {
    margin-bottom: 2rem;
  }

  h1 {
    color: #1a1a1a;
    font-size: 2rem;
    margin: 0;
  }

  .status-message {
    color: #856404;
    background-color: #fff3cd;
    border: 1px solid #ffeeba;
    padding: 0.75rem 1rem;
    border-radius: 4px;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  main {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .materials-panel {
    background: #f8f9fa;
    padding: 1.5rem;
    border-right: 1px solid #e9ecef;
  }

  .materials-panel h2 {
    color: #1a1a1a;
    font-size: 1.25rem;
    margin: 0 0 1rem 0;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .material-item {
    width: 100%;
    padding: 0.75rem 1rem;
    background: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    font-size: 1rem;
    color: inherit;
  }

  .material-item:hover {
    background: #e9ecef;
  }

  .material-item.selected {
    background: #007bff;
    color: white;
  }

  .risk-panel {
    padding: 1.5rem;
  }

  .risk-panel h2 {
    color: #1a1a1a;
    font-size: 1.5rem;
    margin: 0 0 1.5rem 0;
  }

  .risk-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    transition: transform 0.2s ease;
  }

  .metric-card:hover {
    transform: translateY(-2px);
  }

  .metric-card h3 {
    color: #1a1a1a;
    font-size: 1rem;
    margin: 0 0 0.5rem 0;
  }

  .metric-card p {
    color: #6c757d;
    margin: 0;
    font-size: 1.25rem;
  }

  .placeholder {
    color: #6c757d;
    opacity: 0.7;
  }

  .select-prompt {
    color: #6c757d;
    font-size: 1.1rem;
    text-align: center;
    margin-top: 2rem;
  }
</style> 