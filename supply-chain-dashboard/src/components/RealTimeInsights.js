// RealTimeInsights.js
import React, { useEffect, useState } from 'react';
import './RealTimeInsights.css';

function RealTimeInsights() {
    const [insights, setInsights] = useState([]);

    useEffect(() => {
        console.log('Attempting to connect to WebSocket...');
        const ws = new WebSocket('ws://localhost:8000/ws/realtime');
        
        ws.onopen = () => {
            console.log('WebSocket Connected Successfully');
        };
        
        ws.onmessage = (event) => {
            console.log('Received data:', event.data);
            const data = JSON.parse(event.data);
            setInsights(prev => [data, ...prev].slice(0, 10)); // Keep last 10 items
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket Connection Closed');
        };

        return () => ws.close();
    }, []);

    const formatInsight = (data) => {
        switch(data.source) {
            case 'weather':
                return `Weather: ${data.main.temp}°C in ${data.name}`;
            case 'reddit':
                return `Reddit: New post in r/${data.subreddit} - "${data.title}"`;
            case 'news':
                return `News: ${data.title}`;
            default:
                return JSON.stringify(data);
        }
    };

    return (
        <div className="real-time-insights">
            <h3>Real-Time Insights</h3>
            <div className="insights-container">
                {insights.map((insight, index) => (
                    <div key={index} className="insight-item">
                        {formatInsight(insight)}
                        <span className="timestamp">
                            {new Date(insight.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default RealTimeInsights;