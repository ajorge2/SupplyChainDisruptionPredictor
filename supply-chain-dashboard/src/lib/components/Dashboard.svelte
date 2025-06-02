<script>
  // No chart imports needed

  // Mock data for testing
  const mockProducts = {
    "Raw Materials": [
      { id: 1, name: 'Aluminum' },
      { id: 2, name: 'Copper' },
      { id: 3, name: 'Steel' }
    ],
    "Semiconductors": [
      { id: 4, name: 'Silicon Wafers' },
      { id: 5, name: 'Memory Chips' }
    ],
    "Chemicals": [
      { id: 6, name: 'Industrial Gases' },
      { id: 7, name: 'Specialty Chemicals' }
    ]
  };

  const mockLocations = {
    "US Cities": [
      "New York City",
      "Boston",
      "Philadelphia",
      "Miami",
      "Atlanta"
    ],
    "Countries": [
      "China",
      "Japan",
      "Germany",
      "Mexico",
      "Canada"
    ]
  };

  let products = mockProducts;
  let locations = mockLocations;
  let selectedProduct = null;
  let selectedLocation = null;
  let selectedCategory = Object.keys(products)[0];
  let selectedLocationType = Object.keys(locations)[0];
  let riskData = {};

  function handleProductSelect(product) {
    selectedProduct = product;
  }

  function handleLocationSelect(location) {
    selectedLocation = location;
  }
</script>

<div class="dashboard">
  <header>
    <h1>Supply Chain Risk Dashboard</h1>
    <p class="status-message">⚠️ Using placeholder data - API integration pending</p>
  </header>

  <main>
    <aside class="selection-panel">
      <div class="product-section">
        <h2>Products</h2>
        <div class="category-selector">
          {#each Object.keys(products) as category}
            <button 
              class="category-btn"
              class:selected={selectedCategory === category}
              on:click={() => selectedCategory = category}
            >
              {category}
            </button>
          {/each}
        </div>
        <ul class="item-list">
          {#each products[selectedCategory] as product}
            <button 
              class="item-btn"
              class:selected={selectedProduct?.id === product.id}
              on:click={() => handleProductSelect(product)}
            >
              {product.name}
            </button>
          {/each}
        </ul>
      </div>

      <div class="location-section">
        <h2>Locations</h2>
        <div class="category-selector">
          {#each Object.keys(locations) as type}
            <button 
              class="category-btn"
              class:selected={selectedLocationType === type}
              on:click={() => selectedLocationType = type}
            >
              {type}
            </button>
          {/each}
        </div>
        <ul class="item-list">
          {#each locations[selectedLocationType] as location}
            <button 
              class="item-btn"
              class:selected={selectedLocation === location}
              on:click={() => handleLocationSelect(location)}
            >
              {location}
            </button>
          {/each}
        </ul>
      </div>
    </aside>

    <section class="risk-panel">
      {#if selectedProduct && selectedLocation}
        <h2>Risk Analysis: {selectedProduct.name} in {selectedLocation}</h2>
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
        <p class="select-prompt">Select both a product and location to view risk analysis</p>
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
    grid-template-columns: 400px 1fr;
    gap: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .selection-panel {
    background: #f8f9fa;
    padding: 1.5rem;
    border-right: 1px solid #e9ecef;
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .product-section, .location-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  h2 {
    color: #1a1a1a;
    font-size: 1.25rem;
    margin: 0;
  }

  .category-selector {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .category-btn {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }

  .category-btn:hover {
    background: #e9ecef;
  }

  .category-btn.selected {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }

  .item-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .item-btn {
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

  .item-btn:hover {
    background: #e9ecef;
  }

  .item-btn.selected {
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