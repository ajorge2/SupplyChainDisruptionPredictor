import React, { useEffect, useState } from "react";
import { fetchData } from "../services/api";

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const getAlerts = async () => {
      const alertData = await fetchData("/alerts");
      setAlerts(alertData);
    };
    getAlerts();
  }, []);

  return (
    <div style={{ marginTop: "20px" }}>
      <h2>Active Alerts</h2>
      <ul>
        {alerts.map((alert, index) => (
          <li key={index}>{alert.message}</li>
        ))}
      </ul>
    </div>
  );
};

export default Alerts;
