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
  let analyzedProduct = "";
  let analyzedLocation = "";
  let result = null;
  let loading = false;
  let error = "";
  let materialRiskScores = {};
  let dataLoaded = false;
  let rawProduct = "";
  let showProjectInfo = true;
  let modalData = null;

  onMount(async () => {
    try {
      // Load products from products.json
      const productsRes = await fetch("/api/products");
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
            rawName: name,
            category: formatName(category)
          });
        });
      });

      // Process semiconductors (direct items)
      Object.keys(productsData.raw_materials.semiconductors).forEach((name) => {
        processedProducts["Semiconductors"].push({
          id: `semi_${name}`,
          name: formatName(name),
          rawName: name,
          category: "Semiconductors"
        });
      });

      // Process chemicals
      Object.entries(productsData.raw_materials.chemicals).forEach(([category, items]) => {
        Object.keys(items).forEach((name) => {
          processedProducts["Chemicals"].push({
            id: `chem_${category}_${name}`,
            name: formatName(name),
            rawName: name,
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
            rawName: name,
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
            rawName: name,
            category: formatName(category)
          });
        });
      });

      products = processedProducts;

      // Load locations from locations.json
      const locationsRes = await fetch("/api/locations");
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
      product = selectedProd.rawName;
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
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          product: product.toLowerCase(),
          location: location.toLowerCase()
        })
      });
      if (!res.ok) throw new Error("API error");
      result = await res.json();
      analyzedProduct = product;
      analyzedLocation = location;

      // Fetch risk scores for each material
      if (result && result.raw_materials && result.material_source_locations) {
        for (const material of result.raw_materials) {
          try {
            if (result.material_source_locations[material] && result.material_source_locations[material].length > 0) {
              const locations = result.material_source_locations[material];
              const riskRes = await fetch(`/api/risk_score?${locations.map(loc => `locations=${encodeURIComponent(loc)}`).join('&')}&material=${encodeURIComponent(material)}`);
              if (riskRes.ok) {
                const riskData = await riskRes.json();
                materialRiskScores[material] = riskData;
              } else {
                console.error(`Failed to fetch risk score for ${material}:`, riskRes.status);
                materialRiskScores[material] = null;
              }
            }
          } catch (err) {
            console.error(`Network error for ${material}:`, err);
            materialRiskScores[material] = null;
          }
        }
      }
    } catch (e) {
      error = e.message;
    }
    loading = false;
  }

  function showSourcesModal(material, scoreData) {
    if (scoreData && scoreData.location_scores) {
      const allSources = [];
      Object.values(scoreData.location_scores).forEach(locScore => {
        if (locScore.sources) {
          allSources.push(...locScore.sources.together);
          allSources.push(...locScore.sources.material_only);
          allSources.push(...locScore.sources.location_only);
        }
      });
      // Use a Set to get unique URLs
      modalData = {
        material,
        sources: [...new Set(allSources)].filter(Boolean) // Filter out null/empty URLs
      };
    }
  }

  function closeModal() {
    modalData = null;
  }
</script>

<div class="dashboard">
  <main>
    <header>
      <h1>Supply Chain Risk Dashboard</h1>
      <p class="instruction-text">
        Enter any consumer product (like "iPhone", "Tesla Model 3", or "Nike shoes") and a location to analyze supply chain disruption risks. 
        Our AI system breaks down the product into its component raw materials and evaluates mentions in news and social media to provide a risk score (0-3) with detailed breakdown of materials and their source locations.
      </p>
      <div class="header-buttons">
        <button class="details-btn" on:click={() => document.getElementById('project-details').scrollIntoView({ behavior: 'smooth' })}>
          📋 See Project Details
        </button>
        <a href="https://github.com/ajorge2/SupplyChainDisruptionPredictor" target="_blank" rel="noopener noreferrer" class="details-btn github-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-github"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
          GitHub Repo
        </a>
      </div>
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
                <strong class="selection-label">Product:</strong> <span class="selection-value">{analyzedProduct}</span><br>
                <strong class="selection-label">Location:</strong> <span class="selection-value">{analyzedLocation}</span>
              </p>
              
              {#if result.raw_materials && result.raw_materials.length > 0}
                <div class="materials-list">
                  <h4>Component Materials:</h4>
                  <ul class="material-list">
                    {#each result.raw_materials as material}
                      <li class="material-item">
                        <div class="material-info">
                          <span class="material-name">{material}</span>
                          {#if result.material_source_locations && result.material_source_locations[material] && result.material_source_locations[material].length > 0}
                          <div class="material-locations">
                            Source Locations: {result.material_source_locations[material].join(', ')}
                          </div>
                          {/if}
                        </div>
                        <div class="material-details">
                          {#if materialRiskScores[material]}
                            <div class="risk-score-container">
                              <span 
                                class="risk-score-value"
                                class:risk-0={materialRiskScores[material].aggregate_risk_score === 0}
                                class:risk-1={materialRiskScores[material].aggregate_risk_score === 1}
                                class:risk-2={materialRiskScores[material].aggregate_risk_score === 2}
                                class:risk-3={materialRiskScores[material].aggregate_risk_score === 3}
                              >
                                {materialRiskScores[material].aggregate_risk_score}
                              </span>
                              <div class="tooltip">
                                <p><strong>Aggregate Risk: {materialRiskScores[material].aggregate_risk_score}</strong></p>
                                <hr>
                                {#each Object.entries(materialRiskScores[material].location_scores) as [loc, score]}
                                  <p><strong>{loc.charAt(0).toUpperCase() + loc.slice(1)}:</strong> Risk {score.risk_score}</p>
                                  <ul>
                                    <li>Together: {score.mentions.together}</li>
                                    <li>Material Only: {score.mentions.material_only}</li>
                                    <li>Location Only: {score.mentions.location_only}</li>
                                  </ul>
                                {/each}
                              </div>
                            </div>
                            {#if materialRiskScores[material].aggregate_risk_score > 0}
                              <button class="view-sources-btn" on:click={() => showSourcesModal(material, materialRiskScores[material])}>
                                Sources
                              </button>
                            {/if}
                          {:else}
                            <span class="risk-score-value">N/A</span>
                          {/if}
                        </div>
                      </li>
                    {/each}
                  </ul>
                </div>
              {:else}
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
              {/if}
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

    <!-- Project Description Section at Bottom -->
    <div id="project-details" class="project-info-section">
      <div class="project-header">
        <h2>🚀 Advanced Supply Chain Disruption Prediction System</h2>
        <button class="back-to-top-btn" on:click={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          ↑ Back to Top
        </button>
      </div>
      
      <div class="project-description">
        <div class="tech-stack">
          <h3>🛠️ Technical Architecture</h3>
          <div class="tech-grid">
            <div class="tech-card">
              <h4>Backend Infrastructure</h4>
              <ul>
                <li><strong>FastAPI</strong> - High-performance REST API with automatic OpenAPI documentation</li>
                <li><strong>PostgreSQL</strong> - Relational database with complex supply chain data modeling</li>
                <li><strong>Apache Kafka</strong> - Real-time event streaming for data ingestion</li>
                <li><strong>Docker & Docker Compose</strong> - Containerized microservices architecture</li>
              </ul>
            </div>
            
            <div class="tech-card">
              <h4>Data Processing & Analytics</h4>
              <ul>
                <li><strong>OpenAI API Integration</strong> - AI-powered product breakdown and material identification</li>
                <li><strong>Real-time Data Processing</strong> - Continuous analysis of incoming data streams</li>
                <li><strong>Risk Assessment Algorithms</strong> - Multi-factor risk scoring and evaluation</li>
                <li><strong>Data Pipeline Management</strong> - Automated data transformation and enrichment</li>
              </ul>
            </div>
            
            <div class="tech-card">
              <h4>Data Ingestion & Processing</h4>
              <ul>
                <li><strong>Multi-source Integration</strong> - News APIs, social media, weather data</li>
                <li><strong>Real-time Streaming</strong> - Kafka consumers for live data processing</li>
                <li><strong>Data Validation</strong> - Schema enforcement and quality checks</li>
                <li><strong>ETL Pipelines</strong> - Automated data transformation and enrichment</li>
              </ul>
            </div>
            
            <div class="tech-card">
              <h4>Frontend & UX</h4>
              <ul>
                <li><strong>Svelte.js</strong> - Modern reactive frontend framework</li>
                <li><strong>Real-time Updates</strong> - Live risk score calculations</li>
                <li><strong>Interactive Visualizations</strong> - Dynamic risk assessment display</li>
                <li><strong>Responsive Design</strong> - Cross-platform compatibility</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div class="system-features">
          <h3>🎯 Core System Capabilities</h3>
          <div class="features-grid">
            <div class="feature-item">
              <span class="feature-icon">🤖</span>
              <div>
                <h4>AI-Powered Product Analysis</h4>
                <p>Uses OpenAI API to intelligently break down any consumer product into its component raw materials and supply chain dependencies</p>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <div>
                <h4>Multi-dimensional Risk Analysis</h4>
                <p>Analyzes supply chain risks across geopolitical, environmental, economic, and social factors using advanced algorithms</p>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">🌍</span>
              <div>
                <h4>Global Supply Chain Mapping</h4>
                <p>Maps complex supply chain networks with material sourcing locations, transportation routes, and dependency analysis</p>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">⚡</span>
              <div>
                <h4>Real-time Risk Monitoring</h4>
                <p>Continuously monitors global events and automatically updates risk scores based on emerging threats and disruptions</p>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">🔍</span>
              <div>
                <h4>Intelligent Material Identification</h4>
                <p>Automatically identifies and categorizes raw materials from product descriptions using comprehensive material databases</p>
              </div>
            </div>
            
            <div class="feature-item">
              <span class="feature-icon">🔧</span>
              <div>
                <h4>Scalable Architecture</h4>
                <p>Microservices-based design supporting high-throughput data processing and concurrent user access</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="complexity-highlights">
          <h3>💡 Technical Complexity Highlights</h3>
          <div class="complexity-grid">
            <div class="complexity-card">
              <h4>AI-Powered Product Analysis</h4>
              <p>Integrates OpenAI API to intelligently decompose any consumer product into its constituent raw materials. Uses natural language processing to understand product descriptions and cross-references with comprehensive material databases to identify supply chain dependencies.</p>
            </div>
            
            <div class="complexity-card">
              <h4>Advanced Data Processing</h4>
              <p>Processes millions of data points from multiple sources including news articles, social media posts, weather reports, and economic indicators. Implements sophisticated text processing techniques for sentiment analysis and event extraction.</p>
            </div>
            
            <div class="complexity-card">
              <h4>Real-time Event Streaming</h4>
              <p>Built on Apache Kafka for handling high-volume, real-time data streams. Implements complex event processing patterns to detect supply chain disruption signals from multiple concurrent data sources.</p>
            </div>
            
            <div class="complexity-card">
              <h4>Complex Supply Chain Modeling</h4>
              <p>Models intricate supply chain networks with multiple tiers, dependencies, and alternative sourcing options. Implements graph algorithms for dependency analysis and bottleneck identification.</p>
            </div>
          </div>
        </div>

        <div class="risk-scoring-section">
          <h3>📊 Risk Scoring Algorithm</h3>
          <div class="risk-scoring-grid">
            <div class="risk-score-card">
              <h4>Risk Score 0 - Low Risk</h4>
              <p>Neither the material nor the location are ever mentioned, or only the location is mentioned once</p>
            </div>
            
            <div class="risk-score-card">
              <h4>Risk Score 1 - Low-Medium Risk</h4>
              <p>The material is mentioned once by itself, or the location is mentioned twice by itself</p>
            </div>
            
            <div class="risk-score-card">
              <h4>Risk Score 2 - Medium Risk</h4>
              <p>Both the material and location are mentioned together in the same data point once, the material is mentioned twice by itself, or the location is mentioned three times by itself</p>
            </div>
            
            <div class="risk-score-card">
              <h4>Risk Score 3 - High Risk</h4>
              <p>Both the material and location are mentioned together in the same data point more than once, the material is mentioned more than twice by itself, or the location is mentioned more than three times by itself</p>
            </div>
          </div>
          <p class="risk-note">
            <strong>Note:</strong> Risk scores are calculated based on the frequency and context of mentions in news articles and social media posts, 
            providing real-time insights into potential supply chain disruptions.
          </p>
        </div>
      </div>
    </div>
  </main>
</div>

{#if modalData}
  <div class="modal-backdrop" on:click={closeModal}>
    <div class="modal-content" on:click|stopPropagation>
      <button class="close-modal-btn" on:click={closeModal}>&times;</button>
      <h3>Sources for {modalData.material}</h3>
      {#if modalData.sources.length > 0}
        <ul class="source-link-list">
          {#each modalData.sources as sourceUrl}
            <li>
              <a href={sourceUrl} target="_blank" rel="noopener noreferrer">{sourceUrl}</a>
            </li>
          {/each}
        </ul>
      {:else}
        <p>No specific sources found for this risk level.</p>
      {/if}
    </div>
  </div>
{/if}

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
    text-align: center;
    margin-bottom: 2rem;
    padding: 2rem 0;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    color: #2c3e50;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .instruction-text {
    margin: 0;
    font-size: 1.1rem;
    color: #5a6c7d;
    line-height: 1.5;
    max-width: 600px;
    text-align: center;
    font-weight: 400;
  }

  .header-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .details-btn {
    background: linear-gradient(135deg, #6e8efb, #a777e3);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .github-btn {
    background: #333;
  }

  .github-btn:hover {
    background: #444;
  }

  .details-btn:hover {
    transform: translateY(-2px);
  }

  .back-to-top-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
  }

  .back-to-top-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
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
    font-weight: 500;
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
    background: #f8f9fa;
    color: #333;
  }

  .high-risk {
    color: white !important;
    background: #dc3545 !important;
  }

  .medium-risk {
    color: white !important;
    background: #fd7e14 !important;
  }

  .low-risk {
    color: white !important;
    background: #28a745 !important;
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
    color: #333;
  }

  .risk-card.pending h3,
  .risk-card.pending p {
    color: #333;
  }

  .risk-card.empty {
    background: #f8f9fa;
    border: none;
    color: #333;
  }

  .risk-card.empty h3,
  .risk-card.empty p {
    color: #333;
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

  .materials-list {
    margin-top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .materials-list h4 {
    margin: 0;
    color: #333;
    font-size: 1.1rem;
  }

  .material-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #ecf0f1;
    gap: 1rem;
  }

  .material-item:last-child {
    border-bottom: none;
  }

  .material-info {
    flex-grow: 1;
    text-align: left;
  }

  .material-locations {
    font-size: 0.85rem;
    color: #666;
    margin-top: 4px;
  }

  .material-details {
    display: flex;
    align-items: center;
  }

  .material-name {
    font-weight: 600;
    color: #34495e;
  }

  .risk-score-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .risk-score-value {
    font-size: 1.1rem;
    font-weight: 700;
    padding: 5px 15px;
    border-radius: 20px;
    min-width: 30px;
    text-align: center;
    color: white;
    transition: transform 0.2s;
  }

  .risk-score-container:hover .risk-score-value {
    transform: scale(1.1);
  }

  .risk-0 { background-color: #2ecc71; }
  .risk-1 { background-color: #f1c40f; color: #333; }
  .risk-2 { background-color: #e67e22; }
  .risk-3 { background-color: #e74c3c; }

  .tooltip {
    visibility: hidden;
    width: 240px;
    background-color: #333;
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 10px;
    position: absolute;
    z-index: 10;
    bottom: 125%;
    left: 50%;
    margin-left: -120px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 0.9rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }

  .tooltip::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #333 transparent transparent transparent;
  }

  .risk-score-container:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }

  .tooltip p {
    margin: 0 0 5px 0;
  }
  .tooltip hr {
    border: none;
    border-top: 1px solid #555;
    margin: 5px 0;
  }
  .tooltip ul {
    margin: 5px 0 0 0;
    padding-left: 20px;
  }
  .tooltip li {
    margin-bottom: 3px;
  }

  .view-sources-btn {
    background-color: #ecf0f1;
    color: #34495e;
    border: 1px solid #bdc3c7;
    padding: 6px 12px;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .view-sources-btn:hover {
    background-color: #e0e6e8;
    border-color: #95a5a6;
    transform: translateY(-1px);
  }

  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal-content {
    background-color: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    position: relative;
  }

  .close-modal-btn {
    position: absolute;
    top: 10px;
    right: 15px;
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: #888;
  }

  .modal-content h3 {
    margin-top: 0;
    color: #2c3e50;
  }

  .source-link-list {
    list-style: none;
    padding: 0;
    margin-top: 1rem;
  }

  .source-link-list li {
    margin-bottom: 0.5rem;
  }

  .source-link-list a {
    color: #3498db;
    text-decoration: none;
    word-break: break-all;
    background-color: #f8f9fa;
    padding: 8px 12px;
    border-radius: 6px;
    display: block;
    transition: background-color 0.2s;
  }

  .source-link-list a:hover {
    background-color: #e9ecef;
    text-decoration: underline;
  }

  /* Project Description Section Styles */
  .project-info-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    margin: 2rem 0;
    padding: 2rem;
    color: white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }

  .project-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .project-header h2 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .toggle-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
  }

  .toggle-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
  }

  .project-description {
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
  }

  .tech-stack h3,
  .system-features h3,
  .complexity-highlights h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }

  .tech-card {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .tech-card h4 {
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
    font-weight: 600;
    color: #fff;
  }

  .tech-card ul {
    margin: 0;
    padding-left: 1.2rem;
    list-style: none;
  }

  .tech-card li {
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    line-height: 1.4;
    position: relative;
  }

  .tech-card li:before {
    content: "▸";
    position: absolute;
    left: -1rem;
    color: #ffd700;
    font-weight: bold;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .feature-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .feature-icon {
    font-size: 2rem;
    flex-shrink: 0;
    margin-top: 0.2rem;
  }

  .feature-item h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
  }

  .feature-item p {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.5;
    opacity: 0.9;
  }

  .complexity-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .complexity-card {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .complexity-card h4 {
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
    font-weight: 600;
    color: #fff;
  }

  .complexity-card p {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.6;
    opacity: 0.9;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .project-info-section {
      margin: 1rem 0;
      padding: 1.5rem;
    }

    .project-header {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .project-header h2 {
      font-size: 1.5rem;
    }

    .tech-grid,
    .features-grid,
    .complexity-grid {
      grid-template-columns: 1fr;
    }

    .feature-item {
      flex-direction: column;
      text-align: center;
    }

    .feature-icon {
      margin: 0 auto 0.5rem auto;
    }
  }

  /* Risk Scoring Section Styles */
  .risk-scoring-section {
    margin-top: 2.5rem;
  }

  .risk-scoring-section h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .risk-scoring-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .risk-score-card {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease;
  }

  .risk-score-card:hover {
    transform: translateY(-2px);
  }

  .risk-score-card h4 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .risk-score-card h4::before {
    content: "";
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .risk-score-card:nth-child(1) h4::before {
    background: #28a745;
  }

  .risk-score-card:nth-child(2) h4::before {
    background: #ffc107;
  }

  .risk-score-card:nth-child(3) h4::before {
    background: #fd7e14;
  }

  .risk-score-card:nth-child(4) h4::before {
    background: #dc3545;
  }

  .risk-score-card p {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.5;
    opacity: 0.9;
  }

  .risk-note {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    padding: 1rem;
    font-size: 0.9rem;
    line-height: 1.5;
    opacity: 0.9;
    text-align: center;
  }

  .risk-note strong {
    color: #ffd700;
  }

  @media (max-width: 768px) {
    .risk-scoring-grid {
      grid-template-columns: 1fr;
    }
  }
</style> 