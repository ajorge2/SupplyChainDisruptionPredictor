<script>
  import { onMount } from 'svelte';

  let products = {};
  let locations = {};
  let selectedProduct = null;
  let selectedLocation = null;
  let selectedCategory = "";
  let selectedLocationType = "";
  let riskData = {};
  let product = "";
  let location = "";
  let result = null;
  let loading = false;
  let error = "";
  let materialRiskScores = {};
  let dataLoaded = false;

  onMount(async () => {
    try {
      // Load products from products.json
      const productsRes = await fetch("http://192.241.150.36:8000/products");
      if (!productsRes.ok) throw new Error("Failed to load products");
      const productsData = await productsRes.json();
      
      // Helper function to format names
      const formatName = (name) => {
        return name
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      };

      // Process products into a more organized structure
      const processedProducts = {
        "Metals": [],
        "Semiconductors": [],
        "Chemicals": [],
        "Agricultural": [],
        "Minerals": []
      };

      // Process metals (which has subcategories)
      Object.entries(productsData.raw_materials.metals).forEach(([category, items]) => {
        Object.keys(items).forEach((name) => {
          processedProducts["Metals"].push({
            id: `metal_${category}_${name}`,
            name: formatName(name),
            category: formatName(category)
          });
        });
      });

      // Process semiconductors (direct items)
      Object.keys(productsData.raw_materials.semiconductors).forEach((name) => {
        processedProducts["Semiconductors"].push({
          id: `semi_${name}`,
          name: formatName(name),
          category: "Semiconductors"
        });
      });

      // Process chemicals
      Object.entries(productsData.raw_materials.chemicals).forEach(([category, items]) => {
        Object.keys(items).forEach((name) => {
          processedProducts["Chemicals"].push({
            id: `chem_${category}_${name}`,
            name: formatName(name),
            category: formatName(category)
          });
        });
      });

      // Process agricultural
      Object.entries(productsData.raw_materials.agricultural).forEach(([category, items]) => {
        Object.keys(items).forEach((name) => {
          processedProducts["Agricultural"].push({
            id: `agri_${category}_${name}`,
            name: formatName(name),
            category: formatName(category)
          });
        });
      });

      // Process minerals
      Object.entries(productsData.raw_materials.minerals).forEach(([category, items]) => {
        Object.keys(items).forEach((name) => {
          processedProducts["Minerals"].push({
            id: `mineral_${category}_${name}`,
            name: formatName(name),
            category: formatName(category)
          });
        });
      });

      products = processedProducts;

      // Load locations from locations.json
      const locationsRes = await fetch("http://192.241.150.36:8000/locations");
      if (!locationsRes.ok) throw new Error("Failed to load locations");
      const locationsData = await locationsRes.json();
      locations = {
        "US Cities": locationsData.us_cities,
        "Countries": locationsData.countries
      };

      selectedCategory = Object.keys(products)[0];
      selectedLocationType = Object.keys(locations)[0];
      dataLoaded = true;
    } catch (e) {
      error = e.message;
    }
  });

  function handleProductSelect(selectedProd) {
    if (selectedProd) {
      selectedProduct = selectedProd;
      product = selectedProd.name;
    }
  }

  function handleLocationSelect(selectedLoc) {
    if (selectedLoc) {
      selectedLocation = selectedLoc;
      location = selectedLoc;
    }
  }

  function handleCategorySelect(category) {
    selectedCategory = category;
    selectedProduct = null;
    product = "";
  }

  async function search() {
    if (!product || !location) {
      error = "Please select both a product and location";
      return;
    }
    loading = true;
    error = "";
    result = null;
    materialRiskScores = {};
    try {
      const res = await fetch("http://192.241.150.36:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product, location })
      });
      if (!res.ok) throw new Error("API error");
      result = await res.json();

      // Fetch risk scores for each material
      if (result && result.raw_materials && location) {
        for (const material of result.raw_materials) {
          try {
            const riskRes = await fetch(`http://192.241.150.36:8000/risk_score?material=${encodeURIComponent(material)}&location=${encodeURIComponent(location)}`);
            if (riskRes.ok) {
              const riskData = await riskRes.json();
              console.log(`Risk score for ${material} / ${location}:`, riskData);
              materialRiskScores[material] = riskData.risk_score;
            } else {
              // Log the error response
              const errorText = await riskRes.text();
              console.error(`Failed to fetch risk score for ${material} / ${location}:`, riskRes.status, errorText);
              materialRiskScores[material] = null;
            }
          } catch (err) {
            console.error(`Network error for ${material} / ${location}:`, err);
            materialRiskScores[material] = null;
          }
        }
      }
    } catch (e) {
      error = e.message;
    }
    loading = false;
  }
</script>

<div class="dashboard">
  <main>
    <header>
      <h1>Supply Chain Risk Dashboard</h1>
      {#if !dataLoaded}
        <p class="status-message">Loading data...</p>
      {/if}
    </header>

    <form on:submit|preventDefault={search} class="search-form">
      <input placeholder="Product" bind:value={product} />
      <input placeholder="Location" bind:value={location} />
      <button type="submit" disabled={loading || !product || !location}>Analyze</button>
    </form>

    <div class="main-content">
      <aside class="selection-panel">
        <div class="product-section">
          <h2>Products</h2>
          <div class="category-selector">
            {#each Object.keys(products) as category}
              <button 
                class="category-btn"
                class:selected={selectedCategory === category}
                on:click={() => handleCategorySelect(category)}
              >
                {category}
              </button>
            {/each}
          </div>
          
          {#if products[selectedCategory]}
            <div class="category-group">
              <h3 class="category-header">{selectedCategory}</h3>
              <div class="product-list">
                {#each products[selectedCategory] as prod}
                  <button 
                    class="product-item"
                    class:selected={selectedProduct?.id === prod.id}
                    on:click={() => handleProductSelect(prod)}
                  >
                    <span class="product-name">{prod.name}</span>
                    <span class="product-category">{prod.category}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>

        <div class="location-section">
          <h2>Locations</h2>
          <div class="category-selector">
            {#each Object.keys(locations) as type}
              <button 
                class="category-btn"
                class:selected={selectedLocationType === type}
                on:click={() => {
                  selectedLocationType = type;
                  selectedLocation = null;
                  location = "";
                }}
              >
                {type}
              </button>
            {/each}
          </div>
          <div class="item-list">
            {#each locations[selectedLocationType] || [] as loc}
              <button 
                class="item-btn"
                class:selected={selectedLocation === loc}
                on:click={() => handleLocationSelect(loc)}
              >
                {loc}
              </button>
            {/each}
          </div>
        </div>
      </aside>

      <section class="risk-panel">
        {#if loading}
          <div class="risk-card loading">
            <div class="loading-spinner"></div>
            <p>Analyzing risks...</p>
          </div>
        {:else if error}
          <div class="risk-card error">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        {:else if result}
          <div class="risk-card">
            <h3>Risk Analysis</h3>
            <div class="risk-details">
              <p class="selection-info">
                <strong class="selection-label">Product:</strong> <span class="selection-value">{product}</span><br>
                <strong class="selection-label">Location:</strong> <span class="selection-value">{location}</span>
              </p>
              <div class="risk-score">
                <span class="score-label">Risk Score</span>
                <span class="score-value" 
                  class:high-risk={result.risk_score === 3} 
                  class:medium-risk={result.risk_score === 2} 
                  class:low-risk={result.risk_score <= 1}
                >
                  {result.risk_score}
                </span>
              </div>
            </div>
          </div>
        {:else if product && location}
          <div class="risk-card pending">
            <h3>Ready to Analyze</h3>
            <p>Click "Analyze" to calculate risk score for:</p>
            <p class="selection-info">
              <strong>Product:</strong> {product}<br>
              <strong>Location:</strong> {location}
            </p>
          </div>
        {:else}
          <div class="risk-card empty">
            <h3>No Analysis Yet</h3>
            <p>Select a product and location to analyze supply chain risks</p>
          </div>
        {/if}
      </section>
    </div>
  </main>
</div>

<style>
  .dashboard {
    min-height: 100vh;
    width: 100vw;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    background: #f0f2f5;
    font-family: system-ui, -apple-system, sans-serif;
  }

  main {
    width: 100%;
    max-width: 1100px;
    margin: 2rem 0;
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .main-content {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
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

  .category-btn,
  .item-btn {
    color: #333;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem;
  }

  .category-btn.selected,
  .item-btn.selected {
    background: #007bff;
    color: white;
    border-color: #0056b3;
  }

  .category-btn:hover,
  .item-btn:hover {
    background: #e9ecef;
    color: #333;
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
    text-align: left;
    padding: 0.75rem 1rem;
    background: white;
    color: #333;
    border: 1px solid #dee2e6;
  }

  .item-btn:hover {
    background: #e9ecef;
  }

  .item-btn.selected {
    background: #e9ecef;
    color: #222;
    border-color: #007bff;
  }

  .risk-panel {
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
  }

  .risk-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    width: 100%;
    max-width: 400px;
    text-align: center;
  }

  .risk-card h3 {
    color: #333;
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
  }

  .risk-details {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .selection-info {
    text-align: left;
    line-height: 1.6;
    margin: 0;
    color: #333;
  }

  .selection-label {
    color: #666;
    font-weight: 600;
  }

  .selection-value {
    color: #333;
  }

  .risk-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
  }

  .score-label {
    font-size: 0.9rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .score-value {
    font-size: 2.5rem;
    font-weight: bold;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    color: #333;
  }

  .high-risk {
    color: white;
    background: #dc3545;
  }

  .medium-risk {
    color: white;
    background: #fd7e14;
  }

  .low-risk {
    color: white;
    background: #28a745;
  }

  .risk-card.loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .risk-card.error {
    border-left: 4px solid #dc3545;
  }

  .risk-card.pending {
    border: 2px dashed #dee2e6;
  }

  .risk-card.empty {
    background: #f8f9fa;
    border: none;
  }

  .search-form {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .search-form input {
    padding: 0.5rem;
    font-size: 1rem;
  }

  .search-form button {
    padding: 0.5rem 1rem;
    font-size: 1rem;
  }

  .cards {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 1rem;
  }
  .card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    padding: 1rem 1.5rem;
    min-width: 180px;
    max-width: 220px;
  }
  .card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    color: #222;
  }
  .card p {
    margin: 0;
    color: #555;
  }

  .category-group {
    margin-bottom: 1.5rem;
  }

  .category-header {
    font-size: 1.1rem;
    color: #333;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #eee;
  }

  .product-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .product-item {
    display: flex;
    flex-direction: column;
    padding: 0.5rem;
    border-radius: 4px;
    background: white;
    border: 1px solid #eee;
  }

  .product-name {
    font-weight: 500;
    color: #333;
  }

  .product-category {
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.25rem;
  }

  .product-item:hover {
    background: #f8f9fa;
    border-color: #dee2e6;
  }

  .product-item.selected {
    background: #e7f5ff;
    border-color: #74c0fc;
  }
</style> 