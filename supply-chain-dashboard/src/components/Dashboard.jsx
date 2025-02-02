import React from "react";
import RealTimeChart from "./RealTimeChart";
import Alerts from "./Alerts";
import Map from "./Map";
import RealTimeInsights from "./RealTimeInsights";

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      {/* Header Section */}
      <header className="dashboard-header">
        <h1>Supply-Chain Disruption Predictor</h1>
        <p className="header-subtitle">Insights Now.</p>
      </header>

      {/* Main Dashboard Section */}
      <section className="dashboard-main">
        <div className="dashboard-charts">
          <RealTimeChart />
          <Alerts />
          <RealTimeInsights />
        </div>
        <div className="dashboard-map">
          <Map />
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
